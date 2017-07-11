''' Set up socket to listen on known port. If we get a connection, attach and spin off
thread to send hydraulic data'''

from threading import Thread, Lock
import socket
import logging

hydraulics_connection_manager = None
logger = logging.getLogger('hydraulics')


def init(port):
    global hydraulics_connection_manager
    hydraulics_connection_manager = HydraulicsConnectionManager(port)
    hydraulics_connection_manager.start()
    
def shutdown():
    hydraulics_connection_manager.stop()
    
def sendMessage(message):
    hydraulics_connection_manager.queueMessage(message)


class HydraulicsConnectionManager(Thread):
    ''' Responsible for mediating between the hydraulics system (which is generating
        position events) and clients who want position information. Listens for connections 
        from clients, and spawns off threads to respond to them. Gets notified of events
        from hydraulics system, and forwards events to from the all streamer threads, 
        which send them to their attached clients.
        
        The architecture is designed to allow a distributed system where the hydraulics
        system resides on one computer, and consumers of this data reside on others. (And
        yeah, I could use a standard pub-sub system, but that feels like overkill here.)
    '''
        
    def __init__(self, port):
        Thread.__init__(self)
        self.port = port
        self.threads = list()
        self.threadLock = Lock()
        
    def run(self):
        self.running = True
        while self.running: 
            try:
                # set up socket
                self.hydraulics_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.hydraulics_socket.bind((socket.gethostname(), self.port))
                self.hydraulics_socket.settimeout(1)  # XXX REUSE ADDR?
                self.hydraulics_socket.listen(5)  # really should only ever be one or two connection requests

                # use socket
                while self.running:
                    try: 
                        (clientsocket, address) = self.hydraulics_socket.accept() # socket blocks by default
                    except socket.timeout:
                        continue
                        
                    hydraulics_stream_thread = PositionStreamer(clientsocket, self)
                    hydraulics_stream_thread.start()
                    self.threadLock.acquire()
                    self.threads = self.threads.append(hydraulics_stream_thread)
                    self.threadLock.release()
            
                    # XXX - do I want to use multiprocessing here? Rpis are quad core
                    # do I need the lock if I'm doing multicoring? check all of this
            except Exception as e: 
                print "exception on streamer", e
                logger.exception("Error on hydraulics listener socket. Will rebind")
                self.hydraulics_socket.shutdown(socket.SHUT_RDWR)
                self.hydraulics_socket.close()
                self.hydraulics_socket = None
                pass
            
    def stop(self):
        self.running = False
        for streamThread in self.threads:
            streamThread.stop()
            streamThread.join()
        
    def queueMessage(self, msg):
        for streamThread in self.threads:
            streamThread.queueMessage(msg)
        
    def releaseChild(self, streamThread):
        self.threadLock.acquire()
        if streamThread in self.threads:
            self.threads.remove(streamThread)
        self.threadLock.release()
        
class PositionStreamer(Thread):
    ''' Streams sculpture position information to other side of connection '''
    def __init__(self, clientSocket, parentThread):
        Thread.__init__(self)
        self.clientSocket = clientSocket
        self.messageLock = threading.Lock()
        self.messageFifo = list()
        self.parent = parentThread
        
    def run(self):
        self.running = True
        
        while self.running:
            try:
                # Check for message from the hydraulics system. If you find one, send it
                if len(self.messageFifo) > 0:
                    self.messageLock.acquire()
                    msg = self.messageFifo.pop(0)
                    self.messageLock.release()
                    sentBytes = 0
                    msgLen = len(msg)
                    while sentBytes < msgLen:
                        nBytes = self.clientSocket.send(msg[totalsent:])
                        if nBytes == 0:
                            raise RuntimeError("0 bytes sent; socket connection broken")
                            self.running = False
                            break
                        sentBytes = sentBytes + nBytes  
            except:
                logger.exception("Error listening for on hydraulics socket, closing socket")
                self.clientSocket.shutdown(socket.SHUT_RDWR)
                self.clientSocket.close()
                self.parent.releaseChild(self)
                
    def queueMessage(self, message):
        self.messageLock.acquire()
        if len(messageFifo < self.MAX_MESSAGE_LEN):
            self.messageFifo.append(message)
        else:
            logger.warning("Could not queue hydraulics position, too many messages")
        self.messageLock.release()
        
    def stop(self):
        self.running = False
          

# who receives the shutdown signal from the keyboard or the kill signal? Is it always the parent, or not?
# Add log rotation - https://stackoverflow.com/questions/9106795/python-logging-and-rotating-files
# And questions about multiprocessing to allow me to use all of the cores
# And some test code, of course
# Allow changing of some configuration options from GUI
# test mode?
# test trigger - single point, multi point linger, multipoint passthrough, failure cases
# test sample data


