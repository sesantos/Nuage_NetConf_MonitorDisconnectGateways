#About: This is an sample Amqp client fro activemq. With the given details it will connect to active mq and receive message on the topic.
#File expects amqp.properties file to be present in same location where python script is present.
#from __future__ import print_function
###########################################################################################################
##### python amqpClient.py test.log S1 amqp.properties -d -c
########################################################################################################### 

import optparse
import os
import datetime
import time
import logging
import sys
import ConfigParser
import random
import uuid
import json
import threading
from concurrent.futures import ThreadPoolExecutor



from proton.handlers import MessagingHandler,EndpointStateHandler
from proton.reactor import Container, DurableSubscription, ApplicationEvent, EventInjector
from optparse import OptionParser
from gateway_operations import ForceDeploy

sDetailsSection = "DETAILS"
sConnectionSection = "CONNECTION"
sVSDSection = "VSD"


S_UserName = "UserName"
S_Password = "Password"
S_ClientId = "ClientId"
S_TopicName = "TopicName"
S_QueueName = "QueueName"

S_Port = "Port"
S_IpAddr1 = "IpAddr1"
S_IpAddr2 = "IpAddr2"
S_IpAddr3 = "IpAddr3"

S_VSDUserName = "VSDUserName"
S_VSDPassword = "VSDPassword"
S_VSDOrg = "VSDOrg"
S_VSDUrl = "VSDUrl"

LOG = None
OPTIONS = None
ARGS = None

def main():
    initLogging()
    LOG.info("Starting Amqp Client")
    oAmqpClient = AmqpClient()
    Container(Recv(oAmqpClient), EndPointHandler()).run()


def initLogging():
    global LOG, OPTIONS, ARGS

    usage = "This Script is an ActiveMq client using AMQP connector .\nusage: %prog [OPTION]-c [OPTION]-d"
    parser = OptionParser(usage=usage)

    parser.add_option("-c", "--cluster", action="store_true", dest="cluster", default=False,
                      help="[OPTIONAL]Connect to cluster setup.")
    parser.add_option("-d", "--durable", action="store_true", dest="durable", default=False,
                      help="[OPTIONAL]Connect to durable setup.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="[OPTIONAL]run command in verbose mode.")
    parser.add_option("-p", "--propertyFile", action="store", dest="property", default="amqp.properties",
                      help="[OPTIONAL] Property File to use. Defaults to amqp.properties file",type="string")
    parser.add_option("-f", "--logFile", action="store", dest="logfile", default="amqp-client.log",
                      help="[OPTIONAL] Log file to redirect logs. Defaults to amqp-client.log",type="string")
    parser.add_option("-i", "--clientId", action="store", dest="clientid", default="My Client",
                      help="[OPTIONAL] Client Id through which connection has to be made. Defaults to My Client",type="string")

    (OPTIONS, ARGS) = parser.parse_args()

    # Use the specified log file for logging
    logfile = None
    if OPTIONS.logfile is not None:
        logfile = OPTIONS.logfile

    # Initialize logging parameters
    if OPTIONS.verbose is True:
        basicLevel = logging.DEBUG
    else:
        basicLevel = logging.WARN

    #Setup Our logger
    LOG = logging.getLogger('amqp-client')
    hdlr = logging.FileHandler(logfile)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    LOG.addHandler(hdlr)
    LOG.propagate = False
    LOG.setLevel(logging.DEBUG)

    # Setup basic logging , The qpid library logging
    logging.basicConfig(filename=logfile, level=basicLevel,
                        format='%(asctime)s %(levelname)s %(message)s')


class AmqpClient():

    def __init__(self):
        #Initialize Defaults
        self.bClusterMode = False
        self.bDurableSubscription = True
        self.sUserName = "username%40csp"
        self.sPassword = "password"
        self.sClientId = "Amqp Client"
        self.sTopicName = "topic://topic/CNATopic"
        self.sQueueName = "queue://queue/CNAQueue"
        self.isTopic = False
        self.vsdUserName = "username"
        self.vsdPassword = "password"
        self.vsdOrg = "Org"
        self.vsdUrl = "https://10.20.30.10"
        

        self.sPort = "5672"
        self.lUrls = []

        self.initializeArgumentsForAmqp()
        self.parseFileForAmqpDetails()


    def initializeArgumentsForAmqp(self):
        LOG.info("Initializing arguments")

        # Set the Cluster Mode
        if OPTIONS.cluster is True:
            self.bClusterMode = True

        # Set the Durable subscribtion Mode
        if OPTIONS.durable is True:
            self.bDurableSubscription = True

        if OPTIONS.property is not None:
            self.propertyFile = OPTIONS.property

        if OPTIONS.clientid is not None:
            self.sClientId = OPTIONS.clientid

        LOG.info(
            "Starting ActiveMq Amqp client with Cluster Mode : %s, And durable subscribtion mode set to : %s", self.bClusterMode, self.bDurableSubscription)

    def parseFileForAmqpDetails(self):
        LOG.info("Scanning property file and getting Amqp Details")
        config = ConfigParser.RawConfigParser()
        config.read(self.propertyFile)

        if config.has_section(sDetailsSection):
            #If Username password provided use them else use default
            if config.has_option(sDetailsSection, S_UserName):
                self.sUserName = config.get(sDetailsSection, S_UserName)

            if config.has_option(sDetailsSection, S_Password):
                self.sPassword = config.get(sDetailsSection, S_Password)

            if config.has_option(sDetailsSection, S_TopicName) :
                self.sTopicName = "topic://"+config.get(sDetailsSection, S_TopicName)
                self.isTopic = True
            else:
                if config.has_option(sDetailsSection, S_QueueName) :
                    self.sQueueName = "queue://" + config.get(sDetailsSection, S_QueueName)

        if config.has_section(sConnectionSection):
            if config.has_option(sConnectionSection, S_Port):
                self.sPort = config.get(sConnectionSection, S_Port)

            if self.bClusterMode:
                LOG.info("Cluster mode adding all 3 Ip's")
                self.lUrls.append(self.getUrl(config.get(sConnectionSection, S_IpAddr1)))
                self.lUrls.append(self.getUrl(config.get(sConnectionSection, S_IpAddr2)))
                self.lUrls.append(self.getUrl(config.get(sConnectionSection, S_IpAddr3)))
            else:
                LOG.info("Standalone mode adding only one Ip")
                self.lUrls.append(self.getUrl(config.get(sConnectionSection, S_IpAddr1)))
        else:
            LOG.error("No Connection Details Section")

        if config.has_section(sVSDSection):
            if config.has_option(sVSDSection, S_VSDUserName) and config.has_option(sVSDSection, S_VSDPassword) and config.has_option(sVSDSection, S_VSDOrg) and config.has_option(sVSDSection, S_VSDUrl):
                self.vsdUserName = config.get(sVSDSection, S_VSDUserName)
                self.vsdPassword = config.get(sVSDSection, S_VSDPassword)
                self.vsdOrg = config.get(sVSDSection, S_VSDOrg)
                self.vsdUrl = config.get(sVSDSection, S_VSDUrl)
            else:
                LOG.error("Missing Nuage VSD Parameters")
        else:
            LOG.error("No Nuage VSD Details Section")


        LOG.info("Connect to ActiveMQ using User Name: %s , Password :%s , Client Id: %s , Connecting to Topic: %s , with Subscription mode set to : %s .",self.sUserName, self.sPassword, self.sClientId, self.sTopicName, self.bDurableSubscription)
        LOG.info("Url for connection is: %s",self.lUrls)

    def getUrl(self, aInIpAddr):
        return self.sUserName+":"+self.sPassword+"@"+aInIpAddr+":"+self.sPort;
        
class Recv(MessagingHandler):
    def __init__(self, aInOAmqpClient):
        super(Recv, self).__init__()
        self.oAmqpClient = aInOAmqpClient
        self.received = 0
        self.ForceDeploy = ForceDeploy(self.oAmqpClient.vsdUserName,self.oAmqpClient.vsdPassword,self.oAmqpClient.vsdOrg,self.oAmqpClient.vsdUrl, LOG, EventInjector())

    def on_start(self, event):
        #Set the client id So that It is easy to Identify.
        event.container.container_id=self.oAmqpClient.sClientId
        conn = event.container.connect(urls=self.oAmqpClient.lUrls,heartbeat=1000000)

        if self.oAmqpClient.bDurableSubscription:
            durable = DurableSubscription()
            if self.oAmqpClient.isTopic:
                event.container.create_receiver(conn, self.oAmqpClient.sTopicName, options=durable)
            else:
                event.container.create_receiver(conn, self.oAmqpClient.sQueueName, options=durable)
        else:
            event.container.create_receiver(conn, self.oAmqpClient.sTopicName)

    def on_message(self, event):
        LOG.info("Message Header: %s", event.message.properties)
        LOG.info("Message Received: %s", event.message.body)
        
        message_event = json.loads(event.message.body)
        
        if message_event['entityType'] == 'netconfsession' and message_event['type'] == 'UPDATE':
            message_entities=message_event['entities'][0]
            message_diffmap_value=message_event['diffMap'].values()[0]

            if message_diffmap_value['modified'] is not None:
                message_status=message_diffmap_value['modified']
                message_status_values=message_status['status']
                LOG.info('For Gateway {} This is a transation from: {} to {}'.format(message_entities['associatedGatewayName'], message_status_values['oldValue'],message_status_values['newValue']))
                if message_status_values['oldValue'] == "DISCONNECTED" and message_status_values['newValue'] == "CONNECTED":
                    LOG.info ("Doing a Force Deploy on the Gateway: {}".format(message_entities['associatedGatewayName']))
                    self.thread = threading.Thread(target=self.ForceDeploy.forceDeploy, args=(message_entities['associatedGatewayName'], message_entities['associatedGatewayID'], ApplicationEvent("force_deploy_done", delivery=event.delivery)))
                    self.thread.daemon=False
                    self.thread.start()
                



    def on_disconnected(self, event):
        LOG.info("Amqp connection to %s disconnected.", event.connection.hostname)

class EndPointHandler(EndpointStateHandler):
    def __init__(self):
        super(EndPointHandler, self).__init__()

    def on_connection_opened(self, event):
        LOG.info("Amqp connection to %s connected.", event.connection.hostname)
        super(EndPointHandler, self).on_connection_opened(event)




if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        LOG.exception("Received Keyboard Interrupt exiting")
    except Exception as e:
        LOG.exception("Exception Occured during execution %s", e)
        sys.exit(1)
    finally:
        LOG.info("Exiting Finally")