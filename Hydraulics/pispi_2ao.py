#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import spidev
import sys

spi = spidev.SpiDev()       # spidev should be already installed

GPIO.setmode(GPIO.BCM)      # use the RPi 3 GPIO pin markings
GPIO.setwarnings(False)     # disable warnings
GPIO.setup(4,GPIO.OUT)      # Chip Select for the 2AO Analog Output module
GPIO.output(4,1)            # Chip Select 2AO set high


def writeAnalogOutput1(dac1): # write channel 1 output
    spi.open (0,1)           # open SPI channel 1
    output = 0x3000          # format DAC command for channel 1
    output |= dac1
    buf_0 = (output >> 8) & 0xff
    buf_1 = output & 0xff
    GPIO.output(4,0)         # Set Chip Select 2AO LOW
    spi.writebytes([buf_0,buf_1]) # write command and data bytes to DAC
    GPIO.output(4,1)         # Set Ship Select 2AO HIGH
    spi.close                # close SPI 
    return

def writeAnalogOutput2(dac2): #write channel 2 output
    output = 0xb000
    output |= dac2
    buf_0 = (output >> 8) & 0xff
    buf_1 = output & 0xff
    GPIO.output(4,0)
    spi.writebytes([buf_0,buf_1])
    GPIO.output(4,1)
    spi.close
    return
        
        

if __name__ == '__main__':
    try:
        while True:
            dac1_counts = 745   # 4 mA  Output A1, ~2 VDC Output V1
            dac2_counts = 3723  # 20 mA Output A2, ~10 VDC Output V2
            print "Output 1 DA Counts = " + str(dac1_counts)
            print "Output 2 DA Counts = " + str(dac2_counts)
            writeAnalogOutput1(dac1_counts)
            writeAnalogOutput2(dac2_counts)
            time.sleep(5)            
            
    except KeyboardInterrupt:   # Press CTRL C to exit program
        spi.close()
        sys.exit(0)
            
