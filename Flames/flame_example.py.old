# Threading and message passing framework

''' For the Flame Pi, I'd suggest the following architecture:
- A thread responsible for speaking the ! protocol. Let's call this the 'Poofer Firing'
thread, since poofer_firing.py is Josh's name for this code
- A thread responsible for interfacing with the out side world. I'll call this the Webserver 
thread.
- A thread responsible for handling events caused by sculpture positional triggers
- A message passing system between the threads
- A bit of connector code (not on its own thread) that is responsible for the high level
interface between the thread speaking the ! protocol and the other threads. This thread
maintains some global state, and is responsible for formatting and passing messages

(And yeah, these could be processes instead of threads, and the Webserver thread might be 
spinning up its own threads to handle incoming HTTP requests. If we want to use processes
instead of threads we can revisit that in a week or so, and webserver frameworks
spin up their own threads in a way that's pretty much transparent to whoever is using them.)

The code ends up looking something like this:
(see poofer.py for my current set up code, which doesn't have all of these threads, but does
have some additional configuration '''

import Queue
import time
import Logging
import flames_api
import poofer_firing
import triggers
import flame_effects

if __name__ == '__main__':
    
    # For cleanup cleanliness
    pooferEventQueue = None

    try:
        # create queue for sending
        pooferEventQueue = Queue.Queue()
        
        # Initialize Poofer thread
        poofer_firing.init(pooferEventQueue)
        
        # Initialize trigger thread
        triggers.init()
    
        # initialize connector between poofer thread and the rest of the world
        flame_effecfs.init(pooferEventQueue)
    
        # Initialize webserver
        # (nb - depending on the framework used, this may not return - for instance
        # httpserver.serve_forver(), used by BasicHttpServer, just runs off and listens
        # for connections. In that case, you don't need to track the webThread variable,
        # and you don't need to try to shut it down
        flames_api.init()
       
        # you need this only if the above call returns...
        while True:
            time.sleep(5)
            
    except Exception:
        logger.exception("Flame Exit:")
        flames_api.shutdown()
        poofer_firing.shutdown()
        trigger_thread.shutdown()
        flame_effects.shutdown()
        
            
''' The poofer firing code would be structured something like this:'''
import Thread
import Queue
import json

pooferFiringThread = None

def init(msgQueue):
    global pooferFiringThread
    pooferFiringThread = PooferFiringThread(msgQueue)
    pooferFiringThread.run()
    
def shutdown():
    global pooferFiringThread
    if pooferFiringThread != None:
        pooferFiringThread.shutdown()
        pooferFiringThread = None
    
class PooferFiringThread(Thread):
    TIMEOUT = 1 # 1 second timeout, even if no events
    
    def __init__(self, msgQueue):
        Thread.__init__(self)
        self.msgQueue = msgQueue
        self.running = False
        self.pooferEvents = list() # time-ordered list of poofer events
        
    def shutdown():
        self.running = False
    
    def run(self):
        self.running = True
        while(self.running):
            if len(self.pooferEvents > 0): # there are poofer events
                currentTime - time.time()
                # pop events off of the list. If the current time is greater than
                # the time associated with the event, set up for serial       
            if len(self.pooferEvents > 0): # there are poofer events in the future
                waitTime = self.events[0]["time"] - time.time()
            else:
                waitTime = PooferFiringThread.TIMEOUT
            
            try:
                msg = msgQueue.get(True, waitTime)
                # parse message. If this is a request to do a flame sequence,
                # set up poofer events, ordered by time. Event["time"] attribute
                # should be current time (time.time()) plus the relative time from
                # the start of the sequence
                msgObj = json.loads(msg)
                type = msgObj["type"]
                if type == "flameEffectStart":
                    # figure out firing sequence associated with the name, set
                    # up poofer events
                # else - whatever other type of event you want to process ...
            except Queue.Empty:
                # this is just a timeout - completely expected. Run the loop
                pass
            except Exception:
                # log this... Not expected!
                

''' And the flame effects connector code looks something like this: '''
import Queue
import json

msgQueue = None
disabledPoofers = list()
globalEnable = True
disabledFlameEffects = list()

def init(flameQueue):
    global msgQueue
    msgQueue = flameQueue
    
def shutdown():
    pass
    
def doFlameEffect(flameEffectName):
    if not flameEffectName in disabledFlameEffects:
        flameEffectMsg = {"type":"flameEffectStart", "name":flameEffectName}
        msgQueue.put(json.dumps(flameEffectMsg)
    
def stopFlameEffect(flameEffectName):
    flameEffectMsg = {"type":"flameEffectStop", "name":flameEffectName}
    msgQueue.put(json.dumps(flameEffectMsg)
    
def disableFlameEffect(flameEffectName):
    if not flameEffectName in disabledFlameEffects:
        disabledFlameEffects.append(flameEffectName)
    else:
        # log this - disable called twice on same flame effect  
        pass
    stopFlameEffect(flameEffectName)

def enableFlameEffect(flameEffectName):
    if flameEffectName in disabledFlameEffects:
        disabledFlameEffects.remove(flameEffectName)
    else:
        # log this - enable called twice on same flame effect  
        pass

def disablePoofer(pooferId):
    if not pooferId in disabledPoofers:
        disabledPoofers.append(pooferId)
        flameEffectMsg = {"type":"pooferDisable", "name":pooferId}
        msgQueue.put(json.dumps(flameEffectMsg)

def enablePoofer(pooferId):
    if pooferId in disabledPoofers:
        disabledPoofers.remove(pooferId)
        flameEffectMsg = {"type":"pooferEnable", "name":pooferId}
        msgQueue.put(json.dumps(flameEffectMsg)
    
def globalPause():
    flameEffectMsg = {"type":"stop"}
    globalEnable = False
    msgQueue.put(json.dumps(flameEffectMsg)

def globalRelease():
    globalEnable = True
    flameEffectMsg = {"type":"resume"}
    msgQueue.put(json.dumps(flameEffectMsg)
    
def isStopped():
    return not globalEnable
   
def getDisabledPoofers():
    return disabledPoofers
    
def getDisabledFlameEffects():
    return disabledFlameEffects
    

    
    
    
    


    

            

        
        
        
    


