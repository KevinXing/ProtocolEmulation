import argparse
import sys
import json
import time
import socket

localPort = ''
last = False
table = {}
neigborList = []
nextHop = {}
first = True

def checkPort(port):
	if (port < 1024 or port > 65536):
		print 'port ' + str(port) + 'invalid'
		exit(2) 

#dvnode <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]
def argParse():
	global localPort, last, table, neigborList
	parser = argparse.ArgumentParser()
	parser.add_argument('localPort')
	parser.add_argument('neigbors', nargs='*')
	argResult = parser.parse_args()
	try:
		localPort = int(argResult.localPort)
		checkPort(localPort)
		table[localPort] = {}
		
		neigbors = argResult.neigbors
		if (len(neigbors) % 2 == 1):
			last = True
		for i in range(0, len(neigbors), 2):
			if (i + 1 < len(neigbors)):
				table[localPort][int(neigbors[i])] = float(neigbors[i + 1])
				neigborList.append(int(neigbors[i]))
		printTable()
	except ValueError:
		print 'input invalid'
		exit(2)

def msgRev():
	global first
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(('127.0.0.1', localPort))
	while (True):
		try:
			data, (addr, port) = s.recvfrom(1024)
			tmp = json.loads(data)
			for neigbor in tmp:
				print '[{0}] Message received at Node {1} from Node {2}'.format(time.time(), localPort, neigbor)
				update = updateTable(neigbor, tmp[neigbor])
				if update or first:
					informNeigbors()
					first = False
				printTable()
		except KeyboardInterrupt:
			sys.exit()

def informNeigbors():
	global localPort, table, neigborList
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	data = json.dumps(table)
	for x in neigborList:
		s.sendto(data, ('127.0.0.1', x))
		print '[{0}] Message sent from Node {1} to Node {2}'.format(time.time(), localPort, x)
	sys.stdout.flush()
	s.close()

def updateTable(x, msg):
	global table, localPort, nextHop
	x = int(x)
	update = False 
	sys.stdout.flush()

	for y in msg:
		yi = int(y)
		if yi == localPort:
			continue
		if yi not in table[localPort]:
			print y
			update = True
			table[localPort][yi] = table[localPort][x] + msg[y]
			if x in nextHop:
				nextHop[yi] = nextHop[x]
			else:
				nextHop[yi] = x
		else:
			if (table[localPort][yi] > table[localPort][x] + msg[y]):
				update = True
				table[localPort][yi] = table[localPort][x] + msg[y]
				if x in nextHop:
					nextHop[yi] = nextHop[x]
				else:
					nextHop[yi] = x
	return update

def printTable():
	global table, localPort, nextHop
	print '[{0}] Node {1} Routing Table'.format(time.time(), localPort)
	for x in table[localPort]:
		tmp = ''
		if x in nextHop:
			tmp = ' ; Next hop -> Node ' + str(nextHop[x])
		print '- (' + str(table[localPort][x]) + ') -> Node ' + str(x) +  tmp
		sys.stdout.flush()

def main():
	global last, first
	if last:
		informNeigbors()
		first = False
	msgRev()

argParse()
main()




