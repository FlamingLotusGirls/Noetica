#!/usr/bin/python

# This file is designed to translate a firing sequence to ! (bang) code and send it to the poofer controller boards.
# It expects to be passed to it the following data structures:
# systemMode - defined in file ..? ADD
# disabledPoofers - list of poofers that are currently disabled
# firingSequence (see notes below)

#structure of firingSequence
# firingSequence 
# Poofers are named by location:  which plink they're on, and then which location they're in within their plink.
# The names of the plink and poofer locations are: north, south, east, west, top, and bottom.
# Poofers can be fired in sequence or in parallel. Parallel-fired poofers will technically fire in a 
# sequence but there will be no rest time in the bang code, giving the best visual appearance possible of 
# these firing events happening in parallel. Sequentially-fired poofers will have a rest time between them 
# to give the visual appearance of a sequential event. See parameters section for this rest time.
#
# firingSequence is a string list of the form:
# {ABxxxx^ABxxxx,RRxxxx,ABxxxx,etc}
# where:
# A is the position of the poofer, which can be T, B, N, S, E, W
# B is the position of the poofer on its plink, it can be T, B, N, S, E, W
# RR indicates that there should be a rest for time xxxxx
# xxxx is the time duration of the firing, in milliseconds (max value is 3500, as defined by poofer control board firmware)
# Note that xxxx must always be a 4 digit number, so there must be leading zeros for millisecond values > 1000 
# ^ separates firing events that should happen in parallel
# , separates firing events that should happen in sequence (and therefore separates the string elements in the list)
#
# Example: 
# To define a firing sequence where poofers in the N-S axis fire rapidly (100ms poofs) in sequence from the outside in,
# with both N and S sides firing from the outside in at the same time, we would write:
# {NN0100^SS0100,NT0100^ST0100,TN0100^TS0100,TT0100}

# The bang protocol used for comms to communicate with poofer controller board.
# Bang protocol defined here: http://flg.waywardengineer.com/index.php?title=Bang_(!)_Protocol

import sys
import traceback
import time
import RPi.GPIO as GPIO


### PARAMETERS - DO NOT CHANGE ###
#determined by the switching speed of the DMI-SH-112L relay on the poofer controller board, and by early testing
#stored as 4 digit strings (with leading zeros if needed) for compatability with firingSequence time format

firingMinimumFiringDurationTime		= "0050" 	#milliseconds, needs to be tested
timeFiringEventSequentialRestTime	= "0250" 	#milliseconds, needs to be tested
bangMaximumCommandsInASequence		= 10 		#integer, needs to be tested


### VARIABLES ###
#expected list of poofer controller boards



### MAIN SEQUENCE ###

#initialize GPIO
init()

#sanity checks on firingSequence
checkSequence(firingSequence)

#convert firingSequence to bangCommandSequence
generateBangCommandSequence(firingSequence)

#send bang commands to poofer controller boards


### FUNCTIONS ###

def init():
	GPIO.setmode(GPIO.BCM) 	#use RPi GPIO numbers
	GPIO.setwarnings(False) #disable warnings
	#ADD: take inventory of connected poofer controller boards and store in connectedPooferBoards
	#ADD: construct a list of missing poofer controller boards in missingPooferBoards
	#print(x, " poofer controller boards are connected")


## sanity and limit checks on firingSequence ##
def checkSequence(firingSequence):
		
	try:
		#count the number of actions in the sequence
                # (counts each parallel and sequential event)

                #count the number of steps in the sequence
                # (counts sequential steps only -- each group of parallel events is 1 step)
                for step in firingSequence:


		#make sure that all the 			
			
		return(0)


	except Exception as e:
		print("Error: firingSequence is malformed or out of bounds", e)
		traceback.print_exc(file=sys.stdout)
		return(1)


## parse out firing sequence into bang code ##
def generateBangCommandSequence(firingSequence):

	try:
		#translate firingSequence into bang code
		for step in firingSequence:
			#divide parallel firings into single events
			
			#write the events into a sequence of bang commands
				#if the current event is routed to a disabled poofer, replace it with a rest to maintain the sequence timeline
				try:
					for i in disabledPoofers:
						try: 
							event=disabledPoofers.index(i)
						except ValueError: #if it's not in the list

						else: # if it is in the list
							#replace event with a rest
							
							
			
				bangCommandSequence=
			#
			
			
			
		else:
			#end the poof string with the "end" command.
			bangCommandSequence= + "."

	except Exception as e:
		print("Error while sending bang code: ", e)
		traceback.print_exc(file=sys.stdout)
return(bangCommandSequence)



## send bangCommandSequence to the poofer controller boards
def fireBangCommandSequence(bangCommandSequence)

	try:
		
		
		
	except Exception as e:
		print("Error sending bangCommandSequence to poofer controller boards", e)
		traceback.print_exc(file=sys.stdout)

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

# send command to poofer control board

