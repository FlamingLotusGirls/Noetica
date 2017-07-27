''' Set up socket to listen on known port. If we get a connection, attach and spin off
thread to send hydraulic data'''

from threading import Thread, Lock
import socket
import logging
import Queue

hydraulics_connection_manager = None
logger = logging.getLogger('hydraulics')


def init(port):
    global hydraulics_connection_manager
    logger.info("Hydraulics stream init, port {}".format(port))
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
#                self.hydraulics_socket.bind((socket.gethostname(), self.port))
                self.hydraulics_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.hydraulics_socket.bind(("localhost", self.port))
                logger.info("bind to {}:{}".format(socket.gethostname(), self.port))
                self.hydraulics_socket.settimeout(5)  # XXX REUSE ADDR?
                self.hydraulics_socket.listen(5)  # really should only ever be one or two connection requests

                # use socket
                while self.running:
                    try: 
                        logger.debug("socket accept... waiting")
                        (clientsocket, address) = self.hydraulics_socket.accept() # socket blocks by default
                    except socket.timeout:
                        continue
                        
                    hydraulics_stream_thread = PositionStreamer(clientsocket, self)
                    self.threadLock.acquire()
                    self.threads.append(hydraulics_stream_thread)
                    self.threadLock.release()
                    hydraulics_stream_thread.start()
            
                    # XXX - do I want to use multiprocessing here? Rpis are quad core
                    # do I need the lock if I'm doing multicoring? check all of this
            except Exception as e: 
                logger.exception("Error on hydraulics listener socket. Will rebind")
                #self.hydraulics_socket.shutdown(socket.SHUT_RDWR)
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
        logger.debug("attempting to release streamthread")
        self.threadLock.acquire()
        if streamThread in self.threads:
            self.threads.remove(streamThread)
        self.threadLock.release()
        
class PositionStreamer(Thread):
    ''' Streams sculpture position information to other side of connection '''
    MAX_MESSAGE_LEN = 10
    
    def __init__(self, clientSocket, parentThread):
        Thread.__init__(self)
        self.clientSocket = clientSocket
        self.messageFifo = Queue.Queue()
        self.parent = parentThread
        
    def run(self):
        self.running = True
        
        while self.running:
            try:
                # Check for message from the hydraulics system. If you find one, send it
                msg = self.messageFifo.get(timeout=1.0)
                sentBytes = 0
                msgLen = len(msg)
                while sentBytes < msgLen:
                    nBytes = self.clientSocket.send(msg[sentBytes:])
                    if nBytes == 0:
                        raise RuntimeError("0 bytes sent; socket connection broken")
                        self.running = False
                        break
                    sentBytes = sentBytes + nBytes 
                    logger.debug("sent {} bytes to consumer".format(sentBytes)) 
            except Queue.Empty:
                # Queue empty, nothing to see here
                pass
            except:
                logger.exception("Error listening for on hydraulics socket, closing socket")
                #self.clientSocket.shutdown(socket.SHUT_RDWR)
                self.clientSocket.close()
                self.parent.releaseChild(self)
                
    def queueMessage(self, message):
        try:
            self.messageFifo.put_nowait(message)
        except Queue.Full:
            logger.warning("Could not queue hydraulics position, too many messages")
        
    def stop(self):
        self.running = False
          

# who receives the shutdown signal from the keyboard or the kill signal? Is it always the parent, or not?
# And questions about multiprocessing to allow me to use all of the cores
# And some test code, of course
# test mode?
# test trigger - single point, multi point linger, multipoint passthrough, failure cases
# test sample data


