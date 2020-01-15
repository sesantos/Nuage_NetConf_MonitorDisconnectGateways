#About: This is an sample Amqp client fro activemq. With the given details it will connect to active mq and receive message on the topic.
#Usage: python amqpClienty.py -c[for cluster mode] -d[for durable subscription] -v[verbose mode] -i <client Id> -p <property file to use>[properties file to use] -f <log file for output>[log file location]
#File expects amqp.properties file to be present in same location where python script is present.
#from __future__ import print_function
###########################################################################################################
##### python amqpClient.py test.log S1 amqp.properties -d -c
########################################################################################################### 
try:
    import Queue
except:
    import queue as Queue

import logging
import threading
import time
import sys

from vspk import v5_0 as vspk



class ForceDeploy():

    def __init__(self, n_username, n_password, n_org, api_url, log, injector):
        #Initialize Defaults
        self.n_username = n_username
        self.n_password = n_password
        self.n_org = n_org
        self.api_url = api_url
        self.injector = injector
        self.tasks = Queue.Queue()
        self.running = True
        self.LOG = log


    def forceDeploy(self, gatewayName, gatewayID, event=None):
        n_gatewayName = gatewayName
        my_event=event
      

        self.LOG.info("Geting The Session")
        
        nuage_session = vspk.NUVSDSession(
        username=self.n_username,
        password=self.n_password,
        enterprise=self.n_org,
        api_url=self.api_url)

        me = nuage_session.start().user

        
        gateway = me.gateways.get_first(filter='name == "{}"'.format(n_gatewayName))
        
        self.LOG.info('Got the Gateway: {}'.format(gateway.name))

        if gateway:
            self.LOG.info('Got the Gateway: {}'.format(gateway.name))


        RG=me.redundancy_groups.get()
        
        ##find if GW is part of RG
        for RG in RG:
            if (RG.gateway_peer1_name==n_gatewayName) or (RG.gateway_peer2_name==n_gatewayName):
                self.LOG.info('Should Sync the RG: {}'.format(RG.name))
                gateway = RG


        job = vspk.NUJob(command='NETCONF_FORCE_DEPLOY')

        self.LOG.info('Starting {} job for the {} Gateway'.format(
        'NETCONF_FORCE_DEPLOY', gateway.name))

        gateway.create_child(job)
        self.is_job_ready(job, 600, gateway.name, my_event)
            
    def is_job_ready(self, job, timeout, gatewayName, event):
        """
        Waits for job to succeed and returns job.result
        """ 
        timeout_start = time.time()
        while time.time() < timeout_start + timeout:
            job.fetch()
            if job.status == 'SUCCESS':
                self.LOG.info('SUCCESS :: Force Deploy -  Job succeeded on gateway {}!'.format(gatewayName))
                self.injector.trigger(event)
                return
            if job.status == 'FAILED':
                self.injector.trigger(event)
                self.LOG.info('FAILED :: Force Deploy -  Failed on  gateway {} with error: {}!'.format(gatewayName,job.result))
                return
            time.sleep(1)

        self.LOG.info('ERROR :: Job {} failed to return its status in {}sec interval'.format(
            job.command, timeout))