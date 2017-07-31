import json
import logging
from threading import Thread
import Queue

logger = logging.getLogger("events")

'''
 {"event":{"type": ["spos"|
                     "cpos"|
                     "mode_change"],
                     "x":<x>, "y":<y>, "z":<z>, :mode":<mode>'''

''' Listens on the event queue, and publishes events to listeners'''
#arguably, this ought to be a general class that I just use....

    
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
#    eventQueue.put(json.dumps(event))
    eventQueue.put(event)
    
def addListener(eventHandler, msgType):
    eventHandlers.append({"handler": eventHandler, "msgType":msgType})
    
def removeListener(eventHandler):
    for handler in eventHandlers:
        if handler["handler"] == eventHandler:
            eventHandlers.remove(handler)

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
                msgType = msg["msgType"]
                for eventHandler in eventHandlers:
                    if msgType == eventHandler["msgType"] or msgType in eventHandler["msgType"]:
                        eventHandler["handler"](msg)
            except Queue.Empty:
                # just timeout, completely expected
                pass
            except Exception:
                logger.exception("Unexpected exception in flame broadcast thread")
                        
    def shutdown(self):
        self.running = False
