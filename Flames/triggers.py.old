''' Trigger manager, and trigger objects '''

''' Handles triggering of pre-defined flame effects based on sculpture position. 
The TriggerManager listens to a socket over which sculpture position data is streamed, and 
feeds that information to a list of trigger objects. The trigger objects then call the flame
effects code when the appropriate conditions are met.

Triggers are defined in a json-formatted trigger file read in during initialization. 
Each individual object within the file has the following format:
{ "name":<name>, "points":["type":<"passthrough"|"linger">, "x":<x-coord>, "y":<y-coord>
                           "z":<z-coord>, "transitTime":<max time allowed to get to point
                                                         from previous point>
                           "lingerTime":<optional, time to linger if point type is "linger">,
                           "flameEffect":<optional, flame effect name to trigger>]} '''
                           
from threading import Thread
#from flameEffects import FlameEffects
import json
import logging
import time
import socket
import sys

triggerList = list()
triggerThread = None

logger = logging.getLogger('triggers')


def init(triggerFile, addr, port):
    global triggerThread
    print "INIT"
    logger.warning("wtf??")
    try:
        with open(triggerFile) as f:
            print "opened file", triggerFile
            triggerParams = json.load(f) 
        print "triggerparams are", triggerParams
        triggerThread = TriggerManager(addr, port, triggerParams)
        triggerThread.start()
    except IOError:
        logger.exception("Exception initializing triggers!")
        
def shutdown():
    print "Stopping trigger thread"
    global triggerThread
    if triggerThread != None:
        triggerThread.stop()
        triggerThread.join()
    triggerThread = None
    
def getTriggers():
    triggers = triggerThread.getTriggers()
    newTriggers = list()
    for trigger in triggers:
        newTrigger = {"name": trigger.getName(), "enabled": trigger.isEnabled(), 
                      "active": trigger.isActive()}
        newTriggers.append(newTrigger)
    return newTriggers
    
def enableTrigger(triggerName):
    triggers = triggerThread.getTriggers()
    for trigger in triggers:
        if trigger.getName() == triggerName:
            trigger.enable(True)
            break

def disableTrigger(triggerName):
    triggers = triggerThread.getTriggers()
    for trigger in triggers:
        if trigger.getName() == triggerName:
            trigger.enable(False)
            break
        
def _verifyTriggerParamsObject(triggerParamsObject):
    # XXX - I'm doing a lot of assignments here, but the point isn't to assign variables,
    # it's to test that the structure of the object is correct. There are probably better
    # ways to do this, but for now...
    try:
        name = triggerParamsObject["name"]
        points = triggerParamsObject["points"]
        for point in points:
            type = point["type"]
            if type != "linger" and type != "passthrough":
                raise KeyError("linger or passthrough required")
            x = point["x"]
            y = point["y"]
            z = point["z"]
            transitTime = point["transitTime"]
            if type == "linger":
                lingerTime  = point["lingerTime"]
        # NB - there should be at least one associated flame effect at the end, but
        # I'm going to punt on checking for it. The code will not crash without it.    
        return True
    except KeyError:
        log.exception("Malformed trigger parameter")
        return False
       
class TriggerManager(Thread): 
    ''' Maintains list of trigger objects, and feeds them data from the hydraulics 
        position system '''
    def __init__(self, listenAddr, listenPort, triggerParams):
        Thread.__init__(self)
        self.triggerList = list()
        self.listenAddr = listenAddr
        self.listenPort = listenPort
        self.running    = False
        self.socketInit = False
        self.hydraulics_socket = None
        
        print triggerParams

        for triggerParamsObject in triggerParams:
            print triggerParamsObject
            if _verifyTriggerParamsObject(triggerParamsObject):
                print "appending trigger object"
                triggerObject = TriggerObject(triggerParamsObject["name"], 
                                              triggerParamsObject["points"])
                self.triggerList.append(triggerObject)
                triggerObject.enable(True)
                              
# x = json.loads(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values())) # XXX this is a way of creating an object with attributes instead of a generic dict, but I don't quite understand how it works yet
                
    def run(self):
        self.running = True
        while self.running:
            try:
                if not self.socketInit:
                    self._connectHydraulicsSocket(self.listenAddr, self.listenPort)
                    self.socketInit = True
                    logger.info("Connected to hydraulics socket")
                
                # listen for message on queue
                msg = self.hydraulics_socket.recv(32)
                if len(msg) <= 0:
                    logger.warn("0 bytes received on trigger thread, disconnecting")  
                    #self.hydraulics_socket.shutdown(socket.SHUT_RDWR)
                    self.hydraulics_socket.close()
                    self.socketInit = False
                    continue
                    
                print 'received message on position socket', msg
                    
                msgObj = json.loads(msg) # XXX and what happens on exception here?            
                
                # got message, hand to objects
                for trigger in self.triggerList:
                    print "handing message to trigger"
                    trigger.processSculpturePosition(msgObj)
            except socket.error, (value, message):
                logger.exception("Socket error {}".format(message))
                # Attempt reconnect
                self.socketInit = False
                if self.hydraulics_socket != None:
                    #self.hydraulics_socket.shutdown(socket.SHUT_RDWR)
                    self.hydraulics_socket.close()
                    self.hydraulics_socket = None
                time.sleep(3)
            except:
                logger.exception("Error processing hydraulics position data")
                
    def stop(self):
        print "In manager thread. set running false"
        self.running = False
                
    def _connectHydraulicsSocket(self, addr, port):
        try:
            newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            newSocket.connect((addr, port))
            self.hydraulics_socket = newSocket
        except socket.error as e:
            #logger.exception("Socket error {}".format(message))
            newSocket.close()
            raise e
        # NB - these calls are expected to throw if there is a problem


            

# states are
DISABLED = "disabled"
LINGERING = "lingering" # waiting a while at a particular point
LOOKING = "looking"     # looking for a particular point


ENVELOPE_SIZE = 5

# XXX let's not bother with direction down the envelope right now. Just keep us in the envelope
# XXX - want a way to disable these guys!

class TriggerObject():
    ''' Object associated with a particular trigger sequence. The trigger manager feeds it
        position data from the sculpture; it is responsible for maintaining an internal 
        state (based upon past position data) and deciding when to trigger a flame effect '''
    def __init__(self, name, points):
        ''' params object is a list of points, 
            [{name:<triggerName>, points:[{type:"linger"|"passthrough", x:<x>, y:<y>, z:<z>, transitTime: <int>, <lingerTime:<int>>, <flameEffect:<effectName>>}]}]'''
        self.name   = name
        self.points = points
        self.state = DISABLED 
        self.pointTarget = 0 # target is first point
        self.lastTriggerPointTime = 0
        self.lingerTime = 0  # wall time - linger until this time
        print "INIT trigger object!!"
        
    def enable(self, bEnable):
        if bEnable:
            self._restartTrigger()
        else:
            self.state = DISABLED
            
    def getName(self):
        return self.name
        
    def isEnabled(self):
        return self.state != DISABLED
        
    def isActive(self):
        return (self.state == LINGERING) or (self.state == LOOKING and self.pointTarget > 0)
        
    def _restartTrigger(self):
        self.pointTarget = 0
        self.state = LOOKING
        self.lastTriggerPointTime = 0
        self.lingerTime = 0
    
    def processSculpturePosition(self, position):
        if self.state == DISABLED:
            return
        
        currentTime = time.time() 
        targetPoint = self.points[self.pointTarget]
        
        print "received position data", position
        
        if self.state == LINGERING:
            # check that we have either passed the linger timeout, or are still near the point in question
            if currentTime > self.lingerTime:
                # is there a flame effect associated?
                if "flameEffect" in self.points[self.pointTarget]: 
                    doFlameEffect(self.points[self.pointTarget]["flameEffect"])
                    log.info("Flame effect sequence {} called!".format(self.points[self.pointTarget]["flameEffect"]))
                    
                if (len(self.points) > (self.pointTarget+1)):  # go to next point in sequence
                    self.pointTarget = self.pointTarget + 1
                    self.state = LOOKING
                    self.lastTriggerPointTime = currentTime
                else: # end of trigger sequence. Back to the looking for the first point
                    self._restartTrigger()
                    return
            else:
                pass # still lingering...
                    

        elif self.state == LOOKING:
            # Check whether time has expired
            if self.pointTarget != 0 and currentTime > self.transitTime:
                self._restartTrigger()
                return
                
            # now check if we've gotten to the desired point
            if TriggerObject._inEnvelopeRadius(targetPoint, position):
                # got there. Change state...
                if targetPoint["type"] == "linger":
                    self.state == LINGERING
                    self.lingerTime = currentTime + targetPoint["lingerTime"]
                else: # passthrough case
                    if "flameEffect" in targetPoint: 
                        pass #XXX FIXME
                        #FlameEffects.doFlameEffect(targetPoint["flameEffect"])
                    self.state == LOOKING
                    self.pointTarget = self.pointTarget + 1
                    if self.pointTarget >= len(self.points):
                        self.pointTarget = 0
            
            # haven't gotten to desired point - are we in the envelope?
            elif self.pointTarget != 0:  # target 0 has no transition envelope, since there was no previous point
                prevPoint = self.points[self.pointTarget-1]
                if not TriggerObject._inEnvelopeSausage(prevPoint, targetPoint, position):
                    self.restartTrigger()
                    return
               
    
    @staticmethod
    def _inEnvelopeRadius(target, testPoint):
        distanceSquare = (target["x"] - testPoint["x"])^2 + (target["y"] - testPoint["y"])^2 + (target["z"] - testPoint["z"])^2
        return distanceSquare <= ENVELOPE_SIZE^2
        
    @staticmethod
    def _inEnvelopeSausage(targetA, targetB, testPoint):
        if _inEnvelopeRadius(targetA, testPoint):
            return True
        if TriggerObject._inEnvelopeRadius(targetB, testPoint):
            return True
            
        return _distanceToLineSegment(targetA, targetB, testPoint) <= EnvelopeSize
        
    @staticmethod
    def _distanceToLineSegment(targetA, targetB, testPoint): 
        # thanks to quano in StackExchange... XXX - check that this works. And do the math
        
        dx = targetB["x"] - targetA["x"]
        dy = targetB["y"] - targetA["y"]
        dz = targetB["z"] - targetA["z"]

        d2 = dx^2 + dy^2 + dz^2 # square of line segment length   

        u = ((testPoint["x"] - targetA["x"])*dx + (testPoint["y"] - targetA["y"])*dy + (testPoint["z"] - targetA["z"])*dz) / float(d2)
    
        # clamp u
        if u > 1:
            u = 1
        elif u < 0:
            u = 0

        x = targetA["x"] + u * dx
        y = targetA["y"] + u * dy
        z = targetA["z"] + y * dz
    
        return (x - testPoint["x"])^2 + (y - testPoint["y"])^2 + (z - testPoint["z"])^2
        
if __name__ == '__main__':  # for testing - this is part of the flame effects process!
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s', level=logging.DEBUG)
    try:            
        if len(sys.argv) > 1:
            initFile = sys.argv[1]
        else:
            initFile = "./triggers.json"
            
        init(initFile, "127.0.0.1", 9001)
        while True:
            time.sleep(4)
    except KeyboardInterrupt:
        print "Ctl-C detected"
        
    print "CALLING SHUTDOWN"
    shutdown() 
        
