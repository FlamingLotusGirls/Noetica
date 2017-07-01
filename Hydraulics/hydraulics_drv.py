#!/usr/bin/python

# Based on sample code provided by WidgetLords for their raspberry pi 4-20mA analog 
# read/write boards. Use SPI interface for communication ("Pi-SPI")

import RPi.GPIO as GPIO
import time
import spidev
import sys
import hydraulics_playback
from threading import Thread, Lock
import traceback

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

test_output_x = 0  
test_output_y = 0
test_output_z = 0

ioThread = None

poll_interval = 1

def init():
    global ioThread
    spi = None
    spi = spidev.SpiDev()   # spidev normally installed with RPi 3 distro's
                            # Make Sure SPI is enabled in RPi preferences

    GPIO.setmode(GPIO.BCM)  # Use RPi GPIO numbers
    GPIO.setwarnings(False) # disable warnings

    ioThread = four_20mA_IO_Thread(spi)
    ioThread.start()
    
def shutdown():
    ioThread.stop()
   
def setTestOutputs(x, y, z):
    test_output_x = x
    test_output_y = y
    test_output_z = z

def getCurrentInput():
    return adc[0], adc[1], adc[2]     # I don't care about extremely intermittent erroneous values here, so no mutex lock
    
def setState(state):    
    global ioThread
    print ("Setting hydraulics driver state to", state)
    if (isinstance(state, basestring)):
        if (state.lower() == "attract"):
            ioThread.setState(ATTRACT)
        elif (state.lower() == "passthrough"):
            ioThread.setState(PASSTHROUGH)
        elif (state.lower() == "nomove"):
            ioThread.setState(NO_MOVE)
        elif (state.lower() == "loopback"):
            ioThread.setState(LOOPBACK)
            
def getAllStates():
    return ["attract", "passthrough", "nomove", "loopback"]
    
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
    def __init__(self, spi):
        Thread.__init__(self)
        self.spi = spi
        self.running = True
        self.state = NO_MOVE
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
        if (state == PASSTHROUGH or state == ATTRACT or state == NO_MOVE or state == LOOPBACK):
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
                for index in range(0,4):        # Get mA Reading for Channels 1 thru 4 XXX - need channels 1-6?
                    self.readAdc(index)
                    adc[index] = self.readAdc(index)
                    mA[index]  = (adc[index] * mASpan / mASpanAdc) 
#                    print "Reading %d = %0.2f mA" % (index+1,((float)(mA[index]))/Scaler) #XXX - put this in logs
                '''  Write to outputs '''
                if (self.state == PASSTHROUGH): 
                    self.writeAnalogOutput(4,  0, acd[0])
                    self.writeAnalogOutput(4,  1, acd[1])
                    self.writeAnalogOutput(22, 0, acd[2])
                elif (self.state == ATTRACT):
                    x,y,z = hydraulics_playback.getPlaybackData()
                    self.writeAnalogOutput(4,  0, x)
                    self.writeAnalogOutput(4,  1, y)
                    self.writeAnalogOutput(22, 0, z)
                    print( "attract mode, reading x:{}, y:{}, z:{}".format(x,y,z) )
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
                        self.recordingFile.write("%.3f\n%.3f\n%.3f\n" % (adc[0], adc[1], adc[2])) # XXX check this!
                        self.fileMutex.release()
                time.sleep(poll_interval)
            except Exception as e:
                print("Error running spi driver", e)
                traceback.print_exc(file=sys.stdout)
            

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
            
