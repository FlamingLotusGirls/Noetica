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
import json
import logging
import select
import socket
import sys
import time
import unittest

import flames_controller


triggerList = list()
triggerThread = None
triggerFileName = None

logger = logging.getLogger('triggers')


def init(triggerFile, addr, port):
    global triggerThread
    global triggerFileName
    logger.info("Trigger Init, trigger file {}, listening at {}:{}".format(triggerFile, addr, port))
    try:
        with open(triggerFile) as f:
            triggerParams = json.load(f)
        logger.debug("triggerparams are {}".format(triggerParams))
        triggerFileName = triggerFile
        triggerThread = TriggerManager(addr, port, triggerParams)
        triggerThread.start()
    except IOError:
        logger.exception("Exception initializing triggers!")

def shutdown():
    logger.info("Trigger Shutdown")
    global triggerThread
    if triggerThread != None:
        logger.info("...Joining trigger thread")
        triggerThread.stop()
        triggerThread.join()
    triggerThread = None

def getTriggers():
    triggers = triggerThread.getTriggers()
    newTriggers = list()
    for trigger in triggers:
        newTrigger = {"name": trigger.getName(), "enabled": trigger.isEnabled(),
                      "active": trigger.isActive(), "points":trigger.getPoints()}
        newTriggers.append(newTrigger)
    return newTriggers
    
def deleteTrigger(triggerName):
    triggerThread.deleteTrigger(triggerName)
    
def addOrModifyTrigger(trigger):
    triggerThread.addOrModifyTrigger(trigger)
    
def renameTrigger(oldName, newName):
    triggerThread.renameTrigger(oldName, newName)
    
def saveTriggers(triggerFile=None):
    print("SAVING")
    triggerThread.saveTriggers(triggerFile)


def enableTrigger(triggerName):
    logger.debug("Enabling trigger {}".format(triggerName))
    triggers = triggerThread.getTriggers()
    for trigger in triggers:
        if trigger.getName() == triggerName:
            trigger.enable(True)
            break

def disableTrigger(triggerName):
    logger.debug("Disabling trigger {}".format(triggerName))
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
        logger.exception("Malformed trigger parameter")
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

        logger.debug("trigger manager init, trigger params:".format(triggerParams))

        for triggerParamsObject in triggerParams:
            logger.debug("trigger param is {}".format(triggerParamsObject))
            if _verifyTriggerParamsObject(triggerParamsObject):
                logger.debug("trigger verifies, creating object and appending to list")
                triggerObject = TriggerObject(triggerParamsObject["name"],
                                              triggerParamsObject["points"])
                self.triggerList.append(triggerObject)
                triggerObject.enable(True)

# x = json.loads(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values())) # XXX this is a way of creating an object with attributes instead of a generic dict, but I don't quite understand how it works yet
    def getTriggers(self):
        return self.triggerList
        
    def deleteTrigger(self, triggerName):
        for trigger in self.triggerList:
            if trigger.getName() == triggerName:
                logger.debug("Removing trigger {}".format(triggerName))
                self.triggerList.remove(trigger)
                break
 
    def renameTrigger(self, oldName, newName):
        for trigger in self.triggerList:
            if trigger.getName() == oldName:   
                trigger.setName(newName)     
                
    def addOrModifyTrigger(self, trigger):
        if not _verifyTriggerParamsObject(trigger):
            logger.warning("New trigger does not validate")
            return
            
        foundTrigger = None
        for curTrigger in self.triggerList:
            if curTrigger.name == trigger["name"]:
                foundTrigger = curTrigger
                logger.debug("Modifying trigger")
                break
        
        if foundTrigger:
            enabled = foundTrigger.isEnabled()
            self.triggerList.remove(foundTrigger)
        else:
            logger.debug("Adding trigger")
            enabled = True     
        
        triggerObject = TriggerObject(trigger["name"],
                                      trigger["points"])
        self.triggerList.append(triggerObject)
        triggerObject.enable(enabled)
        
    def saveTriggers(self, filename=None):
        logger.debug("Saving triggers");
        newList = []
        for trigger in self.triggerList:
            print ("***Trigger is {}".format(trigger))
            newTrigger = {"name":trigger.name, "points":trigger.points}
            newList.append(newTrigger)
        
        if filename == None:
            filename = triggerFileName
        with open(filename, 'w') as f: # open write
            json.dump(newList, f)
    

    def run(self):
        self.running = True
        msg = ""
        while self.running:
            try:
                if not self.socketInit:
                    self._connectHydraulicsSocket(self.listenAddr, self.listenPort)
                    self.socketInit = True
                    logger.info("Connected to hydraulics socket")

                # listen for message on queue
                ready = select.select([self.hydraulics_socket], [], [], 2.0)
                if ready[0]:
                    msgFrag = self.hydraulics_socket.recv(32)
                    if len(msgFrag) <= 0:
                        logger.warn("0 bytes received on trigger thread, disconnecting")
                        #self.hydraulics_socket.shutdown(socket.SHUT_RDWR)
                        self.hydraulics_socket.close()
                        self.socketInit = False
                        continue
                else:
                    continue # XXX check for errors....

                msg = msg + str(msgFrag)
                eomIdx = msg.find("\n")
                while (eomIdx >= 0) :
                    cmd = msg[:eomIdx]
                    cmdObj = json.loads(cmd)
                    # got message, hand to objects
                    for trigger in self.triggerList:
                        trigger.processSculpturePosition(cmdObj)
                    msg = msg[eomIdx+1:]
                    eomIdx = msg.find("\n")

            except socket.error, (value, message):
                if value != 61: # connection refused, common
                    logger.exception("Socket error {}".format(message))
                else:
                    logger.info("Socket connection refused, will retry")
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
        self.recoveryTime = 5 # number of seconds after successful completion before trigger becomes active again
        self.inRecovery = False
        self.recoveryStartTime = 0
        logger.info("INIT trigger object {}".format(name))

    def enable(self, bEnable):
        if bEnable:
            self._restartTrigger()
        else:
            self.state = DISABLED

    def getName(self):
        return self.name
    
    def setName(self, newName):
        self.name = newName;
        
    def getPoints(self):
        return self.points

    def isEnabled(self):
        return self.state != DISABLED

    def isActive(self):
        return (not self.inRecovery) and ((self.state == LINGERING) or (self.state == LOOKING and self.pointTarget > 0))

    def _restartTrigger(self, bRecover = False):
        self.pointTarget = 0
        self.state = LOOKING
        self.lastTriggerPointTime = 0
        self.lingerTime = 0
        if bRecover:
            self.inRecovery = True
            self.recoveryStartTime = time.time()

    def processSculpturePosition(self, position):
#        print "Received position, ", position
#        print "State is ", self.state
        if self.state == DISABLED:
            return

        currentTime = time.time()
        if self.inRecovery and currentTime > self.recoveryStartTime + self.recoveryTime:
            self.inRecovery = False
        else: 
            return # we're in the recovery period. Bail.
            
        targetPoint = self.points[self.pointTarget]

        if self.state == LINGERING:
            # check that we have either passed the linger timeout, or are still near the point in question
            if currentTime > self.lingerTime:
                # is there a flame effect associated?
                if "flameEffect" in self.points[self.pointTarget]:
                    flames_controller.doFlameEffect(self.points[self.pointTarget]["flameEffect"])
                    logger.info("Flame effect sequence {} called!".format(self.points[self.pointTarget]["flameEffect"]))

                if (len(self.points) > (self.pointTarget+1)):  # go to next point in sequence
                    logger.debug("Trigger {} going to next point ({})".format(self.name, self.pointTarget+1))
                    self.pointTarget = self.pointTarget + 1
                    self.state = LOOKING
                    self.lastTriggerPointTime = currentTime
                else: # end of trigger sequence. Back to the looking for the first point
                    logger.debug("End of trigger {}".format(self.name))
                    self._restartTrigger(True)
                    return
            else:
                pass # still lingering...


        elif self.state == LOOKING:
            # Check whether time has expired
            if self.pointTarget != 0 and (currentTime > (self.lastTriggerPointTime + targetPoint["transitTime"])):
                logger.debug("Restarting trigger {}".format(self.name))
                self._restartTrigger()
                return

            # now check if we've gotten to the desired point
            if TriggerObject._inEnvelopeRadius(targetPoint, position):
                # got there. Change state...
                if targetPoint["type"] == "linger":
                    logger.debug("Trigger {} got to point ({}). Will linger".format(self.name, self.pointTarget))
                    self.state = LINGERING
                    self.lingerTime = currentTime + targetPoint["lingerTime"]
                else: # passthrough case
                    if "flameEffect" in targetPoint:
                        logger.info("Trigger {} calling for flame effect {}".format(self.name, targetPoint["flameEffect"]))
                        flames_controller.doFlameEffect(targetPoint["flameEffect"])
                    self.state = LOOKING
                    self.pointTarget = self.pointTarget + 1
                    if self.pointTarget >= len(self.points):
                        self.pointTarget = 0

            # haven't gotten to desired point - are we in the envelope?
            elif self.pointTarget != 0:  # target 0 has no transition envelope, since there was no previous point
                prevPoint = self.points[self.pointTarget-1]
                if not TriggerObject._inEnvelopeSausage(prevPoint, targetPoint, position):
                    self._restartTrigger()
                    return


    @staticmethod
    def _inEnvelopeRadius(target, testPoint):
        distanceSquare = (target["x"] - testPoint["x"])**2 + (target["y"] - testPoint["y"])**2 + (target["z"] - testPoint["z"])**2
        return distanceSquare <= ENVELOPE_SIZE**2

    @staticmethod
    def _inEnvelopeSausage(targetA, targetB, testPoint):
        if TriggerObject._inEnvelopeRadius(targetA, testPoint):
            return True
        if TriggerObject._inEnvelopeRadius(targetB, testPoint):
            return True

        return TriggerObject._distanceToLineSegment(targetA, targetB, testPoint) <= ENVELOPE_SIZE**2

    @staticmethod
    def _distanceToLineSegment(targetA, targetB, testPoint):

        dx = targetB["x"] - targetA["x"]
        dy = targetB["y"] - targetA["y"]
        dz = targetB["z"] - targetA["z"]

        d2 = dx**2 + dy**2 + dz**2 # square of line segment length

        # u is projection of testpoint's fraction of way along the line segment
        u = ((testPoint["x"] - targetA["x"])*dx + (testPoint["y"] - targetA["y"])*dy + (testPoint["z"] - targetA["z"])*dz) / float(d2)

        # clamp u - because we want an answer inside the line segment.
        if u > 1:
            u = 1
        elif u < 0:
            u = 0

        x = targetA["x"] + u * dx
        y = targetA["y"] + u * dy
        z = targetA["z"] + u * dz

        return (x - testPoint["x"])**2 + (y - testPoint["y"])**2 + (z - testPoint["z"])**2

theTriggerTest = None
def triggerTestEventListenerWrapper(msg):
    print ("EVENT HANDLER CALLED")
    theTriggerTest.eventListener(msg)

class TriggerTests(unittest.TestCase):
    def setUp(self):
        global theTriggerTest
        theTriggerTest = self
        self.sequenceDesired = None
        self.triggered = False

    def tearDown(self):
        hydraulics.hydraulics_playback.shutdown()
        hydraulics.hydraulics_drv.shutdown()
        hydraulics.hydraulics_stream.shutdown()
        hydraulics.event_manager.shutdown()

        shutdown()
        flames_controller.shutdown()
        event_manager.shutdown()
        flames_drv.shutdown()
        pattern_manager.shutdown()

    def initTest(self, triggerFile, playbackDirectory, playbackName, sequenceFile, pollInterval=1000):
        # start up the hydraulics sytem
        hydraulics.event_manager.init()
        hydraulics.hydraulics_stream.init(5001)
        hydraulics.hydraulics_drv.init(pollInterval, hydraulics.hydraulics_drv.TEST)
        hydraulics.hydraulics_playback.init(playbackDirectory, playbackName)

        # start up the flame system
        pattern_manager.init(sequenceFile)
        pooferCommandQueue = Queue.Queue()
        flames_drv.init(pooferCommandQueue)
        event_manager.init()
        flames_controller.init(pooferCommandQueue)
        init(triggerFile, "localhost", 5001)
        event_manager.addListener(triggerTestEventListenerWrapper, "sequence_start")

    def setSequenceToListenFor(self, sequenceName):
        self.sequenceDesired = sequenceName

    def eventListener(self, msg):
        logger.info("Received event, {}".format(msg))
        if (msg["msgType"] == "sequence_start" and
            msg["id"] == self.sequenceDesired):
            self.triggered = True

    def test_SingleLinger(self):
        print ("SINGLE LINGER TEST!!!")
        self.initTest("./trigger_tests/single_linger_trigger.json",
                 "../Hydraulics/playback_tests",
                 "linger_test","test_sequences.json")
        self.setSequenceToListenFor("Top")
        time.sleep(10)
        self.assertTrue(self.triggered)

    def test_PointToPoint(self):
        print ("POINT TO POINT TEST!!!")
        self.initTest("./trigger_tests/point_to_point_trigger.json",
                 "../Hydraulics/playback_tests",
                 "point_to_point_test","test_sequences.json")
        self.setSequenceToListenFor("Bottom")
        time.sleep(13)
        self.assertTrue(self.triggered)

    def test_PassthroughPoint(self):
        print ("PASSTHROUGH TEST!!!")
        self.initTest("./trigger_tests/passthrough_trigger.json",
                 "../Hydraulics/playback_tests",
                 "passthrough_test","test_sequences.json")
        self.setSequenceToListenFor("Top")
        time.sleep(13)
        self.assertTrue(self.triggered)
#
#     def test_SingleLingerNeverHitPoint(self):
#         self.initTest("./trigger_tests/single_linger_trigger.json",
#                  "../Hydraulics/playback_tests",
#                  "linger_test_no_go","test_sequences.json")
#         self.setSequenceToListenFor("Top")
#         time.sleep(10)
#         self.assertFalse(self.triggered)
#
#     def test_SingleLingerTooShortLinger(self):
#         self.initTest("./trigger_tests/single_linger_trigger.json",
#                  "../Hydraulics/playback_tests",
#                  "linger_test_too_short","test_sequences.json")
#         self.setSequenceToListenFor("Top")
#         time.sleep(10)
#         self.assertFalse(self.triggered)
#
#     def test_PointToPointTooSlow(self):
#         self.initTest("./trigger_tests/point_to_point_trigger.json",
#                  "../Hydraulics/playback_tests",
#                  "point_to_point_too_slow","test_sequences.json")
#         self.setSequenceToListenFor("Bottom")
#         time.sleep(10)
#         assertFalse(self.triggered)
#
#     def test_PointToPointOutsideLines(self):
#         self.initTest("./trigger_tests/point_to_point_trigger.json",
#                  "../Hydraulics/playback_tests",
#                  "point_to_point_outside_lines","test_sequences.json")
#         self.setSequenceToListenFor("Bottom")
#         time.sleep(10)
#         self.assertFalse(self.triggered)



if __name__ == '__main__':
    import sys
    import Queue
    sys.path.append('../Hydraulics') # XXX could create a NOETICA_HOME environment variable
    import hydraulics
    import event_manager
    import pattern_manager
    import flames_drv
    import flames_controller

    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d: %(message)s', level=logging.DEBUG)

    unittest.main()
