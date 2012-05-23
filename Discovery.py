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