#!/usr/bin/python
########## Overview
#
# This file is designed to translate a firing sequence to ! (bang) code and send it to the poofer controller boards.
# 
# It expects to be passed to it the following data structures:
#	pooferMappings 	- an object containing the poofer control board address (board number and channel) of each poofer (see notes below for its expected format)
# 	disabledPoofers - list of poofers that are currently disabled
# 	firingSequence 	- list of poofer firing sequence events (see notes below for its expected format)
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
# firingSequence is a string list of the form:
# {ABxxxx&ABxxxx,RRxxxx,ABxxxx,etc}
#
# where: 
#	A is the position of the poofer, which can be T, B, N, S, E, W
# 	B is the position of the poofer on its plink, it can be T, B, N, S, E, W
# 	RR indicates that there should be a rest for time xxxxx
# 	xxxx is the time duration of the firing, in milliseconds (max value is 3500, as defined by poofer control board firmware)
# 	& separates firing events that should happen in parallel
# 	, separates firing events that should happen in sequence 
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

import sys					# system functions
import traceback			# exceptions and tracebacks
import time					# system time
import re 					# regex
from threading import Thread
import Queue
import json
import logging
from poofermapping import mappings as pooferMapping

logger = logging.getLogger("flames_drv")

### PARAMETERS - DO NOT CHANGE ###
#these parameters may need to be tweaked during early testing
minPooferCycleTime					= 50 			#milliseconds, this is the poofer off-to-on-to-off cycle time, dictated by the switching speed of the DMI-SH-112L relay on the poofer controller board
maxFiringSequenceSteps 				= 50			#some upper limit to firing sequence, for sanity checks
minFiringRestTime					= 100			#milliseconds, this is the minimum time we want between two sequential poofer firing steps
maxNonfiringRestTime				= 9999 			#milliseconds, dictates the maximum time for a firing sequence rest event
maxCommandsInAFiringSequence		= 50 			#integer, needs to be tested

#regex filter, precompiled for efficiency
validFiringSequenceEvents			= re.compile('(^(RR|NN|NW|NE|NT|EN|EE|ES|ET|SE|SS|SW|ST|WS|WW|WN|WT|TN|TE|TS|TW|TT|BN|BE|BS|BW)[0-9][0-9][0-9][0-9]$)')


### VARIABLES ###
#expected list of poofer controller boards



##########debug 
'''
firingSequence=[NN0100&NS0100,TT0500,TS4000,RR0100,TT0100]
print("firingSequence profile:")
eventCount=0
print("firing steps=",len(firingSequence))
for step in firingSequence:
	print(step)
	if "&" in step:
		print("step with parallel events:")
		parallelEvents=step.split("&")
		for event in parallelEvents:
			print(event)
			eventCount=eventCount+1
	else:
		eventCount=eventCount+1
print("firing events=",eventCount)
print("==========================================================")
'''

'''
##########


### MAIN SEQUENCE ###

try: 
	#initialize GPIO
	#init()

	#sanity checks on firingSequence
	checkSequence(firingSequence)

	#parse firingSequence into bangCommandList
	#generateBangCommandList(firingSequence)

	#bang bang bang!
	#firePoofers(bangCommandList)

	#done!
	return(0)
	
except Exception as e:
	print ("Exception, exiting...", e)
	return(1)
'''

pooferFiringThread = None
sequenceFile       = None

def init(cmdQueue, sequenceFileName):
    global pooferFiringThread
    global sequenceFile
    sequenceFile = sequenceFileName
    pooferFiringThread = PooferFiringThread(cmdQueue)
    pooferFiringThread.start()
    
def shutdown():
    global pooferFiringThread
    if pooferFiringThread != None:
        pooferFiringThread.shutdown()
        pooferFiringThread = None
    
class PooferFiringThread(Thread):
    TIMEOUT = 1 # 1 second timeout, even if no events
    
    def __init__(self, cmdQueue):
        Thread.__init__(self)
        self.cmdQueue = cmdQueue
        self.running = False
        self.pooferEvents = list() # time-ordered list of poofer events
        
    def shutdown(self):
        self.running = False
    
    def run(self):
        self.running = True
        while(self.running):
            if len(self.pooferEvents) > 0: # there are poofer events
                currentTime - time.time()
                # pop events off of the list. If the current time is greater than
                # the time associated with the event, set up for serial       
            if len(self.pooferEvents) > 0: # there are poofer events in the future
                waitTime = self.events[0]["time"] - time.time()
            else:
                waitTime = PooferFiringThread.TIMEOUT
            
            try:
                cmd = cmdQueue.get(True, waitTime)
                # parse message. If this is a request to do a flame sequence,
                # set up poofer events, ordered by time. Event["time"] attribute
                # should be current time (time.time()) plus the relative time from
                # the start of the sequence
                msgObj = json.loads(cmd)
                type = msgObj["type"]
                if type == "flameEffectStart" and checkSequence(msgObj):
                    # figure out firing sequence associated with the name, set
                    # up poofer events
                    pass
                # else - whatever other type of event you want to process ...
            except Queue.Empty:
                # this is just a timeout - completely expected. Run the loop
                pass
            except Exception:
                # log this... Not expected!
                pass
                
                
                
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
                    if checkEvent(event) != event: 
                        #raise Exception as e:
                        print("Error: firingSequence is malformed.")
                        return False
            return True

        except Exception as e:
            print("Error: firingSequence is malformed or out of bounds", e)
            traceback.print_exc(file=sys.stdout)
            return False 


    ## parse out firing sequence into bang code ##
    def generateBangCommandList(self, firingSequence):

        try:
    
            #steps: 
            #check to see if electronic killswitch is enabled, if so then do nothing
            #iterating through firingSequence, for each step:
            #	generate eventsList
            #	for each in eventsList:
            #		each item becomes a new item in bangCommandList:
            #		bangCommandList[index]="b"+(string: translate alphas to address via pooferMappings)+"t"+str(digits)
            #		make sure that there is a 1:1 match between each step in firingSequence and each step in bangCommandList
        
            #translate firingSequence into bang code
            for step in firingSequence:
                #divide parallel firings into single events
                parallelEvents=step.split("&")
                #write the events into a sequence of bang commands
                

                            
                            
            
                    #bangCommandList=
                #
            
            
            
            #else:
                #end the poof string with the "end" command.
                #bangCommandList= + "."
            

        except Exception as e:
            print("Error while sending bang code: ", e)
            traceback.print_exc(file=sys.stdout)
            return(1)
            
        return(bangCommandList)



    ## send bangCommandList to the poofer controller boards
    def firePoofers(self, bangCommandList):

        try:
            #steps:
            #check to see if electronic killswitch is enabled, if so then do nothing
            #create a separate thread? or have the parent script fire this entire script off in a separate thread?
            #start an event timer? or use thread sleeps to keep track of time?
            #according to bangCommandList time schedule, carry out for each firing event: 
            #	check if electronic killswitch is engaged, if so then exit
            #	send bang commands to the poofer control boards
            #	broadcast a firing event through the REST API
            #	check if electronic killswitch is engaged, if so then exit
            pass
        
        
        except Exception as e:
            print("Error sending bangCommandSequence to poofer controller boards", e)
            traceback.print_exc(file=sys.stdout)
            
            


		
	
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



