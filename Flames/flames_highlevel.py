''' And the flame effects connector code looks something like this: '''
import Queue
import json
import logging
from threading import Thread
from threading import Lock
from websocket_server import WebsocketServer
import event_manager
import pattern_manager

logger = logging.getLogger("flames")

cmdQueue   = None       # requests from upper level
disabledPoofers = list()
globalEnable = True
disabledFlameEffects = list()
activeFlameEffects = list()
stateThread = None
stateLock   = None


def init(flameQueue):
    global cmdQueue
    global stateThread
    global stateLock 
    logger.info("Flame Manager Init")
    stateLock = Lock()
    cmdQueue = flameQueue

    event_manager.addListener(eventHandler)

    
def shutdown():
    logger.info("Flame Manager Shutdown")
    
    
def doFlameEffect(flameEffectName):
    logger.debug("Doing flame effect {}".format(flameEffectName))
    if not flameEffectName in disabledFlameEffects:
        flameEffectMsg = {"type":"flameEffectStart", "name":flameEffectName}
        cmdQueue.put(json.dumps(flameEffectMsg))
    
def stopFlameEffect(flameEffectName):
    flameEffectMsg = {"type":"flameEffectStop", "name":flameEffectName}
    cmdQueue.put(json.dumps(flameEffectMsg))
    
def disableFlameEffect(flameEffectName):
    print "Disable Flame effect", flameEffectName
    if not flameEffectName in disabledFlameEffects:
        disabledFlameEffects.append(flameEffectName)
    else:
        # log this - disable called twice on same flame effect  
        pass
    stopFlameEffect(flameEffectName)

def enableFlameEffect(flameEffectName):
    print "Enable flame effect", flameEffectName
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
    global globalEnable
    flameEffectMsg = {"type":"stop"}
    globalEnable = False
    cmdQueue.put(json.dumps(flameEffectMsg))

def globalRelease():
    global globalEnable
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