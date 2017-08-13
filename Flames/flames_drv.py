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
That's an eve self.pooferMapping as easily human understandable, but it works
'''

import os
import sys                    # system functions
import traceback            # exceptions and tracebacks
import time                    # system time
import re                     # regex
from threading import Thread
import Queue
import json
import logging
import event_manager
import pattern_manager
from collections import defaultdict
import serial
from operator import itemgetter

logging.basicConfig()
logger = logging.getLogger("flames_drv")
POOFER_MAPPINGS_FILE = "./poofer_mappings.json"

### PARAMETERS - DO NOT CHANGE ###
#these parameters may need to be tweaked during early testing
minPooferCycleTime                  = 50             #milliseconds, this is the poofer off-to-on-to-off cycle time, dictated by the switching speed of the DMI-SH-112L relay on the poofer controller board
maxFiringSequenceSteps              = 50            #some upper limit to firing sequence, for sanity checks
minFiringRestTime                   = 100            #milliseconds, this is the minimum time we want between two sequential poofer firing steps
maxNonfiringRestTime                = 9999             #milliseconds, dictates the maximum time for a firing sequence rest event
maxCommandsInAFiringSequence        = 50             #integer, needs to be tested
BAUDRATE                            = 19200
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

class PooferFiringThread(Thread): # comment out for unit testing
# class PooferFiringThread():
    TIMEOUT = 1 # 1 second timeout, even if no events

    def __init__(self, cmdQueue, pooferMappingPath='poofer_mappings.json'):
        Thread.__init__(self) # comment out for unit testing
        logger.info("Init Poofer Firing Thread")
        self.cmdQueue = cmdQueue
        self.running = False
        self.isFiringDisabled = False
        self.pooferEvents = list() # time-ordered list of poofer events
        self.disabled_poofers = set()
        self.ser = self.initSerial()
        with open(pooferMappingPath) as data_file:
            self.pooferMapping = json.load(data_file)
        self.disableAllPoofersCommand = self.generateDisableAllString()


    def shutdown(self):
        self.running = False

    def initSerial(self):
        ser = serial.Serial()
        ser.baudrate = BAUDRATE
        port = False
        for filename in os.listdir("/dev"):
            if filename.startswith("tty.usbserial"):  # this is the ftdi usb cable on the Mac
                port = "/dev/" + filename
                logger.info("Found usb serial at " + port)
                break;
            elif filename.startswith("ttyUSB0"):      # this is the ftdi usb cable on the Pi (Linux Debian)
                port = "/dev/" + filename
                logger.info("Found usb serial at " + port)
                break;

        if not port:
            logger.exception("No usb serial connected")
            return None

        ser.port = port
        ser.timeout = 0
        ser.stopbits = serial.STOPBITS_ONE
        ser.bytesize = 8
        ser.parity   = serial.PARITY_NONE
        ser.rtscts   = 0
        ser.open() # if serial open fails... XXX
        return ser

    def generateDisableAllString(self):
        self.disableAllPoofersCommand = ""
        controllerDict = defaultdict(list)
        for attribute, value in self.pooferMapping.iteritems():
            # print attribute, value
            controllerDict[value[:2]].append(value[2])

        for i in controllerDict.keys():
            self.disableAllPoofersCommand += "!" + i + "~".join(map(lambda x: x+"0", controllerDict[i])) + "."

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

                elif not self.isFiringDisabled:
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

    def checkSequence(self, firingSequence):
        try:
            events = firingSequence["events"]

            if len(events) > maxFiringSequenceSteps:
                raise Exception ("Error: maxFiringSequenceSteps < len(firingSequence) = ", len(firingSequence))

            totalDuration = 0
            for e in events:
                totalDuration += e["duration"]
            if totalDuration > 60000:
                raise Exception ("Error: duration", len(firingSequence))

            return True

        except Exception as e:
            logger.exception("firingSequence is malformed or out of bounds" + str(e))
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
                print command

        except Exception as e:
            ser.close()
            ser = None
            logger.exception("Error sending bangCommandSequence to poofer controller boards: %s", str(e))

    def disablePoofer(self, msgObj):
        self.disabled_poofers.add(msgObj["name"])
        event_manager.postEvent({"msgType":"poofer_disabled", "id":msgObj["name"]})

    def enablePoofer(self, msgObj):
        try:
            self.disabled_poofers.remove(msgObj["name"])
            event_manager.postEvent({"msgType":"poofer_enabled", "id":msgObj["name"]})
        except KeyError as e:
            pass

    def resumeAll(self):
        self.isFiringDisabled = False
        event_manager.postEvent({"msgType":"global_resume", "id":"all?"})

    def stopAll(self):
        try:
            if not ser:
                ser.initSerial()
            if disableAllPoofersCommand == "":
                self.generateDisableAllString()
            ser.write(disableAllPoofersCommand.encode())

            self.isFiringDisabled = True
            self.pooferEvents = list() # reset all pooferEvents
            event_manager.postEvent({"msgType":"global_pause", "id":"all?"})

        except Exception as e:
            logger.exception("Error stopping all poofers: %s", str(e))


    def startFlameEffect(self, msgObj):
        try:
            sequenceName = msgObj["name"]
            sequence = pattern_manager.getPattern(sequenceName)
            if self.checkSequence(sequence):
                self.setUpEvent(sequence)
                event_manager.postEvent({"msgType":"sequence_start", "id":msgObj["name"]})

        except Exception as e:
            logger.exception("Failed to fetch or set up sequence.%s", str(e))

    def stopFlameEffect(self, msgObj):
        event_manager.postEvent({"msgType":"sequence_stop", "id":msgObj["name"]})
        filter(lambda p: p.sequence != msgObj["name"], self.pooferEvents)

    def setUpEvent(self, sequence):
        # Takes a sequence object, and add to self.pooferEvents the bang commands
        # to turn on and to turn off the specified poofers.
        # The obect added to self.pooferEvents is of format:
        # # { "sequence":"sequenceName", "time":"1502068215.5",
        # "bangCommandList":["!0011~21.", "!0021~21."] }

        sequenceName = sequence["name"]

        events = sequence["events"]
        firstFiringTime = time.time()

        if not self.isFiringDisabled:
            for event in events:
                ids = event["ids"]
                startTime = firstFiringTime + event["startTime"]
                endTime = startTime + event["duration"]

                addresses = [self.pooferMapping[a] for a in ids].sort()
                bangCommandList = self.makeBangCommandList(addresses)

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
                self.pooferEvents.sort(key=itemgetter("time"))

    def makeBangCommandList(self, addresses):
        # creates a dictionary with the key being a controller ID (two digits),
        # and values being all the channels for a given controller.
        # returns an object with bang commands to turn poofers both on and off

        print "IN BANG COMMAND LIST MAKER"
        print addresses


        onBangCommands = []
        offBangCommands = []

        try:
            controllerDict = defaultdict(list)
            for controllerId in addresses:
                controllerDict[controllerId[:2]].append(controllerId[2])

            print "controllerDict = ", controllerDict

            for i in controllerDict.keys():
                onBangCommands.append(
                    "!" + i + "~".join(map(lambda x: x+"1", controllerDict[i])) + ".")
                offBangCommands.append(
                    "!" + i + "~".join(map(lambda x: x+"0", controllerDict[i])) + ".")

        except Exception as e:
            print e
            logger.exception("Error generating bang code: %s", str(e))
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
