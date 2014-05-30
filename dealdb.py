from twisted.internet import reactor
from twisted.enterprise import adbapi
dbpool = adbapi.ConnectionPool("MySQLdb", host="localhost",user="matrix",passwd="1q2w3e010320409",db="matrixdb",charset="utf8")
def _createUsersTable(transaction, users):
	transaction.execute("CREATE TABLE IF NOT EXISTS users (email TEXT, name TEXT)")
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