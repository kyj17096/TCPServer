from twisted.internet import reactor
from twisted.enterprise import adbapi
dbpool = adbapi.ConnectionPool("MySQLdb", host="localhost",user="matrix",passwd="1q2w3e010320409",db="matrixdb",charset="utf8")
def _createUsersTable(transaction, users):
	transaction.execute("CREATE TABLE IF NOT EXISTS endpointOrDevice(int id UNSIGNED INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
	ip_addr INT NOT NULL, device_type  enum('PC','ANDROID','IOS','MAC','BROWER','DEVICE','GATEWAY') NOT NULL) \
	password CHAR(32),status enum('PC','ANDROID') NOT NULL, belong_organization VARCHAR(200)")
	
	transaction.execute("CREATE TABLE IF NOT EXISTS companyOrOrganization(int id UNSIGNED INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
	user_name VARCHAR(200), password CHAR(32) , email VARCHAR(100), address VARCHAR(200) , phone_number VARCHAR(20)")
	
	transaction.execute("CREATE TABLE IF NOT EXISTS relationship(int id UNSIGNED INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
	relating_endpoint_id INT NOT NULL, related_endpoint_id INT ,relation enum('frends','stranger')")
	
	transaction.execute("CREATE TABLE IF NOT EXISTS groupe(int id UNSIGNED INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
	topic VARCHAR(250) , desicrption VARCHAR(1000)")
	
	transaction.execute("CREATE TABLE IF NOT EXISTS endpoint_groups(int id UNSIGNED INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
	group_id INT NOT NULL, endpoint_id INT NOT NULL")
	
	for email, name in users:
		transaction.execute("INSERT INTO users (email, name) VALUES(%s, %s)",(email, name))
def createUsersTable(users):
	return dbpool.runInteraction(_createUsersTable, users)
def getName(email):
	return dbpool.runQuery("SELECT name FROM users WHERE email = %s",(email,))
def printResults(results):
	for elt in results:
		print elt[0]
def finish():
	dbpool.close()
	reactor.stop()
users = [("jane@foo.com", "Jane"), ("joel@foo.com", "Joel")]
d = createUsersTable(users)
d.addCallback(lambda x: getName("jane@foo.com"))
d.addCallback(printResults)
reactor.callLater(1, finish)
reactor.run()