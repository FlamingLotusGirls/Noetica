#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import spidev
import sys

print "Start Pi-SPI-8AI Test program"
print "Press CTRL C to exit"

spi = spidev.SpiDev()   # spidev normally installed with RPi 3 distro's
                        # Make Sure SPI is enabled in RPi preferences

GPIO.setmode(GPIO.BCM)  # Use RPi GPIO numbers
GPIO.setwarnings(False) # disable warnings

adc = [0,0,0,0,0,0,0,0]
mA = [0,0,0,0,0,0,0,0]
VDC = [0,0,0,0,0,0,0,0]

mASpan = 2000           # mA Full Scale = 20.00 mA
VDCSpan = 660           # VDC Full Scale = 6.6 VDC
Scaler = 100            # Scaler factor - all reading are * 100
mASpanAdc = 3723        # AD Counts to equal 20 mA
VDCSpanAdc = 4095       # AD Counts to equal 6.6 VDC

def buildReadCommand(channel):  # Build MCP3208 ADC Command and Channel No
    input = 0x0600 | (channel << 6)
    buf_0 = (input >> 8) & 0xff
    buf_1 = input & 0xff
    buf_2 = 0;
    return [buf_0, buf_1, buf_2] # 3 bytes to be sent to MCP3208   

def readAdc(channel):           # SPI Write and Read transfer for channel no.
                                # Chip Select for Analog Input Module is GPIO-7 (CE_1)
    if((channel > 7) or (channel < 0)):
        return -1
    adc = spi.xfer(buildReadCommand(channel)) # Chip Select handled automatically by spi.xfer
    return processAdcValue(adc)   

def processAdcValue(result):    # Process two bytes data for 12 bit resolution
    byte2 = (result[1] & 0x0f)
    return (byte2 << 8) | result[2]


if __name__ == '__main__':
    try:
        spi.open(0,1)           # Open SPI Channel 1 Chip Select is GPIO-7 (CE_1)
        
        while True:
            for index in range(0,4):        # Get mA Reading for Channels 1 thru 4
                adc[index] = readAdc(index)
                mA[index] = (adc[index] * mASpan / mASpanAdc ) 
                print "Reading %d = %0.2f mA" % (index+1,((float)(mA[index]))/Scaler)

            for index in range(4,8):        # Get VDC Readings for Channels 5 thru 8
                adc[index] = readAdc(index)
                VDC[index] = (adc[index] * VDCSpan / VDCSpanAdc ) 
                print "Reading %d = %0.2f VDC" % (index+1,((float)(VDC[index]))/Scaler)

            print " "
            time.sleep(5)
             
    except KeyboardInterrupt:   # Press CTRL C to exit Program
        spi.close()
        sys.exit(0)
            
