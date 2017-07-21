import json
import logging
from threading import Thread
import Queue

logger = logging.getLogger("flames")

'''
 {"event":{"type": ["poofer_on"|
                     "poofer_off"|
                     "pattern_start"|
                     "pattern_stop"|
                     "poofer_enabled"|
                     "poofer_disabled"|
                     "pattern_enabled"|
                     "pattern_disabled"], "id": [pooferId | patternName]}} '''
                     
''' Listens on the event queue, and publishes events to listeners'''
    
eventThread = None
eventQueue  = None
eventHandlers = list()

def init():
    global eventThread
    global eventQueue
    logger.info("Event Manager Init")
    eventQueue = Queue.Queue()
    eventThread = EventManagerThread(eventQueue)
    eventThread.start()
    
def shutdown():
    global eventThread
    if eventThread:
        logger.info("Event Manager Shutdown")
        eventThread.shutdown()
        eventThread.join()
        eventThread = None
    eventHandlers = list()
    
def postEvent(event):
    eventQueue.put(json.dumps(event))
    
def addListener(eventHandler):
    eventHandlers.append(eventHandler)
    
def removeListener(eventHandler):
    try:
        eventHandlers.remove(eventHandler)
    except:
        pass # most likely a not-found error, which we don't care about

class EventManagerThread(Thread):
    def __init__(self, eventQueue):
        Thread.__init__(self)
        self.eventQueue = eventQueue
        
    def run(self):
        self.running = True
        while (self.running):
            try:
                msg = self.eventQueue.get(True, 1) # 1 second timeout
                logger.debug("received event {}".format(msg))
                for eventHandler in eventHandlers:
                    eventHandler(msg)
            except Queue.Empty:
                # just timeout, completely expected
                pass
            except Exception:
                logger.exception("Unexpected exception in flame broadcast thread")
                        
    def shutdown(self):
        self.running = False
