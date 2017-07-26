''' And the flame effects connector code looks something like this: '''
import Queue
import json
import logging
from threading import Thread
from threading import Lock
from websocket_server import WebsocketServer
import event_manager

logger = logging.getLogger("flames")

cmdQueue   = None       # requests from upper level
disabledPoofers = list()
globalEnable = True
flameEffects = list()
disabledFlameEffects = list()
activeFlameEffects = list()
stateThread = None
stateLock   = None


def init(flameQueue, flameEffectsFile):
    global cmdQueue
    global stateThread
    global stateLock 
    logger.info("Flame Manager Init, flameEffectsFile {}".format(flameEffectsFile))
    stateLock = Lock()
    cmdQueue = flameQueue
    try:
        with open(flameEffectsFile) as f:
            flameSequences = json.load(f)
            for sequence in flameSequences:
                flameEffects.append(sequence["name"])
    except KeyError:
        log.exception("Misformatted flame effects file")
        
    event_manager.addListener(eventHandler)

    
def shutdown():
    logger.info("Flame Manager Shutdown")
    
def getFlameEffects():
    return flameEffects
    
def doFlameEffect(flameEffectName):
    if not flameEffectName in disabledFlameEffects:
        flameEffectMsg = {"type":"flameEffectStart", "name":flameEffectName}
        cmdQueue.put(json.dumps(flameEffectMsg))
    
def stopFlameEffect(flameEffectName):
    flameEffectMsg = {"type":"flameEffectStop", "name":flameEffectName}
    cmdQueue.put(json.dumps(flameEffectMsg))
    
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

def isFlameEffectActive(flameEffectName):
    return flameEffectName in activeFlameEffects
    
def isFlameEffectEnabled(flameEffectName):
    return not flameEffectName in disabledFlameEffects

def disablePoofer(pooferId):
    if not pooferId in disabledPoofers:
        disabledPoofers.append(pooferId)
        flameEffectMsg = {"type":"pooferDisable", "name":pooferId}
        cmdQueue.put(json.dumps(flameEffectMsg))

def enablePoofer(pooferId):
    if pooferId in disabledPoofers:
        disabledPoofers.remove(pooferId)
        flameEffectMsg = {"type":"pooferEnable", "name":pooferId}
        cmdQueue.put(json.dumps(flameEffectMsg))
        
def isPooferEnabled(pooferId):
    return not (pooferId in disabledPoofers)
    
def isPooferActive(pooferId):
    return True  # XXX FIXME. Want to be listening for events!
    
def globalPause():
    flameEffectMsg = {"type":"stop"}
    globalEnable = False
    cmdQueue.put(json.dumps(flameEffectMsg))

def globalRelease():
    globalEnable = True
    flameEffectMsg = {"type":"resume"}
    cmdQueue.put(json.dumps(flameEffectMsg))
    
def isStopped():
    return not globalEnable
   
def getDisabledPoofers():
    return disabledPoofers
    
def getDisabledFlameEffects():
    return disabledFlameEffects
    
# XXX - event handler from low level code...
def eventHandler(msg):
    pass