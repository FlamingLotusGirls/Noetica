''' mock flame event producer '''

import event_manager
from operator import itemgetter
import random
from threading import Thread
import time

import poofermapping

gFiringThread = None

def init():
    pass
    
def shutdown():
    stopFiringRandomPoofers()


def turnOnPoofer(pooferName):
    event_manager.postEvent({"type":"poofer_on", "id":pooferName})

def turnOffPoofer(pooferName):
    event_manager.postEvent({"type":"poofer_off", "id":pooferName})
    
def enablePoofer(pooferName):
    event_manager.postEvent({"type":"poofer_enabled", "id":pooferName})

def disablePoofer(pooferName):
    event_manager.postEvent({"type":"poofer_disabled", "id":pooferName})
    
def patternStart(patternName):
    event_manager.postEvent({"type":"pattern_start", "id":patternName})

def patternStop(patternName):
    event_manager.postEvent({"type":"pattern_stop", "id":patternName})

def patternEnabled(patternName):
    event_manager.postEvent({"type":"pattern_enabled", "id":patternName})

def patternDisabled(patternName):
    event_manager.postEvent({"type":"pattern_disabled", "id":patternName})
    
def fireRandomPoofers():
    global gFiringThread
    gFiringThread = RandomPooferFiringThread()
    gFiringThread.start()
    
def stopFiringRandomPoofers():
    global gFiringThread
    if gFiringThread != None:
        gFiringThread.stop()
        gFiringThread.join()
    gFiringThread = None    
    
class RandomPooferFiringThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.availablePoofers = poofermapping.mappings.keys()
        self.poofersActive = list()
    
    def run(self):
        self.isRunning = True
        nextFiringTime = 0
        sleepTime = 0
        while (self.isRunning):
            print "SleepTime is", sleepTime
            time.sleep(sleepTime)
            curTime = time.time()
            
            # Set up some new poofers to fire
            nPoofers = random.randrange(0, min(4, len(self.availablePoofers)))
            print "turning on ", nPoofers
            firingPoofers = list()
            if (curTime > nextFiringTime): 
                while (len(firingPoofers) < nPoofers):
                    pooferIdx = random.randrange(0, nPoofers - len(firingPoofers))
                    poofer = {"id":self.availablePoofers[pooferIdx], "timeStop": curTime + (float(100*random.randrange(3, 30))/1000)}
                    print("Turning on poofer", poofer["id"])
                    turnOnPoofer(poofer["id"])
                    firingPoofers.append(poofer)
                    del self.availablePoofers[pooferIdx]
            
                self.poofersActive = self.poofersActive + firingPoofers
                print self.poofersActive
                self.poofersActive.sort(key=itemgetter("timeStop"))
                nextFiringTime = curTime + random.uniform(1.0, 5.0)
            
            # See if any have stopped firing
            for i in range(0, len(self.poofersActive)):
                poofer = self.poofersActive[i]
                if poofer["timeStop"] > curTime:
                    print("Turning off poofer", poofer["id"])
                    turnOffPoofer(poofer["id"])
                    self.availablePoofers.append(poofer["id"])
                else:
                    self.poofersActive = self.poofersActive[:i]
                    break
                    

            # calculate sleep time
            if len(self.poofersActive) > 0:
                offTime = self.poofersActive[0]["timeStop"] - curTime
            else:
                offTime = 5
                
            sleepTime = min(offTime, nextFiringTime - curTime)
            
    
    def stop(self):
        self.isRunning = False

if __name__ == "__main__":
    try: 
        event_manager.init()
        fireRandomPoofers()
        time.sleep(10)
        print "Stop now!"
        stopFiringRandomPoofers()
        event_manager.shutdown()
    except Exception as e:
        print "Exception occurs!", e
        stopFiringRandomPoofers()
        event_manager.shutdown()
    except KeyboardInterrupt:
        print "Keyboard Interrupt!"
        stopFiringRandomPoofers()
        event_manager.shutdown()
    
        
