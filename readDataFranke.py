#!/usr/bin/env python

#Sensor examples for everything builtin the board such as 
#Magnometer -> Magnetic pull on device
#Gyroscope - > xyz tilt degree on the device
#Accelerometer -> xyz directional force measurment

__version__ = 0.1

import time

import math
import random

#import numpy as np
#import matplotlib.pyplot  as plt

from neo import Accel # import accelerometer
from neo import Magno # import magnometer
from neo import Gyro # import gyroscope
from time import sleep # to add delays

import csv

#import serial
#import sqlite3
#import ast
import datetime
import sys
import os

#from pymodbus.exceptions import ModbusIOException
from argparse import ArgumentParser
# import the server implementation
#from pymodbus.client.sync import ModbusTcpClient as ModbusClient
# configure the client logging
import logging

from subprocess import call







def readBurst(SAMPLES, SAMPLING_RATE, accel, mag, gyr):
 accVals = [None] * SAMPLES
 magVals = [None] * SAMPLES
 gyrVals = [None] * SAMPLES
 times = [None] * SAMPLES
 adcs = [None] * SAMPLES

 startTime = int(round(time.time() * 1000))
 endTime = 0

 delay = 1/float(SAMPLING_RATE)
 
 for i in range (0, SAMPLES):
  accValue = accel.get()
  #magValue = mag.get()
  #gyrValue = gyr.get()
  '''
  accMod = int(accValue[2])
  magMod = int(magValue[2])
  gyrMod = int(gyrValue[2])
  
  accelVals[i] = abs(accMod)
  magVals[i] = abs(magMod)
  gyrVals[i] = abs(gyrMod)
  '''
  accVals[i] = [int(accValue[0]), int(accValue[1]), int(accValue[2]) ]
  #magVals[i] = [int(magValue[0]), int(magValue[1]), int(magValue[2]) ]
  #gyrVals[i] = [int(gyrValue[0]), int(gyrValue[1]), int(gyrValue[2]) ]
  
  times[i] = str(datetime.datetime.now().strftime('%Y%m%d-%H:%M:%S.%f')[:-3])
  
  with open("/sys/bus/iio/devices/iio:device0/in_voltage0_raw", "r") as adcFile:
   adc0 = adcFile.read().replace('\n', '')
   adcs[i] = [adc0]
   
  sleep(delay)
 
 endTime = int(round(time.time() * 1000))
 avgDelay = float(endTime - startTime) / float(len(accVals))
 avgFreq = (1 / avgDelay ) * 1000
	
 print str(avgDelay) + " ms  -  " + str(avgFreq) + " Hz"
 ratio = str(avgFreq / float(SAMPLING_RATE))
 print "Ratio: " + ratio
	
 return accVals, magVals, gyrVals, adcs, times
 
 
 
 
def showData(accData):
 accX = zip(*accData)[0]  
 accY = zip(*accData)[1]
 accZ = zip(*accData)[2]
 
 ffft = abs(np.fft.rfft(accX))
 
 plt.ion()

 data = accX
 
 fig = plt.figure()
 ax1 = fig.add_subplot(211)
 ax2 = fig.add_subplot(212)

 plt.xlabel('samples')
 plt.ylabel('module')
 plt.title('About as simple as it gets, folks')
 #ax1.set_ylim([8000,25000])
 #ax2.set_ylim([0,50000])
 #x2.set_yscale('log')
 line1, = ax1.plot(data[1:])
 line2, = ax2.plot(ffft[1:])

 for i in range(0,1):
  data = accX
  ffft = abs(np.fft.rfft(data))
  line1.set_ydata(data[1:])
  line2.set_ydata(ffft[1:])
  fig.canvas.draw()
  
 plt.show(block=True) 
 
 
 
 

def saveToCvs(csv_file, times, acc, mag, gyr, adcs, gpios):
 
 ##print str( len(times) ) 
 
 line = ""
 
 for i in range(1 , len(times)):
  line = str(times[i])
  
  if acc is not None:
   line = line + "," + str(acc[i][0]) + "," + str(acc[i][1]) + "," + str(acc[i][2])
  if mag is not None:
   line = line + "," + str(mag[i][0]) + "," + str(mag[i][1]) + "," + str(mag[i][2])
  if gyr is not None:
   line = line + "," + str(gyr[i][0]) + "," + str(gyr[i][1]) + "," + str(gyr[i][2])
  if adcs is not None:
   for j in adcs[i]:
    line = line + "," + str(j)
  if gpios is not None:
   for j in gpios[i]:
    line = line + "," + str(j)
  
  #print line
 
  csv_file.write(line + "\n")

 csv_file.write("\n")



 
 
 
 
def main():
 
 accFreqFile = open("/sensors/accelerometer/poll_delay", "w")
 accFreqFile.write("2")
 accFreqFile.close()
 # /sys/bus/iio/devices/iio:device0/in_voltage0_raw
 # /sys/bus/iio/devices/iio:device0/in_voltage_sampling_frequency
 # /sys/bus/iio/devices/iio:device0/
 
 parser = ArgumentParser()

 parser.add_argument('--samplingrate','-f', action='store', default=10, 
                    dest='sampling_rate',
                    help='Set the sampling rate between sensor readings in Hz')
 parser.add_argument('--samples', '-s', action='store', default=16,
                    dest='samples', type=int,
                    help='Set the number of samples per iteration')
 parser.add_argument('--delay', '-d', action='store', default=1,
                    dest='iteration_delay', type=float,
                    help='Set the delay in seconds between two iterations')
 parser.add_argument('--iterations', '-i', action='store', default=1,
                    dest='iterations', type=int,
                    help='Set the number of iteration')
 parser.add_argument('--label', '-l', action='store',
                    dest='label',
                    help='set the label') 
 parser.add_argument('--csv', '-c', action='store_true', default=False,
                    dest='csv_export',
                    help='Export the data in csv')	
									
 parser.add_argument('--version', action='version', version='%(prog)s  ' + str(__version__))

 results = parser.parse_args() 

 print 'Parsed arguments ========='
 print "Sampling rate:  " , results.sampling_rate
 print "Samples per iteration " , results.samples
 print "iterations frequency " , results.iteration_delay
 print "iterations number" , results.iterations
 print "label", results.label
 print '=========================='

 SAMPLING_RATE     = results.sampling_rate
 SAMPLES           = results.samples
 ITERATIONS_DELAY  = results.iteration_delay
 ITERATIONS        = results.iterations
 LABEL             = results.label
 CSV_EXPORT        = results.csv_export

 
 ## initialize motion sensors
 acc = Accel()
 mag = Magno()
 gyr = Gyro() # new objects p.s. this will auto initialize the device onboard

 # accel.calibrate()
 # gyro.calibrate() # Reset current values to 0
 # magno.calibrate()
 
 if CSV_EXPORT:
  # open cvs file
  if LABEL is None: 
   csv_filename = './data/data-'+ str(datetime.datetime.now().strftime('%Y%m%d--%H:%M:%S')) +'.csv'
  else:
   csv_filename = './data/' + LABEL + '-' + str(datetime.datetime.now().strftime('%Y%m%d--%H:%M:%S')) + '.csv'
  csv_file = open(csv_filename, "w+")

 ## main loop
 for i in range(0, ITERATIONS):
  accData, magdata, gyroData, adcs, times  = readBurst(SAMPLES, SAMPLING_RATE, acc, mag, gyr)
  print '>>  Iteration ' + str(i)
  #showData(accData)
  if CSV_EXPORT:
   saveToCvs(csv_file, times, accData, None, None, adcs, None)
  sleep(ITERATIONS_DELAY)
 
 if CSV_EXPORT:
  csv_file.close()
  
   
  

if __name__== "__main__":
 main()







