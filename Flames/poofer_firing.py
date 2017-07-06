 


# This file is designed to assemble and send the commands to the poofer controller boards.
# The bang protocol used for comms to communicate with poofer controller board.
# Bang protocol defined here: http://flg.waywardengineer.com/index.php?title=Bang_(!)_Protocol

## variables (changeable) ##


### parameters - do not change ###
#determined by the switching speed of the DMI-SH-112L relay on the poofer controller board
timeMinimumFiringDuration=20 #milliseconds
timeMinPooferOnOffSwitchCycle=50 #milliseconds



## proof of concept: fire a single poofer ##

#debugging
boardID="01"
boardChannel="1"
print boardID
print boardChannel

# write packet command
poofString="!"

# controller board ID
poofString=poofString + boardID

# controller board channel
poofString=poofString + boardChannel

# on command
poofString=poofString + "1"

# command termiantor
poofString=poofString + "."

print poofString

## create bang code for a single channel ##




## create a sequence of bang commands ##



## write sequence of bang commands ##
##we need to figure out what the upper limits are for firing off commands
##(minimum firing duration) 









