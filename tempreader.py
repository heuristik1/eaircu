import glob
import globals as GLB
import os, sys, math
# from readtemp import ReadTemp
from w1thermsensor import *
from datetime import datetime
import RPi.GPIO as GPIO  # Import GPIO library
import time
import logging
import socket
#from coiltest import Coilstring
#from ISStreamer.Streamer import Streamer

    
class TEMPReader():
    currentSecond = None
    newSecond = None
    TR1sensor = None
    TR2sensor = None
   
    logger = None
    host = socket.gethostname()
 #   streamer = Streamer(bucket_name = host, bucket_key = host, access_key="qLErRNJ6F3FpEHTVWhcEndWitkLegc7i")
    
    def __init__(self):
        self.logger = logging.getLogger('root')
        GPIO.setmode(GPIO.BCM)
        

    def run(self):
        self.initialize_DeviceID()
	#self.get_tempc()
        #self.initialize_temp_sensors()
        self.collectTempData()

		
    # get last 6 digit of mac and use it as an id
    def initialize_DeviceID(self):
        # Read MAC from file
        myMAC = open('/sys/class/net/eth0/address').read()
        macToken = myMAC.split(":")
        uniqueId = macToken[3] + macToken[4] + macToken[5]
        self.DeviceID = uniqueId.replace("\n", "")	
        return

		
		
    # get temp sensor readings
    def getTempReading(self, tempVal):
        return round(tempVal, GLB.DECIMAL_ACCURACY)

    def get_tempc(self, sensor_number):
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob(base_dir + '28*')[sensor_number]
        device_file = device_folder + '/w1_slave'
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        while lines[0].strip()[-3:] !='YES':
                time.sleep(0.2)
                lines = get_tempc(sensor_number)
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
        return temp_c
		
    def read_data(self):
        tempt1 = self.get_tempc(0)
        #self.logger.debug(tempt1)
        t1Reading = round(
            self.getTempReading(
                tempt1),
            GLB.DECIMAL_ACCURACY)
        tempt2 = self.get_tempc(1)
        #self.logger.debug(tempt2)
        t2Reading = round(
            self.getTempReading(
                tempt2),
            GLB.DECIMAL_ACCURACY)
        #Ycoil = GPIO26
	#Ycoilrest = Coilstring(Ycoil)
        return t1Reading, t2Reading

    def verfiyDataRange(self, dataType, value):
        goodRange = False
        # check boundaries of temperature
        if dataType == GLB.DATA_TYPE_TEMPERATURE:
            if GLB.MIN_TEMP <= value <= GLB.MAX_TEMP:
                goodRange = True
        return goodRange

    # collect time stamp data
    def validate_readings(self, picTime, t1Reading, t2Reading):
        self.logger.debug("Validating Readings...")
        # check if data pass range test
        validTemperature1Range = self.verfiyDataRange(GLB.DATA_TYPE_TEMPERATURE, float(t1Reading))
        validTemperature2Range = self.verfiyDataRange(GLB.DATA_TYPE_TEMPERATURE, float(t2Reading))
        # Substitute NULL for error values
        if not validTemperature1Range:
            t1Reading = None
        if not validTemperature2Range:
            t2Reading = None

        collectedData = picTime + "," + self.DeviceID + "," + "," + "," + "," + \
                        "," + "," + str(t1Reading) + "," + str(t2Reading)
        return collectedData

    def collectTempData(self):
        dataCount = 0
        currentFileName = GLB.TEMPLOG_FILE_NAME
        
        while True:
            

            # get a new file name in the beginning of the data collection cycle
            if dataCount == 0:
                currentFileName = self.getNewTempLogFileName()

            now = datetime.now()
            picTime = now.strftime("%Y-%m-%d %H:%M:%S")
            self.currentSecond = now.second
            #readings = self.read_data()
            self.logger.debug("readdata...")
            #
            t1Reading,t2Reading = self.read_data()
            #t2Reading = self.read_data(1)
            # discard duplicates
            if self.is_dup():
                continue

            collectedData = self.validate_readings(
                picTime, t1Reading, t2Reading)

            # store data
            self.storeToFile(currentFileName, collectedData)

            log_data = "[TIME] " + picTime + "\n" + \
                       "[ID] " + self.DeviceID + "\n" + \
                       "[T1] " + str(t1Reading) + "\n" + \
                       "[T2] " + str(t2Reading) + "\n"
 		       #"[RESTY]" +str(Ycoilrest) + "\n"
            #self.logger.info(collectedData)
            #self.streamer.log("[TIME] ", picTime)
            #self.streamer.log("[ID] ", self.DeviceID)
            #         self.streamer.log("[Tblue] ", str(t2Reading), epoch = picTime)
            #         self.streamer.log("[Tyello] ", str(t1Reading), epoch = picTime)
            #          self.streamer.flush

            dataCount += 1
            time.sleep(.85)
            if dataCount > 59:
                dataCount = 0
            
        return

    def is_dup(self):
        dup = False
        self.newSecond = datetime.now().second
        if self.currentSecond == self.newSecond:
            dup = True
            self.logger.info("Duplicate reading found at second %s" % str(self.newSecond))
        self.currentSecond = self.newSecond
        time.sleep(.85)
        return dup

    # store info into file
    def storeToFile(self, fileName, data, append=True):
        if append:
            myFileOutput = open(fileName, "a")
        else:
            myFileOutput = open(fileName, "w")
        myFileOutput.write(data)
        myFileOutput.close()
        return

    # create log file path if it does not exist
    def createLogFilePath(self):
        # if directory battlog does not exist, create one
        if not (os.path.isdir(GLB.LOG_FILE_PATH)):
            os.mkdir(GLB.LOG_FILE_PATH)
        return

   

    # create debug log file path if it does not exist
    def createDebugFilePath(self):
        # if directory rtclog does not exist, create one
        if not (os.path.isdir(GLB.DEBUG_FILE_PATH)):
            os.mkdir(GLB.DEBUG_FILE_PATH)
        return

    # get current time in a string
    def getTimeString(self):
        return time.strftime("%m%d%y%H%M%S")

    # get current time in a string formatted for reading
    def getFormatTimeString(self):
        return time.strftime("%m/%d/%y %H:%M:%S")

    # get new file name based on current time
    def getNewTempLogFileName(self):
        return GLB.TEMPLOG_FILE_NAME + self.getTimeString() + ".txt"

    # get new file name based on current time
    def getDebugNewFileName(self):
        return GLB.DEBUG_FILE_NAME + self.getTimeString() + ".csv"

    # use this function to print or save debug msg
    def log(self, logType, msg):
        if logType == GLB.DEBUG_DETAIL:
            self.storeToFile(GLB.DEBUG_LOG_FILE_NAME, self.getTimeString() + " " + msg)
        elif logType == GLB.DEBUG_SAVE:
            self.storeToFile(GLB.DEBUG_LOG_FILE_NAME, self.getTimeString() + " " + msg)
   
   
