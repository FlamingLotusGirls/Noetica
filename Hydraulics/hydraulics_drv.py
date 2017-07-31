#!/usr/bin/python

# Based on sample code provided by WidgetLords for their raspberry pi 4-20mA analog 
# read/write boards. Use SPI interface for communication ("Pi-SPI")
try:
    import RPi.GPIO as GPIO
except:
    from stubs import GPIO 

try:
    import spidev
except:
    from stubs import spidev

import json
import sys
from threading import Thread, Lock
import time
import traceback
import logging

import hydraulics_playback
#import hydraulics_stream
import event_manager

adc = [0,0,0,0,0,0,0,0]
mA  = [0,0,0,0,0,0,0,0]
VDC = [0,0,0,0,0,0,0,0]

mASpan     = 2000       # mA Full Scale = 20.00 mA
VDCSpan    = 660        # VDC Full Scale = 6.6 VDC
Scaler     = 100        # Scaler factor - all reading are * 100
mASpanAdc  = 3723       # AD Counts to equal 20 mA
VDCSpanAdc = 4095       # AD Counts to equal 6.6 VDC


PASSTHROUGH = 0   # send inputs on to outputs
ATTRACT     = 1   # send preset recording to outputs
NO_MOVE     = 2   # just read inputs. Do not attempt to write to outputs
LOOPBACK    = 3   # send test output to input
TEST        = 4   # Internal test. Stream recorded data out to flame system

test_output_x = 0  
test_output_y = 0
test_output_z = 0

ioThread = None

poll_interval = 1
logger = logging.getLogger('hydraulics')

def init(interval = 1000, mode=PASSTHROUGH):
    logger.info("Hydraulics driver init, interval {}, mode {}".format(interval, mode))
    global ioThread
    global poll_interval
    poll_interval = float(interval)/float(1000)
    spi = None
    spi = spidev.SpiDev()   # spidev normally installed with RPi 3 distro's
                            # Make Sure SPI is enabled in RPi preferences
                            

    GPIO.setmode(GPIO.BCM)  # Use RPi GPIO numbers
    GPIO.setwarnings(False) # disable warnings

    ioThread = four_20mA_IO_Thread(spi, mode)
    ioThread.start()
    
def shutdown():
    print("Stopping driver thread")
    if ioThread:
        ioThread.stop()
   
def setTestOutputs(x, y, z):
    test_output_x = x
    test_output_y = y
    test_output_z = z
    
def attractModeEnable(tf):
    global attractModeEnabled
    attractModeEnabled = tf

def isAttractModeEnabled():
    return attractModeEnabled

def getCurrentInput():
    return adc[0], adc[1], adc[2]     # I don't care about extremely intermittent erroneous values here, so no mutex lock
    
def getVoltageInput():
    return VDC[4], VDC[5], VDC[6]
    
def setState(state):    
    global ioThread
    logger.info("Setting hydraulics driver state to {}".format(state))
    if (isinstance(state, basestring)):
        if (state.lower() == "attract"):
            ioThread.setState(ATTRACT)
        elif (state.lower() == "passthrough"):
            ioThread.setState(PASSTHROUGH)
        elif (state.lower() == "nomove"):
            ioThread.setState(NO_MOVE)
        elif (state.lower() == "loopback"):
            ioThread.setState(LOOPBACK)
        elif (state.lower() == "test"):
            ioThread.setState(TEST)
        else:
            logger.warn("Attempted to set hydraulics driver to unknown state {}".format(state))
            
def getAllStates():
    return ["attract", "passthrough", "nomove", "loopback", "test"]
    
def getState():
    global ioThread
    intState = ioThread.getState()
    if (intState == ATTRACT):
        return "attract"
    elif (intState == PASSTHROUGH):
        return "passthrough"
    elif (intState == NO_MOVE):
        return "nomove"
    elif (intState == LOOPBACK):
        return "loopback"
    elif (intState == TEST):
        return "test"
    else:
        return "unknown"
        
def startRecording(file):
    ioThread.startRecording(file)

def stopRecording():
    ioThread.stopRecording()
    
def isRecording():
    return ioThread.isRecording
    
def getLoopbackValues():
    return test_output_x, test_output_y, test_output_z
    
def setLoopbackValues(x, y, z):
    global test_output_x
    global test_output_y
    global test_output_z
    
    try:
        test_output_x = int(x)
        test_output_y = int(y)
        test_output_z = int(z)
    except NumberFormatException:
        pass

class four_20mA_IO_Thread(Thread):
    def __init__(self, spi, mode):
        Thread.__init__(self)
        self.spi = spi
        self.running = True
        self.state = mode
        self.isRecording   = False
        self.recordingFile = None
        self.fileMutex = Lock()
        
        GPIO.setup(4,GPIO.OUT)       # Chip Select for the 2AO Analog Output module
        GPIO.output(4,1)
        GPIO.setup(22,GPIO.OUT)      # Chip Select for the 2nd 2AO Analog Output module
        GPIO.output(22,1)
        GPIO.setup(7,GPIO.OUT)       # Chip Select for the 8AI Analog Input module
        GPIO.output(7,1)
        
    def stop(self):
        self.running = False
        
    def setState(self, state):
        if (state == PASSTHROUGH or state == ATTRACT or state == NO_MOVE or state == LOOPBACK or state == TEST):
            self.state = state
            
    def getState(self):
        return self.state
        
    def startRecording(self, file):
        if self.isRecording:
            self.stopRecording()
        self.fileMutex.acquire()
        self.isRecording = True
        self.recordingFile = file
        self.recordingStopTime = time.time() + 30 # maximum recording time 30 seconds.
        self.fileMutex.release()
    
    def stopRecording(self):
        self.fileMutex.acquire()
        self.isRecording = False
        if (self.recordingFile != None):
            self.recordingFile.close()
        self.recordingFile = None
        self.fileMutex.release()
        
        
    def run(self):
        while (self.running):
            try:                    
                self.spi.open(0,1)           # Open SPI Channel 1 Chip Select is GPIO-7 (CE_1), analog read
                ''' Read from inputs '''
                for index in range(0,3):        # Get mA Reading for Channels 1 thru 3 
                    self.readAdc(index)
                    adc[index] = self.readAdc(index)
                    mA[index]  = (adc[index] * mASpan / mASpanAdc) 
#                    print "Reading %d = %0.2f mA" % (index+1,((float)(mA[index]))/Scaler) #XXX - put this in logs
                for index in range(4,7):        # Get Voltage reading for channels 5 thru 7
                    self.readAdc(index)
                    adc[index] = self.readAdc(index)
                    VDC[index] = (adc[index] * VDCSpan / VDCSpanAdc ) 
#                    print "Reading %d = %0.2f VDC" % (index+1,((float)(VDC[index]))/Scaler)
                ''' send sculpture position information to whoever is listening '''
                if self.state == TEST:
                    x,y,z = hydraulics_playback.getPlaybackData()  # test state: send from playback data
                    event_manager.postEvent({"msgType":"pos", "x":x, "y":y, "z":z, "xx":x, "yy":y, "zz":z})
                else:          
                    event_manager.postEvent({"msgType":"pos", "x":mA[0], "y":mA[1], "z":mA[2],
                                                    "         xx":VDC[4], "yy":VDC[5], "zz":VDC[6]})
                # XXX - I need to be able to test this without the outputs hooked up!!!
                '''  Write to outputs '''
                if (self.state == PASSTHROUGH): 
                    self.writeAnalogOutput(4,  0, adc[0])
                    self.writeAnalogOutput(4,  1, adc[1])
                    self.writeAnalogOutput(22, 0, adc[2])
                elif (self.state == ATTRACT):
                    x,y,z = hydraulics_playback.getPlaybackData()
                    self.writeAnalogOutput(4,  0, x)
                    self.writeAnalogOutput(4,  1, y)
                    self.writeAnalogOutput(22, 0, z)
                elif (self.state == LOOPBACK):
                    self.writeAnalogOutput(4,  0, test_output_x)
                    self.writeAnalogOutput(4,  1, test_output_y)
                    self.writeAnalogOutput(22, 0, test_output_z)
                self.spi.close() # XXX open and then close? what?
                if (self.isRecording):
                    if time.time() >= self.recordingStopTime:
                        self.stopRecording()
                    else:
                        self.fileMutex.acquire()
                        self.recordingFile.write("%d\n%d\n%d\n" % (adc[0], adc[1], adc[2])) # XXX check this!
                        self.fileMutex.release()
                time.sleep(poll_interval)
            except Exception as e:
                logger.exception("Error running spi driver")
                #traceback.print_exc(file=sys.stdout)
            

    def readAdc(self, channel):     # SPI Write and Read transfer for channel no.
                                    # Chip Select for Analog Input Module is GPIO-7 (CE_1)
        if((channel > 7) or (channel < 0)):
            return -1
        adc = [0,0,0]
        adc = self.spi.xfer(self.buildReadCommand(channel)) # Chip Select handled automatically by spi.xfer
        return self.processAdcValue(adc) 


    def processAdcValue(self, result):    # Process two bytes data for 12 bit resolution
        byte2 = (result[1] & 0x0f)
        return (byte2 << 8) | result[2]

    def buildReadCommand(self, channel):  # Build MCP3208 ADC Command and Channel No
        input = 0x0600 | (channel << 6)
        buf_0 = (input >> 8) & 0xff
        buf_1 = input & 0xff
        buf_2 = 0;
        return [buf_0, buf_1, buf_2] # 3 bytes to be sent to MCP3208 
        
    def writeAnalogOutput(self, gpio, channel, dac):
        if (channel == 0):
            output = 0x3000  # DAC command for channel 0
        else:
            output = 0xb000  # DAC command for channel 1
        output |= dac
        buf_0 = (output >> 8) & 0xff
        buf_1 = output & 0xff
        GPIO.output(gpio,0)         # Set Chip Select 2AO LOW
        self.spi.writebytes([buf_0,buf_1]) # write command and data bytes to DAC
        GPIO.output(gpio,1)         # Set Ship Select 2AO HIGH
        


if __name__ == '__main__':
    try:
        print "Start Pi-SPI Test program"
        print "Press CTRL C to exit"
        init()           
    except KeyboardInterrupt:   # Press CTRL C to exit Program
        spi.close()
        sys.exit(0)
            
