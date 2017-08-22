import logging
import time
from threading import Thread
import event_manager
import hydraulics_drv
#import hydraulics_playback

gAttractModeTimeout = 30 #
gAutoAttractModeEnabled = False
gOldPos = [0,0,0]
gMaxDelta = 20  # 0-4095 scale
gAttractModeStartTime = 0
gInAttractMode = False
gAttractMonitorThread = None
gOriginalDriverInput = "controller"
gInterruptable = True
isRunning = True

logger = logging.getLogger("hydraulics")

def init(timeout = 30, delta=200, autoEnable=False):
    global gAttractModeStartTime
    global gAttractMonitorThread
    
    logger.info("Attract Manager Init, timeout {}, autoEnable {}, delta {}".format(timeout, autoEnable, delta))
    
    attractModeTimeout(timeout)
    attractModeDelta(delta)
    event_manager.addListener(eventHandler, "cpos")
    
    gAttractModeStartTime = time.time() + gAttractModeTimeout
    gAttractMonitorThread = Thread(target=attractModeMonitor)
    gAttractMonitorThread.start()

def shutdown():
    global isRunning
    global gAttractMonitorThread
        
    logger.info("Attract Manager Shutdown")
    
    isRunning = False
    if gAttractMonitorThread != None:
        gAttractMonitorThread.join()
        gAttractMonitorThread = None
        
def inAttractMode():
    return gInAttractMode
    
# interruptable is sort of a mode. You've got
# - autoattract
# - one shot attract
# - continuous attract
# - attract on/off (separate switch)
# So maybe I should have a way of setting that?
# Who controls? Us. Event manager can handle the autoattract
# Other issues:
# - Attract mode recovery time. How long does it take to recover from a movement?
# What do we do to get the sculpture into position? Do we wait until get gets close?
# (would have to change the playback manager)

def startAttractMode(interruptable=True):
    global gInAttractMode
    global gAttractModeTimeout
    global gOriginalDriverInput
    global gInterruptable
    
    gInAttractMode = True
    logger.info("Starting attract mode")
    gOriginalDriverInput = hydraulics_drv.getInputSource()
#    hydraulics_playback.startLeadIn()
    hydraulics_drv.setInputSource("recording")
#    gAttractModeTimeout = 0
    gInterruptable = interruptable
    
def interruptable(tf=None):
    global gInterruptable
    if tf == None:
        return gInterruptable
    else:
        gInterruptable = tf

def stopAttractMode():
    global gInAttractMode
    
    logger.info("leaving attract mode")
    hydraulics_drv.setInputSource(gOriginalDriverInput)
    gInAttractMode = False
    

def attractModeTimeout(timeout=None): # time in seconds
    global gAttractModeTimeout
    global gAttractModeStartTime
    
    if timeout == None:
        return gAttractModeTimeout
    
    else:
        gAttractModeTimeout = timeout # XXX check numeric
        gAttractModeStartTime = time.time() + timeout

def autoAttractModeEnabled(tf=None):
    global gAutoAttractModeEnabled
    global gAttractModeStartTime
   
    if tf == None:
        return gAutoAttractModeEnabled
    else:
        logger.debug("Attract mode enable called, tf is {}".format(tf)) 
        gAutoAttractModeEnabled = (tf == True)
        if (gAutoAttractModeEnabled) :
            gAttractModeStartTime = time.time() + gAttractModeTimeout 	 

def attractModeDelta(delta=None):
    global gMaxDelta
    if delta == None:
        return gMaxDelta
    else:
        gMaxDelta = delta # XXX check numeric
        
def eventHandler(msg):
    global gInAttractMode
    global gAttractModeStartTime
    global gOldPos

    if msg["msgType"] == "cpos":
        x = msg["x"]
        y = msg["y"]
        z = msg["z"]
        
        # XXX - do I want to add a low-pass filter?
        if ((abs(x - gOldPos[0]) > gMaxDelta) or
            (abs(y - gOldPos[1]) > gMaxDelta) or
            (abs(z - gOldPos[2]) > gMaxDelta)):
            logger.debug("Position has changed. Resetting attract mode position and timeout")
            gOldPos[0] = x
            gOldPos[1] = y
            gOldPos[2] = z
            gAttractModeStartTime = time.time() + gAttractModeTimeout 
            if gInAttractMode and gInterruptable:
                stopAttractMode()

        
def attractModeMonitor():
    while isRunning:
        if (time.time() > gAttractModeStartTime and (not gInAttractMode) and gAutoAttractModeEnabled):  
            logger.info("Starting attract mode automatically")
            startAttractMode()
        time.sleep(1)
        logger.debug("Attract monitor. gInAttractMode: {}, gAutoAttract: {}, startTime: {}".format(gInAttractMode, gAutoAttractModeEnabled, gAttractModeStartTime))     
        logger.debug("ATTRACT monitor. gInterruptible: {}".format(gInterruptable))
if __name__ == "__main__":
    try:
        logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d: %(message)s', level=logging.DEBUG)
        event_manager.init()
        hydraulics_drv.init()
        init(2, True)
        event_manager.postEvent({"msgType":"cpos", "x":50, "y":50, "z":50})
        time.sleep(5)
        if gInAttractMode:
            logger.debug("SUCCESS! In attract mode!")
        else:
            logger.debug("FAILURE! Not in attract mode")
        event_manager.postEvent({"msgType":"cpos", "x":500, "y":50, "z":50})
        time.sleep(1)
        if not gInAttractMode:
            logger.debug("SUCCESS! Not in attract mode!")
        else:
            logger.debug("FAILURE! In attract mode")
    except Exception:
        logger.exception("Unexpect failure in test")
        
    hydraulics_drv.shutdown()
    event_manager.shutdown()
    shutdown()
    
        
