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
control = [0,0,0]

mASpan     = 2000       # mA Full Scale = 20.00 mA
VDCSpan    = 660        # VDC Full Scale = 6.6 VDC
Scaler     = 100        # Scaler factor - all reading are * 100
mASpanAdc  = 3723       # AD Counts to equal 20 mA
VDCSpanAdc = 4095       # AD Counts to equal 6.6 VDC

inputSource = "controller"
feedbackSource = "sculpture"

validInputs = "controller, recording, manual"
validFeedbacks = "sculpture, recording"

outputEnabled = True

manual_x = 0
manual_y = 0
manual_z = 0

ioThread = None

pollInterval = 1
logger = logging.getLogger('hydraulics_drv')

def init(interval = 1000, enableOutput = False):
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
        logger.debug("Input source set to {}".format(source))
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
    
def getControlInput():
    return control[0], control[1], control[2]
    
def getSculpturePosition():
    return VDC[4], VDC[5], VDC[6] 

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
        ''' Run the main driver thread - read from the linear position sensors and PID controllers,
            write out to the linear position sensors. Also broadcast position information 
            to anyone who wants it.
            
            This function is complicated by the fact that, depending on the mode, we may
            be mapping various different inputs (sensor, recorded data, manual data) to various
            different outputs (sensor, no output) or broadcasting different things (sensor,
            recorded data). These different inputs and outputs have different units, which 
            means we need to translate between them if we have to do a mapping. 
            
            Here's a handy key:
            - sensor data from the controller ranges from 400 to 2000 (that's in hundredths 
            of a milliamp)
            - voltage data from the sculpture ranges from 0 to 660 (that's in hundredths of
            a volt)
            - Recorded data ranges from 0.0 to 1.0. These are unitless coordinates.
            - The ADC converter goes from 0-4095. The maximum value for controller data is
            3723. The maximum value for sculpture data is 4095.
            
            In this code, 'control' needs to be in 
            '''
    
        global control
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
                    playback_x, playback_y, playback_z = hydraulics_playback.getPlaybackData()  # test state: send from playback data
                    control[0],control[1],control[2] = normalized_2_adcMA(playback_x, playback_y, playback_z)
                elif inputSource == "manual": # input range is 400-2000
                    control[0], control[1], control[2] = mA_2_adcMA(manual_x, manual_y, manual_z)
                else: # normal state, read from controller
                    control[0] = adc[0]
                    control[1] = adc[1]
                    control[2] = adc[2]
                if feedbackSource == "recording":
                    if inputSource == "recording": # NB - dont call getPlaybackData twice 
                        feedback_x = playback_x
                        feedback_y = playback_y
                        feedback_z = playback_z
                    else:
                        feedback_x, feedback_y, feedback_z = hydraulics_playback.getPlaybackData() 
                else: # Feedback source from PID controller
                    feedback_x, feedback_y, feedback_z = VDC_2_normalized(VDC[4], VDC[5], VDC[6])
                    
                # send sculpture position to whoever is listening
                nX, nY, nZ = adcMA_2_normalized(control[0], control[1], control[2])
                event_manager.postEvent({"msgType":"pos", 
                                         "x":nX, "y":nY, "z":nZ, 
                                         "xx":feedback_x, "yy":feedback_y, "zz":feedback_z})
                event_manager.postEvent({"msgType":"cpos", "x":mA[0], "y":mA[1], "z":mA[2],
                                         "xx":VDC[3], "yy":VDC[4], "zz":VDC[5]})
                                         
                # write to output
                if outputEnabled:
#                    logger.debug("writing output, {}, {}, {}".format(x,y,z))
                    self.writeAnalogOutput(4,  0, control[0])
                    self.writeAnalogOutput(4,  1, control[1])
                    self.writeAnalogOutput(22, 0, control[2])

                self.spi.close() # XXX open and then close? what?
                
                time.sleep(pollInterval)
            except Exception as e:
                logger.exception("Error running spi driver")
 
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
        
# Some utility conversion functions
def VDC_2_normalized(vX, vY, vZ):
    return float(vX)/660.0, float(vY)/660.0, float(vZ)/660.0
    
def normalized_2_VDC(nX, nY, nZ):
    return int(nX*660), int(nY*660), int(nZ*660)
    
def mA_2_normalized(mX, mY, mZ):
    return float(mX-400)/1600, float(mY-400)/1600, float(mZ-400)/1600
    
def normalized_2_mA(nX, nY, nZ):
    return int(nX*1600+400), int(nY*1600+400), int(nZ*1600+400)
    
def normalized_2_adcV(nX, nY, nZ):
    return int(nX*4095), int(nY*4095), int(nZ*4095)

def normalized_2_adcMA(nX, nY, nZ):  # yes, I'm sure numpy does this calculation more elegantly.
    return int(nX*3723), int(nY*3723), int(nZ*3723)
    
def adcMA_2_normalized(mX, mY, mZ):
    return float(mX)/3723.0, float(mY)/3723.0, float(mZ)/3723.0
    
def mA_2_adcMA(mX, mY, mZ):
    return mX*3723/2000, mY*3723/2000, mZ*3723/2000
      


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
    
