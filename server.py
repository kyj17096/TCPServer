from twisted.internet import protocol, reactor
class Echo(protocol.Protocol):
	def connectionMade(self):
		print "connection from android client is created"
	def connectionLost(self, reason):
		print "connection to android client is lost"
	def dataReceived(self, data):
		print "receive data is:",data
		self.transport.write(data)
		
class EchoFactory(protocol.Factory):
	def buildProtocol(self, addr):
		return Echo()
reactor.listenTCP(8000, EchoFactory())
reactor.run()