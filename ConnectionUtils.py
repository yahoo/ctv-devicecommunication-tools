import sys, os, threading, uuid, readline, errno
import ssl, socket, select, asyncore, asynchat
import hmac, hashlib, time
from urllib import urlencode

class async_chat_ssl(asynchat.async_chat):
	""" Asynchronous connection with SSL support. """

	def __init__(self, addr):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ssl = ssl.wrap_socket(sock)

		#print "connecting to ", addr
		self.ssl.connect(addr)

		asynchat.async_chat.__init__(self, sock=self.ssl)

		self.send = self._ssl_send
		self.recv = self._ssl_recv

	def _ssl_send(self, data):
		""" Replacement for self.send() during SSL connections. """
		try:
			result = self.write(data)
			return result
		except ssl.SSLError, why:
			if why[0] in (asyncore.EWOULDBLOCK, errno.ESRCH):
				return 0
			else:
				raise ssl.SSLError, why
			return 0

	def _ssl_recv(self, buffer_size):
		""" Replacement for self.recv() during SSL connections. """
		try:
			data = self.read(buffer_size)
			if not data:
				self.handle_close()
				return ''
			return data
		except ssl.SSLError, why:
			if why[0] in (asyncore.ECONNRESET, asyncore.ENOTCONN,
						  asyncore.ESHUTDOWN):
				self.handle_close()
				return ''
			elif why[0] == errno.ENOENT:
				# Required in order to keep it non-blocking
				return ''
			else:
				raise

class ConnectionHandler(async_chat_ssl):
	def __init__(self, addr, queue=None, onMessageRecieved=None, onMessageRecievedContext=None):
		async_chat_ssl.__init__(self, addr)
		self.ibuffer = []
		self.set_terminator("|END")
		self.onMessageReceived = onMessageRecieved
		self.onMessageRecievedContext = onMessageRecievedContext
		self.queue = queue
		#print("Handler initialized")

	def returnMessage(self, msg):
		if self.queue != None:
			self.queue.put(msg)
		else:
			method = self.onMessageReceived
			if self.onMessageRecievedContext != None:
				context = self.onMessageRecievedContext
				context.method(msg)
			else:
				method(msg)

	def collect_incoming_data(self, data):
		self.ibuffer.append(data)

	def found_terminator(self):
		response = "".join(self.ibuffer)
		self.ibuffer = []
		self.returnMessage(response)

def createSession(connection, app_id, consumer_key, secret, app_name):
	keyopts = {
		'app_id': app_id,
		'consumer_key': consumer_key,
		'secret': hmac.new(secret, consumer_key, hashlib.sha1).hexdigest()
	}
	
	createCommand = "SESSION|CREATE|%s|%s|END" %(urlencode(keyopts), app_name)
	print "SENDING:", createCommand
	connection.handler.push(createCommand)
	
def resetSession(connection, instanceID):
	resetCommand = "SESSION|RESET|%s|END" % instanceID
	print "SENDING:", resetCommand
	connection.handler.push(resetCommand)

def authSession(connection, code):
	cert = str(ssl.DER_cert_to_PEM_cert(connection.handler.socket.getpeercert(True))).rstrip()
	
	#Some machines already have the \n.. I can't even...wha??
	if '\n-----END CERTIFICATE-----' not in cert:
		cert = cert.replace('-----END CERTIFICATE-----', '\n-----END CERTIFICATE-----')

	signature = hmac.new(code, cert, hashlib.sha1).hexdigest()
	authCommand = "SESSION|AUTH|%s|END" % signature

	print "SENDING:", authCommand
	connection.handler.push(authCommand)

class Connection():
	def __init__(self, host, port, queue=None, onMessageRecieved=None, onMessageRecievedContext=None):
		self.buffer = []
		self.handler = ConnectionHandler((host, port), queue, onMessageRecieved, onMessageRecievedContext)

	def startLoop(self):
		asyncore.loop(1)
		print "Connection Closed"

	def close(self):
		self.handler.close_when_done()
