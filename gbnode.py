import argparse
import threading
import time
import socket
import sys
import random


#---------------------- global variables -------------------------
# input arguments
selfPort = ''
peerPort = ''
winSize = ''
N = ''
P = ''
curN = 0

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
END = 2
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

# stats
sendPackets = 0
sendDrop = 0
recvPackets = 0
recvDiscard = 0
totalPackets = 0

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
		checkPort(peerPort)
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

def timer(s):
	global timerStop, timerCnt, timerTotal, timerGap, msgBuf, IP, peerPort
	while (True):
		if (timerCnt == timerTotal):
			print '[{0}] packet{1} timeout'.format(time.time(), base)
			startTimer()
			for i in range(base, nextSeq):
				idx = i % bufSize
				s.sendto(msgBuf[idx], (IP, peerPort))
				print '[{0}] packet{1} {2} sent'.format(time.time(), i, msgBuf[idx][-1])
			sys.stdout.flush()
		else:
			if (not timerStop.is_set()):
				timerCnt = timerCnt + 1
				sys.stdout.flush()
				time.sleep(0.05)

def makePkt(nextSeq, dataType, data):
	return str(nextSeq) + str(dataType) + str(data)

def drop():
	global N, P, curN
	
	if (N != ''):
		if (curN == N):
			curN = 0
			return True
		else:
			curN = curN + 1
	if (P != ''):
		r = random.random()
		if (r < P):
			return True
		else:
			return False
	return False
		


#---------------------- send packet -------------------------
def msgSend(s, data):
	global nextSeq, msgBuf, base, bufSize, DATA, peerPort, IP, sendPackets
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
	global totalPackets, sendDrop, sendPackets
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	print 'node> ',
	while (True):
		sys.stdout.flush()
		msg = raw_input()
		msg = msg.split(' ')[1]
		totalPackets = len(msg)
		for i in range(len(msg)):
			msgSend(s, msg[i])


#---------------------- receive packet -------------------------
def msgRev():
	global base, nextSeq, timerStop, expSeq, selfPort, IP, ACK, DATA, END, sendDrop, sendPackets, recvDiscard, recvPackets, totalPackets
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((IP, selfPort))
	while (True):
		data, (addr, port) = s.recvfrom(1024)
		msgType = int(data[-2])
		msgSeq = int(data[0:-2])
		msgData = data[-1]

		if msgType == ACK: 
			sendPackets = sendPackets + 1
			if (drop()):
				sendDrop = sendDrop + 1
				print '[{0}] ACK{1} discarded'.format(time.time(), msgSeq)
			else:
				if msgSeq == base:
					print '[{0}] ACK{1} received, window moves to {2}'.format(time.time(), msgSeq, base % bufSize)
					base = base + 1
					if (base == nextSeq):
						timerStop.set()
					else:
						startTimer()
				if totalPackets == base:
					print '[Summary] {0}/{1} packets discarded, loss rate = {2}%'.format(sendDrop, sendPackets, float(sendDrop)/float(sendPackets) * 100)
					pkt = makePkt(0, END, 0)	
					s.sendto(pkt, (IP, peerPort))
					exit(0)
					 

		elif msgType == DATA:
			recvPackets = recvPackets + 1
			if (drop()):
				recvDiscard = recvDiscard + 1
				print '[{0}] packet{1} discarded'.format(time.time(), msgSeq)
			else:
				if msgSeq == expSeq:
					pkt = makePkt(expSeq, ACK, 0)
					s.sendto(pkt, (IP, peerPort))
					expSeq = expSeq + 1
					print '[{0}] packet{1} {2} received'.format(time.time(), msgSeq, msgData)
					print '[{0}] ACK{1} sent, expecting packet{2}'.format(time.time(), expSeq - 1, expSeq)
				else:
					if (expSeq > 0):		
						tmp = msgSeq
						if (msgSeq >= expSeq - 1):
							tmp = expSeq - 1
						pkt = makePkt(tmp, ACK, 0)
						s.sendto(pkt, (IP, peerPort))
						print '[{0}] ACK{1} sent, expecting packet{2}'.format(time.time(), tmp, tmp + 1)
		else:
			print '[Summary] {0}/{1} packets dropped, loss rate = {2}%'.format(recvDiscard, recvPackets, float(recvDiscard)/float(recvPackets) * 100)
			exit(0)
				
						
				

		sys.stdout.flush()
				
		

def main():
	global timerStop, timerThread
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	timerStop.set()
	timerThread = threading.Thread(target = timer, args = (s,))
	timerThread.daemon = True
	timerThread.start()
	listenThread = threading.Thread(target = msgRev)
	listenThread.daemon = True
	listenThread.start()
	sendHelper()

argParse()
main()




