from twisted.enterprise import adbapi
from twisted.internet import protocol, reactor
import json
from hashlib import sha256
from hmac import HMAC
from twisted.protocols.basic import LineReceiver
import os
import base64

def encrypt_password(password, salt=None):
	"""Hash password on the fly."""

	if salt is None:
		salt = os.urandom(8) # 64 bits.
	
	assert 8 == len(salt)
	
	assert isinstance(salt, str)
	
	if isinstance(password, unicode):
		password = password.encode('UTF-8')

	assert isinstance(password, str)

	result = password
	for i in xrange(10):
		result = HMAC(result, salt, sha256).digest()
	
	return base64.encodestring(salt + result)
	

def validate_password(input_password,hashed):
	origin = base64.decodestring(hashed)
	return hashed == encrypt_password(input_password, salt=origin[:8])

	

class Matrix(LineReceiver):
	def __init__(self):
		self.loginErrorCount = 0
		self.id = "0"
		self.cmdHandler = {
		"login_in":self.loginIn,
		"login_out" : self.loginOut,
		"accept_new_friend" : self.acceptNewFriend,
		"keep_live" :self.keepLive,
		"data_to_peer" : self.dataToPeer,
		"refuse_new_friend" : self.refuseNewFriend,
		"remove_friend" : self.removeFriend,
		"add_into_group" : self.addIntoGroup
		}
	def connectionMade(self):
#		self.transport.write(json.dumps({"command":"connect_status","connect_status":"connected"}))
		self.sendLine(json.dumps({"command":"connect_status","connect_status":"connected"}));
		print "connection from android client is created"
	def connectionLost(self, reason):
		self.factory.devicesOnLine.pop(self.id,"")
		print "connection to android client is lost"
	def lineReceived(self, data):
		print "line receive data is:",data
		self.handleCommand(data)
		
#		self.transport.write(data)
#	def dataReceived(self,data):
#		print "raw data is:",data
		
	def handleCommand(self,data):
		try:
			decodejson = json.loads(data)
			cmd = decodejson['command']
			print 'handler command ', cmd
			self.cmdHandler[cmd](decodejson)
		except ValueError:
			print 'No JSON object could be decoded'
			return
			
	
	def loginIn(self,data):
		print 'Login in check'
		d = self.factory.dbpool.runQuery("SELECT id,password FROM endpointOrDevice WHERE id = %s",(data["id"],))
		d.addCallback(self.loginCheck,data)
		
	def loginOut(self,data):
		self.factory.dbpool.runOperation("UPDATE endpointOrDevice set status ='OffLine' Where id = %s",(self.id,))
		self.factory.devicesOnLine.pop(self.id,"")

	def acceptNewFriend(self,data):	
		self.factory.dbpool.runOperation("INSERT INTO relationship (relating_endpoint_id, related_endpoint_id) VALUES(%s, %s)",(data['relating_id'],data['related_id']))

	def refuseNewFriend(self,data):
#		self.factory.dbpool.runOperation("INSERT INTO relationship (relating_endpoint_id, related_endpoint_id) VALUES(%s, %s)",(data['relating_id'],data['related_id']))
		pass
		
	def removeFriend(self,data):
		self.factory.dbpool.runOperation("DELETE FROM relationship WHERE relating_endpoint_id=%s,related_endpoint_id=%s",(self.id,data['targetId']))
		
	def dataToPeer(self,data):
		for a in self.factory.devicesOnLine.keys():
			print a
		self.factory.devicesOnLine[data['targetid']].sendLine(json.dumps({"command":"data_to_peer","command_to_device":data['command_to_device']}))
		print 'send line finish'
		
	def keepLive(self,data):
		print 'keep live tick from ',data['id']
		pass
	def addIntoGroup(self,data):
		pass
		
	def loginCheck(self,selectResult,data):
		print "Login check" ,selectResult,data#data['password'],selectResult[0][1]
		if(len(selectResult)>0):
			if(validate_password(data['password'],selectResult[0][1])):
				print 'compare', data['password'], selectResult[0][1]
				self.id = data['id']
				self.factory.devicesOnLine[self.id] = self
				self.factory.dbpool.runOperation("UPDATE endpointOrDevice set status ='OnLine' Where id = %s",(data['id'],))
				self.sendLine(json.dumps({"command":"login_status","login_status":"login sucess"}))
				self.loginErrorCount =0
				print 'login check ok'
			else:
				self.sendLine(json.dumps({"command":"login_status","login_status":"wrong password or id"}))
				self.loginErrorCount+=1
				if(self.loginErrorCount>10):
					self.transport.loseConnection()
				print 'login check failed'
		else:
			self.sendLine(json.dumps({"command":"login_status","login_status":"wrong password or id"}))
			self.loginErrorCount+=1
			if(self.loginErrorCount>10):
				self.transport.loseConnection()
			print 'return 0 when query database '
	
class MatrixFactory(protocol.Factory):
	def __init__(self):
		self.devicesOnLine = {}
		
	def startFactory(self):
		self.dbpool = adbapi.ConnectionPool("MySQLdb", host="localhost",user="matrix",
			passwd="1q2w3e010320409",db="matrixdb",charset="utf8")
		self.dbpool.runInteraction(self.createUsersTable)
	
	def stopFactory(self):
		self.dbpool.close()
		
	protocol = Matrix
	
	def createUsersTable(self,transaction):
		transaction.execute("CREATE TABLE IF NOT EXISTS endpointOrDevice(id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,\
		ip_addr INT NOT NULL,device_type enum('PC','ANDROID','IOS','MAC','BROWER','DEVICE','GATEWAY') NOT NULL ,password CHAR(80),\
		status enum('OnLine','OffLine') NOT NULL, belong_organization VARCHAR(200))")
		
		transaction.execute("CREATE TABLE IF NOT EXISTS companyOrOrganization(id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, \
		user_name VARCHAR(200), password CHAR(32) , email VARCHAR(100), address VARCHAR(200) , phone_number VARCHAR(20))")
		
		transaction.execute("CREATE TABLE IF NOT EXISTS relationship(id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, \
		relating_endpoint_id INT NOT NULL, related_endpoint_id INT NOT NULL ,relation enum('frends','stranger'))")
		
		transaction.execute("CREATE TABLE IF NOT EXISTS groupe(id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, \
		topic VARCHAR(250) , desicrption VARCHAR(1000))")
		
		transaction.execute("CREATE TABLE IF NOT EXISTS endpoint_groups(id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, \
		group_id INT NOT NULL, endpoint_id INT NOT NULL)")	

		transaction.execute("INSERT INTO endpointOrDevice (ip_addr, device_type,password,status) VALUES(%s,%s,%s,%s)",('1020303','ANDROID',encrypt_password('123456789'),'offLine'))
		transaction.execute("INSERT INTO endpointOrDevice (ip_addr, device_type,password,status) VALUES(%s,%s,%s,%s)",('1020303','ANDROID',encrypt_password('123456789'),'offLine'))
		
	
reactor.listenTCP(8000, MatrixFactory())
reactor.run()


	
	


	
