This is a sample Python Code based on Nuage AMQP which monitors the status of all netconf sessions of the gateways.
In case a transition from Disconnect to Connect is detected a NetConf force Deploy operation is pushed on VSD in order to ensure that the gateway overlay configuration is consistent with VSD.


Install Instructions:

	 yum install git
	 git clone https://github.com/sesantos/Nuage_NetConf_MonitorDisconnectGateways.git

	 yum install epel-release
	 yum install python-pip
	 yum install gcc
	 yum install openssl

	 pip install futures
	 pip install vspk
	 yum install python-qpid-proton


Setup Instructions:
	Populate the configuration file:

	1-create a user on VSD for JMS client and associate it to Root user-group

	2-Populate the amqp.properties file with JMS username/password, VSD IP Address

	amqp.properties

		[DETAILS]
		UserName=jmsclient%40csp
		Password=jmsclient
		#TopicName=topic/CNAMessages
		TopicName=topic/CNAMessages
		QueueName=queue/CNANetconf

		[CONNECTION]
		Port=5672
		IpAddr1=10.150.34.91

		[VSD]
		VSDUserName=csproot
		VSDPassword=csproot
		VSDOrg=csp
		VSDUrl=https://10.150.34.91

Running Instructions:
 
	#python MonitorDisconnect.py

Log OutPut Example:

	2020-01-15 11:53:30,250 INFO For Gateway NOS-SDN-DC1-POD1-Leaf1 This is a transation from: CONNECTED to DISCONNECTED

	2020-01-15 11:55:12,199 INFO For Gateway NOS-SDN-DC1-POD1-Leaf1 This is a transation from: DISCONNECTED to CONNECTED
	2020-01-15 11:55:12,199 INFO Doing a Force Deploy on the Gateway: NOS-SDN-DC1-POD1-Leaf1
	2020-01-15 11:55:12,200 INFO Geting The Session
	2020-01-15 11:55:12,418 INFO Got the Gateway: NOS-SDN-DC1-POD1-Leaf1
	2020-01-15 11:55:12,419 INFO Got the Gateway: NOS-SDN-DC1-POD1-Leaf1
	2020-01-15 11:55:12,513 INFO Should Sync the RG: NOSSDN-DC1-POD1-Leaf
	2020-01-15 11:55:12,513 INFO Starting NETCONF_FORCE_DEPLOY job for the NOSSDN-DC1-POD1-Leaf Gateway
	2020-01-15 11:56:17,637 INFO SUCCESS :: Force Deploy -  Job succeeded on gateway NOSSDN-DC1-POD1-Leaf!
	
