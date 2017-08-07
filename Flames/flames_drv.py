#!/usr/bin/python
########## Overview
#
# This file is designed to translate a firing sequence to ! (bang) code and send it to the poofer controller boards.
#
# It expects to be passed to it the following data structures:
#    pooferMappings     - an object containing the poofer control board address (board number and channel) of each poofer (see notes below for its expected format)
#     disabledPoofers - list of poofers that are currently disabled
#     firingSequence     - list of poofer firing sequence events (see notes below for its expected format)
#
# If it fails to correctly carry out the events in firingSequence, it will return 1.
# Successful firing will return 0.
#

#
########## Structure of firingSequence
# firingSequence
# Poofers are named by location:  which plink they're on, and then which location they're in within their plink.
# The names of the plink and poofer locations are: north, south, east, west, top, and bottom.
# Poofers can be fired in sequence or in parallel. Parallel-fired poofers will technically fire in a
# sequence but there will be no rest time in the bang code, giving the best visual appearance possible of
# these firing events happening in parallel. Sequentially-fired poofers will have a rest time between them
# to give the visual appearance of a sequential event. See parameters section for this rest time.

#
# Therefore each string element is a firing step, and one step can contain several poofers to be fired in parallel.
# Note that xxxx must always be a 4 digit number, so there must be leading zeros for millisecond values < 1000, i.e. 0100
#
# Example:
# To define a firing sequence where poofers in the N-S axis fire rapidly (100ms poofs) in sequence from the outside in,
# with both N and S sides firing from the outside in at the same time, we would write:
# {NN0100&SS0100,NT0100&ST0100,TN0100&TS0100,TT0100}
#
########## Bang Protocol
#
# The bang protocol defines the form of the code used to command the poofer controller boards.
# Bang protocol defined here: http://flg.waywardengineer.com/index.php?title=Bang_(!)_Protocol
#
##########
'''
poofer sequence - let's define it as:
pooferid, on time, delaytime
[{"id":"NW", duration:1000, "startTime":1200} That's an event. So a sequence is
{"name":<name>, [{"id":"NW" etc... Let's use the tool to generate these.
That's an event object. Not as easily human understandable, but it works
'''

import sys                    # system functions
import traceback            # exceptions and tracebacks
import time                    # system time
import re                     # regex
from threading import Thread
import Queue
import json
import logging
import event_manager
from poofermapping import mappings as pooferMapping
import pattern_manager
from collections import defaultdict
import serial

logger = logging.getLogger("flames_drv")
POOFER_MAPPINGS_FILE = "./poofer_mappings.json"

### PARAMETERS - DO NOT CHANGE ###
#these parameters may need to be tweaked during early testing
minPooferCycleTime                    = 50             #milliseconds, this is the poofer off-to-on-to-off cycle time, dictated by the switching speed of the DMI-SH-112L relay on the poofer controller board
maxFiringSequenceSteps                 = 50            #some upper limit to firing sequence, for sanity checks
minFiringRestTime                    = 100            #milliseconds, this is the minimum time we want between two sequential poofer firing steps
maxNonfiringRestTime                = 9999             #milliseconds, dictates the maximum time for a firing sequence rest event
maxCommandsInAFiringSequence        = 50             #integer, needs to be tested

#regex filter, precompiled for efficiency
validFiringSequenceEvents            = re.compile('(^(RR|NN|NW|NE|NT|EN|EE|ES|ET|SE|SS|SW|ST|WS|WW|WN|WT|TN|TE|TS|TW|TT|BN|BE|BS|BW)[0-9][0-9][0-9][0-9]$)')


### VARIABLES ###
#expected list of poofer controller boards




pooferFiringThread = None

def init(cmdQueue):
    global pooferFiringThread
    pooferFiringThread = PooferFiringThread(cmdQueue)
    pooferFiringThread.start()

def shutdown():
    global pooferFiringThread
    logger.info("Flame driver shutdown()")
    if pooferFiringThread != None:
        logger.info("...Joining flame driver thread")
        pooferFiringThread.shutdown()
        pooferFiringThread.join()
        pooferFiringThread = None

class PooferFiringThread(Thread):
    TIMEOUT = 1 # 1 second timeout, even if no events

    def __init__(self, cmdQueue):
        Thread.__init__(self)
        logger.info("Init Poofer Firing Thread")
        self.cmdQueue = cmdQueue
        self.running = False
        self.isStopped = False
        self.pooferEvents = list() # time-ordered list of poofer events
        self.disabled_poofers = set()
        self.ser = initSerial()

    def shutdown(self):
        self.running = False

    def initSerial():
        ser = serial.Serial()
        ser.baudrate = BAUDRATE
        port = False
        for filename in os.listdir("/dev"):
            if filename.startswith("tty.usbserial"):  # this is the ftdi usb cable on the Mac
                port = "/dev/" + filename
                print "Found usb serial at ", port
                break;
            elif filename.startswith("ttyUSB0"):      # this is the ftdi usb cable on the Pi (Linux Debian)
                port = "/dev/" + filename
                print "Found usb serial at ", port
                break;

        if not port:
            print("No usb serial connected")
            return None

        ser.port = port
        ser.timeout =0
        ser.stopbits = serial.STOPBITS_ONE
        ser.bytesize = 8
        ser.parity   = serial.PARITY_NONE
        ser.rtscts   = 0
        ser.open() # if serial open fails... XXX
        return ser

    def run(self):
        self.running = True
        while(self.running):
            if len(self.pooferEvents) > 0: # there are poofer events
                # pop events off of the list. If the current time is greater than
                # the time associated with the event, set up for serial

                currentTime - time.time()
                event = self.pooferEvents.pop(0)
                currentTime = time.time()
                if event["time"] < currentTime:
                    self.firePoofers(event["bangCommandList"])
                else:
                    self.pooferEvents.insert(0, event)

            if len(self.pooferEvents) > 0: # there are poofer events in the future
                waitTime = self.events[0]["time"] - time.time()

            else:
                waitTime = PooferFiringThread.TIMEOUT

            try:
                # TODO:
                cmd = self.cmdQueue.get(True, waitTime)
                logger.debug("Received Message on cmd queue!")
                # parse message. If this is a request to do a flame sequence,
                # set up poofer events, ordered by time. Event["time"] attribute
                # should be current time (time.time()) plus the relative time from
                # the start of the sequence
                msgObj = json.loads(cmd)
                type = msgObj["cmdType"]
                logger.debug("message is {}".format(msgObj))
                if type == "stop":
                    self.stopAll()

                elif type == "resume":
                    self.resumeAll()

                elif type == "pooferDisable":
                    # TODO: does this need to persist?
                    self.disablePoofer(msgObj)

                elif not isStopped:
                    if type == "flameEffectStop":
                        self.stopFlameEffect(msgObj)

                    elif type == "pooferEnable":
                        self.enablePoofer(msgObj)

                    elif type == "flameEffectStart":
                        self.startFlameEffect(msgObj)
                        # else - whatever other type of event you want to process ...
                    elif type == "flameEffectStop":
                        self.stopFlameEffect(msgObj)

            except Queue.Empty:
                # this is just a timeout - completely expected. Run the loop
                pass
            except Exception:
                logger.exception("Unexpected exception processing command queue!")



    ## sanity and limit checks on an event from firingSequence ##
    # CSW - suggest just returning True or False, and logging the reason, rather than
    # returning the reason as a string. The upper level code really doesn't care why
    # the call failed.
    def checkEvent(self, event):
        ##########
        #this function will return the event if it's not malformed
        # and also check to see if the timings are in the allowed ranges
        # if these checks fail, the function will return information as to why
        # if these checks pass, it returns the event

        #note: poofer names can be: NN,NW,NE,NT,EN,EE,ES,ET,SE,SS,SW,ST,WS,WW,WN,WT,TN,TE,TS,TW,TT,BN,BE,BS,BW
        # and times can be a sequence of any four numerical characters (0000 to 9999)
        ##########

        #check the form of the event to make sure that it is not malformed
        filteredEvent=re.match(validFiringSequenceEvents, event) #returns None if the firing sequence event is malformed
        #debug
        print("result=" ,result)

        #now carry out the limit checks
        if filteredEvent is not None: #the event was not malformed

            #split event string into alpha and numerical characters
            alphas=re.findall('\d*\D+', event)
            digits=re.findall('(\d+|D+)', event)

            #first, check to see if the poofer is in the disabledPoofers list
            #and if it is then replace it with a rest
            for disabledPoofer in disabledPoofers:
                if disabledPoofer == alphas:
                    event="RR"+digits
                    return(1)
                        #else: # if it is in the list
                                #replace event with a rest

            #then, if it's a rest event, make sure it's not larger than the max rest time
            if alphas == "RR":
                if int(digits) > int(maxNonFiringRestTime):
                    result = "rest time > maxNonFiringRestTime"
            else:
                #next, make sure that the poofer event time is not too short, to prevent poofer valve jamming
                if int(digits) < int(minPooferCycleTime):
                    result="event time < minPooferCycleTime, event= " + event

                else: #it has passed the checks, yay!
                    result = event

        else: #the event was malformed
            #raise Exception as e:
            print("Error: firingSequence event is malformed, event=", event)
            print("Exception code: ", e)
            result = "malformed"

        return(result)


    def checkSequence(self, firingSequence):
        #debug
        print ("starting checkSequence")
        return True # XXX need to short circuit this for now
        try:
            #exception if firingSequence does not have more steps in it than the upper limit
            if len(firingSequence) > maxFiringSequenceSteps:
                raise Exception ("Error: maxFiringSequenceSteps < len(firingSequence) = ", len(firingSequence))
                traceback.print_exc(file=sys.stdout)

            #populate eventList
            for step in firingSequence:
                #debug
                print("current step = ", step)

                if "&" in step: #this step has parallel firing events
                    #debug
                    print("found to be a parallel event step")
                    eventList=step.split("&")

                else: #this step has only one firing event
                    #debug
                    print("found to be a single event step")
                    eventList=step

                #check eventList for malformed commands
                for event in eventList:
                    if checkEvent(event) != event: # != "malformed" ?
                        #raise Exception as e:
                        print("Error: firingSequence is malformed.")
                        return False
            return True

        except Exception as e:
            print("Error: firingSequence is malformed or out of bounds", e)
            traceback.print_exc(file=sys.stdout)
            return False

    ## send bangCommandList to the poofer controller boards
    def firePoofers(self, bangCommandList):
        #TODO: This was just grabbed from heartbeat_controller. Need to
        # make sure this is what we want
        try:
            if not self.isRunning:
                return 1

            if not ser:
                ser = initSerial()

            for command in bangCommandList:
                ser.write(command.encode())

        except Exception as e:
            ser.close()
            ser = None
            print("Error sending bangCommandSequence to poofer controller boards", e)
            traceback.print_exc(file=sys.stdout)

    def disablePoofer(msgObj):
        self.disabled_poofers.add(msgObj["name"])
        event_manager.postEvent({"msgType":"poofer_disabled", "id":msgObj["name"]})

    def enablePoofer(msgObj):
        enabled_poofer = self.disabled_poofers.pop(msgObj["name"])
        if enabled_poofer != None:
            event_manager.postEvent({"msgType":"poofer_enabled", "id":msgObj["name"]})

    def resumeAll():
        self.isStopped = False
        event_manager.postEvent({"msgType":"global_resume", "id":"all?"})

    def stopAll():
        self.isStopped = True
        # TODO: send bang command to stop all poofers
        self.pooferEvents = list() # reset all pooferEvents
        event_manager.postEvent({"msgType":"global_pause", "id":"all?"})

    def startFlameEffect(msgObj):
        if self.checkSequence(msgObj):
            setUpEvent(msgObj)
            event_manager.postEvent({"msgType":"sequence_start", "id":msgObj["name"]})

    def stopFlameEffect(msgObj):
        #  TODO: Need to figure out how to stop this,
        # since now this is also removing commands to stop poofers
        event_manager.postEvent({"msgType":"sequence_stop", "id":msgObj["name"]})
        filter(lambda p: p.sequence != msgObj["name"], pooferEvents)

    def setUpEvent(msgObj):
        # Takes a sequence object, and add to self.pooferEvents the bang commands
        # to turn on and to turn off the specified poofers.
        # The obect added to self.pooferEvents is of format:
        # # { "sequence":"sequenceName", "time":"1502068215.5",
        # "bangCommandList":["!0011~21.", "!0021~21."] }

        sequenceName = msgObj["name"]
        sequence = self.pattern_manager.getPattern(sequenceName)

        duration = sequence["duration"]
        events = sequence["events"]
        firstFiringTime = time.time()

        if not self.isStopped:
            for event in events:
                ids = events["ids"]
                startTime = firstFiringTime + event["startTime"]
                endTime = startTime + event["duration"]

                addresses = [pooferMapping[a] for a in ids].sort()
                bangCommandList = makeBangCommandList(addresses)

                pooferEvent = {}
                pooferEvent["sequence"] = sequenceName
                pooferEvent["time"] = startTime
                pooferEvent["bangCommandList"] = bangCommandList["on"]

                endPooferEvent = {}
                endPooferEventendPooferEvent["sequence"] = sequenceName
                endPooferEvent["time"] = endTime
                endPooferEvent["bangCommandList"] = bangCommandList["off"]

                # TODO: need to figure out best way to sort this thing
                self.pooferEvents.append(pooferEvent)
                self.pooferEvents.append(endPooferEvent)

    def makeBangCommandList(addresses):
        # creates a dictionary with the key being a controller ID (two digits),
        # and values being all the channels for a given controller.
        # returns an object with bang commands to turn poofers both on and off

        onBangCommands = []
        offBangCommands = []

        try:
            controllerDict = defaultdict(list)
            for controllerId in address: controllerDict[controllerId[:2]].append(controllerId[2])

            for i in controllerDict.keys():
                onBangCommands.append(
                    "!" + i + "~".join(map(lambda x: x+"1", controllerDict[i])) + ".")
                offBangCommands.append(
                    "!" + i + "~".join(map(lambda x: x+"0", controllerDict[i])) + ".")

        except Exception as e:
            print("Error generating bang code: ", e)
            traceback.print_exc(file=sys.stdout)
            return(1)

        return {"on":onBangCommands, "off":offBangCommands}





'''
## proof of concept: fire a single poofer ##

def singlePooferProofOfConcept():

#debugging
boardID="01"
boardChannel="1"
print boardID
print boardChannel

#command components: write, boardID, boardChannel, on
bangString="!"+ boardID + boardChannel + "1"
# command terminator
bangString=poofString + "."

print bangString
'''
