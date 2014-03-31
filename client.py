#!/usr/bin/python

###########################################################################
# Copyright (c) 2014, Yahoo.
# All rights reserved.
#
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
# * Redistributions of source code must retain the above
# copyright notice, this list of conditions and the
# following disclaimer.
#
# * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the
# following disclaimer in the documentation and/or other
# materials provided with the distribution.
#
# * Neither the name of Yahoo. nor the names of its
# contributors may be used to endorse or promote products
# derived from this software without specific prior
# written permission of Yahoo.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###########################################################################

import sys, ConfigParser
try:
	import argparse
except:
	print("'argparse' python library not found.\n If using Ubuntu, run 'sudo apt-get install python-argparse'")
	sys.exit()
from Discovery import *
from ConnectionUtils import *

DEFAULT_APP_ID = "0xeTgF3c"
DEFAULT_CONSUMER_KEY = "dj0yJmk9T1Y0MmVIWWEzWVc3JmQ9WVdrOU1IaGxWR2RHTTJNbWNHbzlNVEUzTkRFM09ERTJNZy0tJnM9Y29uc3VtZXJzZWNyZXQmeD0yNA--"
DEFAULT_SECRET = "1b8f0feb4d8d468676293caa769e19958bf36843"
DEFAULT_APP_NAME = "Test Client (client.py)"

IS_RUNNING=False

class ReceiverThread(threading.Thread):
		def __init__(self, connection):
			threading.Thread.__init__(self)
			self.connection=connection
			self.isClosing=False

		def run(self):
			while not self.isClosing:
				cmnd = getUserInput("SEND: ")
				if cmnd == "" or cmnd == -1 : continue
				if cmnd == "q": break

				self.connection.handler.push(cmnd)
			self.connection.handler.close_when_done()

userInputState = {"prompt":"", "isWaiting":False}
def printMessage(msg):
	if(userInputState["isWaiting"]):
		print "\n",msg
		sys.stdout.write(userInputState["prompt"])
	else:
		print msg

def getUserInput(prompt):
	userInputState["isWaiting"] = True
	userInputState["prompt"] = prompt
	data =  raw_input(prompt)
	userInputState["isWaiting"] = False
	return data

def api(args):
	def onMessageRecieved(msg):
		print "RCVD:", msg

	client = Connection(args.host, args.port, onMessageRecieved=onMessageRecieved)

	if args.instanceId:
		resetSession(client, args.instanceId)
	elif args.manual_auth == False:
		createSession(client, args.app_id, args.consumer_key, args.secret, args.app_name)
	
		authSession(client, raw_input("Please enter code:"))

	inputReader = ReceiverThread(client)
	inputReader.start()

	client.startLoop();
	inputReader.isClosing=True
	
def setupReadlineHistory(historyFile):
	try:
		readline.read_history_file(historyFile)
		readline.parse_and_bind("set set editing-mode vi")
		readline.parse_and_bind("set horizontal-scroll-mode On")
	except IOError, e:
		print(e)
		pass
	import atexit
	atexit.register(readline.write_history_file, historyFile)

def parse_args():
	parser = argparse.ArgumentParser(description='Connect to a Device Communication-enabled TV and send messages')
	parser.add_argument('host', nargs='?', help='hostname or IP to connect to, omit for automatic search')
	parser.add_argument('port', type=int, nargs='?', default=8099, help='port of device, defaults to 8099')
	parser.add_argument('-m', '--manual-auth', action='store_true', help='do not prompt for code, just connect')
	parser.add_argument('-i', '--instanceId',  help='use an instanceID to connect, will override --manual-auth')
	parser.add_argument('-y', '--history',  default=os.path.join(os.environ["HOME"], ".client.py.hist"), help='use non-default history file')
	parser.add_argument('-c', '--config',  default=os.path.join(os.environ["HOME"], ".client.py.config"), help='configuration file that stores authorization keys, leave blank to use default non-production keys. See config.sample for configuration file example. Default location: %s' % os.path.join(os.environ["HOME"], ".client.py.config"))
	return parser.parse_args()
	
def load_config(args):
	config = ConfigParser.RawConfigParser({"app_id": DEFAULT_APP_ID, "consumer_key":DEFAULT_CONSUMER_KEY, "secret": DEFAULT_SECRET, "app_name":DEFAULT_APP_NAME})
	configsRead = config.read(args.config)
	
	if configsRead is None: 
		print("WARNING: Using default auth keys. Note these can only be used in a simulator environment. See --help for more information." % args.config)
	elif args.config not in configsRead:
		print("Unable to load config file %s, using default auth keys. Note these can only be used in a simulator environment." % args.config)
	
	args.app_id = config.get("DEFAULT", "app_id")
	args.consumer_key = config.get("DEFAULT", "consumer_key")
	args.secret = config.get("DEFAULT", "secret")
	args.app_name = config.get("DEFAULT", "app_name")
	
	
		
def main():
		args = parse_args()
		load_config(args)
		
		if not args.host and PYBONJOUR_AVAILABLE:
			print("Starting automatic discovery... For manual usage, see the -h option")
			args.host, args.port = discover()
			if args.host is None or args.port is None:
				print("Unable to automatically resolve host and port. For manual usage, see the -h option")
		elif not args.host and not PYBONJOUR_AVAILABLE:
			print("Automatic search not available, please install pybonjour")
		
		if args.host != None and args.port != None:
			setupReadlineHistory(args.history)
			
			api(args)

if __name__ == "__main__":
		main()
