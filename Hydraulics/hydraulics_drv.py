''' Communicate with sculpture hydraulics hardware. Reads directly from the linear 
    position sensors in the controllers (input), writes to the PID controllers that
    control the sculpture (output). Also reads current position of the sculpture
    (feedback).
    
    The input and output channels use 4-20mA for signaling.
    The feedback channel uses 0-10V.
    
    Based on sample code provided by WidgetLords for their raspberry pi 4-20mA analog
    read/write boards. Communication with 4-20mA control hardware uses SPI interface
    ("Pi-SPI") 
'''

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

inputSource = "controller"
feedbackSource = "sculpture"

validInputs = "controller, recording, manual"
validFeedbacks = "scuplture, recording"

outputEnabled = True

manual_x = 0
manual_y = 0
manual_z = 0


ioThread = None

pollInterval = 1
logger = logging.getLogger('hydraulics_drv')

def init(interval = 1000, enableOutput  = False):
    logger.info("Hydraulics driver init, interval {}, output {}".format(interval, enableOutput))
    global ioThread
    global pollInterval
    global outputEnabled
    
    outputEnabled = enableOutput
    pollInterval = float(interval)/float(1000)
    
    spi = spidev.SpiDev()   # spidev normally installed with RPi 3 distro's
                            # Make Sure SPI is enabled in RPi preferences
                            

    GPIO.setmode(GPIO.BCM)  # Use RPi GPIO numbers
    GPIO.setwarnings(False) # disable warnings

    ioThread = four_20mA_IO_Thread(spi)
    ioThread.start()
    
def shutdown():
    logger.info("Hydraulics driver shutdown")
    if ioThread:
        logger.info("...Joining hydraulics driver thread")
        ioThread.stop()
        ioThread.join()
        
def getInputSource():
    return inputSource

def setInputSource(source):
    ''' Input sources are either the controller ('controller'), a recorded motion file 
       ('recording'), or manually specified values ('manual') '''
    global inputSource
    if source in validInputs:
        inputSource = source
    else:
        logger.warn("Invalid input source {} specified, ignoring".format(source))
        
def getInputSources():
    return validInputs

def getFeedbackSources():
    return validFeedbacks
    
def getFeedbackSource():
    return feedbackSource
    
def setFeedbackSource(source):
    ''' Feedback sources are either the sculpture ('sculpture'),or a recorded motion file 
        ('recording') Recorded feedback sources are useful for testing flame sequence 
        triggers when you don't need the sculpture to be moving '''
    global feedbackSource
    if source in validFeedbacks:
        feedbackSource = source
    else:
        logger.warn("Invalid feedback source {} specified, ignoring".format(source))
        
def enableOutput(tf=True):
    ''' Enable output to the sculpture'''
    global outputEnabled
    outputEnabled = (tf == True)
    logger.info("Hydraulics output enable set to {}".format(outputEnabled))
       
def isOutputEnabled():
    return outputEnabled

def getCurrentInput():
    return adc[0], adc[1], adc[2]     # I don't care about extremely intermittent erroneous values here, so no mutex lock
    
def getVoltageInput():
    return VDC[4], VDC[5], VDC[6]
    
def setManualPosition(x,y,z):
    global manual_x
    global manual_y
    global manual_z
    
    # XXX check for numerics
    manual_x = int(x)
    manual_y = int(y)
    manual_z = int(z)
    
def getManualPosition():
    return manual_x, manual_y, manual_z
    


class four_20mA_IO_Thread(Thread):
    def __init__(self, spi):
        Thread.__init__(self)
        self.spi = spi
        self.running = True
 
        GPIO.setup(4,GPIO.OUT)       # Chip Select for the 2AO Analog Output module
        GPIO.output(4,1)
        GPIO.setup(22,GPIO.OUT)      # Chip Select for the 2nd 2AO Analog Output module
        GPIO.output(22,1)
        GPIO.setup(7,GPIO.OUT)       # Chip Select for the 8AI Analog Input module
        GPIO.output(7,1)
        
    def stop(self):
        self.running = False
        
      
    def run(self):
        while (self.running):
            try:                    
                self.spi.open(0,1)           # Open SPI Channel 1 Chip Select is GPIO-7 (CE_1), analog read
                # Read input data
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
                if inputSource == "recording":
                    x,y,z = hydraulics_playback.getPlaybackData()  # test state: send from playback data
                elif inputSource == "manual":
                    x = manual_x
                    y = manual_y
                    z = manual_z
                else: # normal state, read from controller
                    x = mA[0]
                    y = mA[1]
                    z = mA[2]
                if feedbackSource == "recording":
                    if inputSource == "recording": # NB - dont call getPlaybackData twice
                        feedback_x = x
                        feedback_y = y
                        feedback_z = z 
                    else:
                        feedback_x, feedback_y, feedback_z = hydraulics_playback.getPlaybackData()
                else:
                    feedback_x = VDC[4]
                    feedback_y = VDC[5]
                    feedback_z = VDC[6]

                # send sculpture position to whoever is listening
                event_manager.postEvent({"msgType":"pos", 
                                         "x":x, "y":y, "z":z, 
                                         "xx":feedback_x, "yy":feedback_y, "zz":feedback_z})
                                         
                # write to output
                if outputEnabled:
#                    logger.debug("writing output, {}, {}, {}".format(x,y,z))
                    self.writeAnalogOutput(4,  0, x)
                    self.writeAnalogOutput(4,  1, y)
                    self.writeAnalogOutput(22, 0, z)

                self.spi.close() # XXX open and then close? what?
                
                time.sleep(pollInterval)
            except Exception as e:
                logger.exception("Error running spi driver")
                #traceback.print_exc(file=sys.stdout)
 
        self.spi.close()
        

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
        


def testHandler(msg):
    logger.info("Received msg: {}".format(msg))
            

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(module)s %(lineno)d:  %(message)s', level=logging.DEBUG)
    try:
        print "Start Pi-SPI Test program"
        print "Press CTRL C to exit"
        event_manager.init()
        event_manager.addListener(testHandler, "pos")
        init(50)
        time.sleep(0.1)   
        setInputSource("manual")
        time.sleep(0.1)
        print "Input Sources are", getInputSources()
        setInputSource("manual")
        setManualPosition(100, 200, 300)
        time.sleep(0.1)
        enableOutput(True)
        time.sleep(0.1) 
    except KeyboardInterrupt:   # Press CTRL C to exit Program
        pass
    except Exception:
        logger.exception("Unexpected test exception")
        
    shutdown()
    event_manager.shutdown()
    sys.exit(0)
    
