''' Trigger manager, and trigger objects '''
from threading import Thread

#from flameEffects import FlameEffects
import json
import logging
import time

triggerList = list()

logger = logging.getLogger('triggers')

def init(triggerFile = "./triggers.json", addr, port):
    try:
        with open(triggerFile) as f:
            triggerParams = json.load(f) 
        triggerThread = TriggerManager(triggerParams, addr, port)
        triggerThread.start()
    except:
        logger.exception("Exception initializing triggers!")
        
def _verifyTriggerParamsObject(triggerParamsObject):
    # XXX - I'm doing a lot of assignments here, but the point isn't to assign variables,
    # its to test that the structure of the object is correct. There are probably better
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

        for triggerParamsObject in triggerParams:
            if _verifyTriggerParamsObject(triggerParamsObject):
                self.triggerList.append(TriggerObject(triggerParamsObject["name"], 
                                                      triggerParamsObject["points"]))
                              
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
                    self.hydraulics_socket.shutdown()
                    self.hydraulics_socket.close()
                    self.socketInit = False
                    continue
                    
                msgObj = json.loads(msg) # XXX and what happens on exception here?            
                
                # got message, hand to objects
                for trigger in self.triggerList:
                    trigger.processSculpturePosition(msgObj)
            except socket.error, (value, message):
                logger.exception("Socket error {}".format(message))
                # Attempt reconnect
                self.socketInit = False
                if self.hydraulics_socket != None:
                    self.hydraulics_socket.shutdown(socket.SHUT_RDWR)
                    self.hydraulics_socket.close()
                    self.hydraulics_socket = None
                time.sleep(0.5)
            except:
                logger.exception("Error processing hydraulics position data")
                
    def stop(self):
        self.running = False
                
    def _connectHydraulicsSocket(self):
        self.hydraulics_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.hydraulics_socket.connect((addr, port))
        # NB - these calls are expected to throw if there is a problem


            

# states are
DISABLED = "disabled"
LINGERING = "lingering"
LOOKING = "looking"



ENVELOPE_SIZE = 5

# XXX let's not bother with direction down the envelope right now. Just keep us in the envelope

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
        
    def _restartTrigger(self):
        self.pointTarget = 0
        self.state = LOOKING
        self.lastTriggerPointTime = 0
        self.lingerTime = 0
    
    def processSculpturePosition(self, position):
        if self.state == DISABLED:
            return
        
        currentTime = time.now() # or something
        targetPoint = self.points[self.pointTarget]
        
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
            if _inEnvelopeRadius(targetPoint, position):
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
                if not _inEnvelopeSausage(prevPoint, targetPoint, position):
                    self.restartTrigger()
                    return
               
    
    def _inEnvelopeRadius(target, testPoint):
        distanceSquare = (target["x"] - testPoint["x"])^2 + (target["y"] - testPoint["y"])^2 + (target["z"] - testPoint["z"])^2
        return distanceSquare <= ENVELOPE_SIZE^2
        
    def _inEnvelopeSausage(targetA, targetB, testPoint):
        if _inEnvelopeRadius(targetA, testPoint):
            return True
        if _inEnvelopeRadius(targetB, testPoint):
            return True
            
        return _distanceToLineSegment(targetA, targetB, testPoint) <= EnvelopeSize
        

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


        
            
        
