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

import select, time, socket

PYBONJOUR_AVAILABLE = True
try:
	import pybonjour
except:
	print("pybonjour not installed, no auto discovery available")
	PYBONJOUR_AVAILABLE = False

regtype  = "_yctvwidgets._tcp"
timeout  = 5
resolved_addrs = []

def resolve_callback(sdRef, flags, interfaceIndex, errorCode, fullname, hosttarget, port, txtRecord):
	if errorCode == pybonjour.kDNSServiceErr_NoError:
		global resolved_addrs
		ip = socket.gethostbyname(hosttarget)
		if ip not in [entry.get("host") for entry in resolved_addrs]:
			print("resolved %s:%d" % (ip, port))
			resolved_addrs.append({"sdRef":sdRef, "hostname": hosttarget, "host": ip, "port": port})

def browse_callback(sdRef, flags, interfaceIndex, errorCode, serviceName,
					regtype, replyDomain):
	if errorCode != pybonjour.kDNSServiceErr_NoError:
		return

	if not (flags & pybonjour.kDNSServiceFlagsAdd):
		print 'Service removed'
		return

	print 'DC Service found; resolving'
	global resolved_addrs
	resolve_sdRef = pybonjour.DNSServiceResolve(0,
						    interfaceIndex,
						    serviceName,
						    regtype,
						    replyDomain,
						    resolve_callback)

	try:
		while True:
			ready = select.select([resolve_sdRef], [], [], timeout)
			if resolve_sdRef not in ready[0]:
				break
			pybonjour.DNSServiceProcessResult(resolve_sdRef)
	finally:
		resolve_sdRef.close()

def discover(timeout=10):
	timeout = float(timeout)
	browse_sdRef = pybonjour.DNSServiceBrowse(regtype = regtype, callBack = browse_callback)
	cTime = time.time()
	try:
		try:
			while len(resolved_addrs) == 0 and time.time()-cTime < timeout:
				ready = select.select([browse_sdRef], [], [], timeout/2)
				if browse_sdRef in ready[0]:
					pybonjour.DNSServiceProcessResult(browse_sdRef)
		except KeyboardInterrupt:
			pass
	finally:
		browse_sdRef.close()
	
	if len(resolved_addrs) > 0:
		if len(resolved_addrs) == 1:
			print("Found 1 matching Service, connecting to %s:%d" % (resolved_addrs[0].get("host"), resolved_addrs[0].get("port")))
			return resolved_addrs[0].get("host"), resolved_addrs[0].get("port")
		else:
			print("Found Services:")
			print("#\tHost:Port")
			for i in range(0, len(resolved_addrs)):
				print("%d:\t%s:%d" % (i, resolved_addrs[i].get("host"), resolved_addrs[i].get("port")))
			user_option = input("Please choose service # to connect:")
			return resolved_addrs[user_option].get("host"), resolved_addrs[user_option].get("port")
	else:
		return None, None
	
if __name__ == "__main__":
	print discover()
