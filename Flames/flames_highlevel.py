''' And the flame effects connector code looks something like this: '''
import Queue
import json
import logging

logger = logging.getLogger("flames")

msgQueue = None
disabledPoofers = list()
globalEnable = True
disabledFlameEffects = list()
flameEffects = list()

def init(flameQueue, flameEffectsFile):
    global msgQueue
    msgQueue = flameQueue
    try:
        with open(flameEffectsFile) as f:
            flameSequences = json.load(f)
            for sequence in flameSequences:
                flameEffects.append(sequence["name"])
    except KeyError:
        log.exception("Misformatted flame effects file")
    
def shutdown():
    pass
    
def getFlameEffects():
    return flameEffects
    
def doFlameEffect(flameEffectName):
    if not flameEffectName in disabledFlameEffects:
        flameEffectMsg = {"type":"flameEffectStart", "name":flameEffectName}
        msgQueue.put(json.dumps(flameEffectMsg))
    
def stopFlameEffect(flameEffectName):
    flameEffectMsg = {"type":"flameEffectStop", "name":flameEffectName}
    msgQueue.put(json.dumps(flameEffectMsg))
    
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
        msgQueue.put(json.dumps(flameEffectMsg))

def enablePoofer(pooferId):
    if pooferId in disabledPoofers:
        disabledPoofers.remove(pooferId)
        flameEffectMsg = {"type":"pooferEnable", "name":pooferId}
        msgQueue.put(json.dumps(flameEffectMsg))
    
def globalPause():
    flameEffectMsg = {"type":"stop"}
    globalEnable = False
    msgQueue.put(json.dumps(flameEffectMsg))

def globalRelease():
    globalEnable = True
    flameEffectMsg = {"type":"resume"}
    msgQueue.put(json.dumps(flameEffectMsg))
    
def isStopped():
    return not globalEnable
   
def getDisabledPoofers():
    return disabledPoofers
    
def getDisabledFlameEffects():
    return disabledFlameEffects