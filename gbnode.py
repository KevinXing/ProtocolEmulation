import argparse
import threading

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
MSG = 0
DATA = 1
IP = "127.0.0.1"

# buffer
msgBuf = []
bufSize = ''
base = 0
nextSeq = 0
tail = 0

# timer
timerThread = None
timerStop = threading.Event()
timerCnt = 0
#---------------------- parse argument -------------------------
def checkPort(port):
	if (port < 1024 or port > 65536):
		print 'port ' + str(port) + 'invalid'
		exit(2) 

#python gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> j -p <value-of-p>]
def argParse():
	global selfPort, peerPort, winSize, N, P
	parser = argparse.ArgumentParser()
	parser.add_argument('selfPort')
	parser.add_argument('peerPort')
	parser.add_argument('winSize')
	parser.add_argument('-d', dest = 'N')
	parser.add_argument('-p', dest = 'P')
	try:
		selfPort = int(selfPort)
		checkPort(selfPort)
		peerPort = int(peerPort)
		checkPort(selfPort)
		winSize = int(winSize)
		N = int(N)
		P = float(P)
		bufSize = 2 * winSize
	except ValueError:
		print 'input invalid'



#---------------------- shared functions --------------------
def startTimer():
	global timerThread, timerStop
	timerCnt = 0
	timerStop.clear()

def makePkt(nextSeq, dataType, data):
	return str(nextSeq) + str(dataType) + data

#---------------------- send packet -------------------------
def msgSend(s, data):
	global nextSeq, msgBuf, base
	idx = nextSeq % bufSize
	while (idx == (base + winSize) % bufSize):
		pass
	msgBuf[idx] = makePkt(nextSeq, dataType, data)
	s.sendto(msgBud[idx], (IP, peerPort))
	if (base == nextSeq):
		startTimer()	
	nextSeq = nextSeq + 1


def sendHelper():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	while True:
		msg = raw_input()
		for i in range(len(msg)):
			msgSend(s, data)



def main():
	global timerStop, timerThread
	timerStop.set()
	timerThread = threading.Thread(target = timer)
	timerThread.start()



