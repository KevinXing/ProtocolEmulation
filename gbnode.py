import argparse
import threading
import time
import socket
import sys


#---------------------- global variables -------------------------
# input arguments
selfPort = ''
peerPort = ''
winSize = ''
N = ''
P = ''

# message
#-----------------------------
#     seq       | type | data 
#-----------------------------
# seq  : 32 bit
# type :  1 bit
# data :  1 bit

# type
ACK = 0
DATA = 1
IP = '127.0.0.1'

# buffer
msgBuf = []
bufSize = ''
base = 0
nextSeq = 0
tail = 0
expSeq = 0

# timer
timerThread = None
timerStop = threading.Event()
timerCnt = 0
timerTotal = 10
timerGap = 0.5

#---------------------- parse argument -------------------------
def checkPort(port):
	if (port < 1024 or port > 65536):
		print 'port ' + str(port) + 'invalid'
		exit(2) 

#python gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> j -p <value-of-p>]
def argParse():
	global selfPort, peerPort, winSize, bufSize, N, P, msgBuf
	parser = argparse.ArgumentParser()
	parser.add_argument('selfPort')
	parser.add_argument('peerPort')
	parser.add_argument('winSize')
	parser.add_argument('-d', dest = 'N')
	parser.add_argument('-p', dest = 'P')
	argResult = parser.parse_args()
	try:
		selfPort = int(argResult.selfPort)
		checkPort(selfPort)
		peerPort = int(argResult.peerPort)
		checkPort(selfPort)
		winSize = int(argResult.winSize)
		if (argResult.N is not None):
			N = int(argResult.N)
		if (argResult.P is not None):
			P = float(argResult.P)
		bufSize = 2 * winSize
		msgBuf = [None] * bufSize
	except ValueError:
		print 'input invalid'
		exit(2)



#---------------------- shared functions --------------------
def startTimer():
	global timerStop, timerCnt, base, msgBuf, nextSeq
	timerCnt = 0
	timerStop.clear()
	print 'start timer'

def timer(s):
	global timerStop, timerCnt, timerTotal, timerGap
	while (True):
		if (timerCnt == timerTotal):
			print '[{0}] packet{1} timeout'.format(time.time(), base)
			startTimer()
			for i in range(base, nextSeq):
				idx = (base + i) % bufSize
				s.sendto(msgBuf[idx], (IP, peerPort))
				print '[{0}] packet{1} {2} sent'.format(time.time(), i, msgBuf[idx])
			sys.stdout.flush()
		else:
			if (not timerStop.is_set()):
				timerCnt = timerCnt + 1
				print timerCnt
				sys.stdout.flush()
				time.sleep(0.5)

def makePkt(nextSeq, dataType, data):
	return str(nextSeq) + str(dataType) + str(data)


#---------------------- send packet -------------------------
def msgSend(s, data):
	global nextSeq, msgBuf, base, bufSize
	idx = nextSeq % bufSize
	while (idx == (base + winSize) % bufSize):
		pass
	msgBuf[idx] = makePkt(nextSeq, DATA, data)
	sys.stdout.flush()
	s.sendto(msgBuf[idx], (IP, peerPort))
	print '[{0}] packet{1} {2} sent'.format(time.time(), nextSeq, data)
	sys.stdout.flush()
	if (base == nextSeq):
		startTimer()	
	nextSeq = nextSeq + 1


def sendHelper():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	while True:
		print 'node> ',
		sys.stdout.flush()
		msg = raw_input()
		msg = msg.split(' ')[1]

		for i in range(len(msg)):
			msgSend(s, msg[i])


#---------------------- receive packet -------------------------
def msgRev():
	global base, nextSeq, timerStop, expSeq, selfPort, IP
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(('127.0.0.1', int(selfPort)))
	print 'here'
	while (True):
		data, (addr, port) = s.recvfrom(1024)
		msgType = data[-2]
		msgSeq = data[0:-2]
		msgData = data[-1]
		if msgType == ACK:
			if msgSeq == base:
				base = base + 1
				print '[{0}] ACK{1} received, window moves to {2}'.format(time.time(), msgSeq, base % bufSize)
				if (base == nextSeq):
					timerStop.set()
				else:
					startTimer()
			else:
				print '[{0}] packet{1} timeout'.format(time.time(), msgSeq)

		elif msgType == DATA:
			pkt = makePkt(expSeq, ACK, 0)
			s.sendto(pkt, (IP, peerPort))
			print '[{0}] packet{1} {2} received'.format(time.time(), msgSeq, msgData)
			print '[{0}] ACK{1} sent, expecting packet{2}'.format(time.time(), expSeq, expSeq + 1)
			if msgSeq == expSeq:
				expSeq = expSeq + 1

		sys.stdout.flush()
				
		

def main():
	global timerStop, timerThread
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	timerStop.set()
	timerThread = threading.Thread(target = timer, args = (s,))
	timerThread.start()
	listenThread = threading.Thread(target = msgRev)
	listenThread.start()
	sendHelper()

argParse()
main()




