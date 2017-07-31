'''Flame controller. Responsible for high-level management of flame effects. All objects 
or modules wanting to know the status of poofers or sequences should call into this module.
Similarly, all objects or modules wanting to change the status of poofers or sequences -
including running a sequence - should call into this module.

Mediates with the low-level flames_drv via a message Queue (flameQueue, for pushing
commands to the low level code) and event listener (for receiving events created by the
flames driver)'''

import Queue
import json
import logging
from threading import Thread
from threading import Lock
from websocket_server import WebsocketServer
import mock_event_producer as mockDriver
import event_manager
import pattern_manager


# XXX - FIXME - need to actually listen for events! Create a mock event producer 

logger = logging.getLogger("flames")

cmdQueue   = None       # requests from upper level
disabledPoofers = list()
globalEnable = True
disabledFlameEffects = list()
activeFlameEffects = list()
gUseDriver = False


def init(flameQueue, useDriver=True):
    global cmdQueue
    global gUseDriver
    logger.info("Flame Controller Init")
    cmdQueue = flameQueue
    gUseDriver = useDriver

    event_manager.addListener(eventHandler)

    
def shutdown():
    logger.info("Flame Controller Shutdown")
    
    
def doFlameEffect(flameEffectName):
    logger.debug("Doing flame effect {}".format(flameEffectName))
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
        if gUseDriver:
            flameEffectMsg = {"type":"pooferDisable", "name":pooferId}
            cmdQueue.put(json.dumps(flameEffectMsg))
        else:
            mockDriver.disablePoofer(pooferId)

def enablePoofer(pooferId):
    if pooferId in disabledPoofers:
        disabledPoofers.remove(pooferId)
        if gUseDriver:
            flameEffectMsg = {"type":"pooferEnable", "name":pooferId}
            cmdQueue.put(json.dumps(flameEffectMsg))
        else:
            mockDriver.enablePoofer(pooferId)
        
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