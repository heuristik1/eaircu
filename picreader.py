import globals as GLB
import spidev, os, sys, math
# from readtemp import ReadTemp

from datetime import datetime
import RPi.GPIO as GPIO  # Import GPIO library
import time
from monotonic import monotonic as monotonic_time
import logging
import socket
#from azure.servicebus import ServiceBusService 


    
class PICReader():
    currentSecond = None
    newSecond = None
    start_time = None
    endtime = None
    v1reference = 0.0
    v2reference = 0.0
    v3reference = 0.0
    c1reference = 0.0
    c2reference = 0.0
    v1slope = 1.0
    v2slope = 1.0
    v3slope = 1.0
    c1slope = 1.0
    c2slope = 1.0
   
    logger = None
    host = socket.gethostname()
    #key_name ="RootManageSharedAccessKey" key_value="-yourkeyhere-"
    #	sbs = ServiceBusService(EAIFDL, shared_access_key_name=key_name, shared_access_key_value=key_value) 
    #	sbs.create_event_hub(host) 
    def __init__(self):
        self.logger = logging.getLogger('root')
        self.createLogFilePath()
        self.initSPI()
        self.setupPIC24RTC()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GLB.CALIBRATION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def run(self):
        self.initialize_calibrated_values()
        self.initialize_slope_multipliers()
        self.collectTimeStampData()

    # for handling of script inputs
    def getSPIOutputByte(self, input):
        msb = input >> 8
        lsb = input & 0xff
        GLB.spi.writebytes([msb, lsb])
        data = GLB.spi.readbytes(2)
        return data

    def get16bitSPIData(self, returnData):
        return self.getWord(returnData[0], returnData[1])

    def getWord(self, msb, lsb):
        return msb * 256 + lsb

    # convert decimal to hex value
    def decToHex(self, decValue):
        firstDigit = (decValue / 10) << 4
        secondDigit = decValue % 10
        return firstDigit + secondDigit

    def getSystemTimeInHex(self):
        rawTimeData = (time.strftime("%y/%m/%d/%H/%M/%S")).split("/")
        for i in range(0, 6):
            rawTimeData[i] = self.decToHex(int(rawTimeData[i]))
        return rawTimeData

    def addSPIDataMarking(self, sendData):
        return sendData | 0x8000

    def removeSPIDataMarking(self, receiveData):
        return receiveData & 0x7fff

    def sendSPIDataWithMarking(self, SPIOutput):
        return self.getSPIOutputByte(self.addSPIDataMarking(SPIOutput))

    def createCommandData(self, commandType, rawData):
        return (commandType << 8) + rawData

    def getPinReading(self, pin):
        my16bitSPIData = self.get16bitSPIData(self.sendSPIDataWithMarking(self.createCommandData(pin, GLB.NULL)))
        return self.removeSPIDataMarking(my16bitSPIData)

    # get current value
    def getCurrReading(self, voltVal, slopemult, calibref=0.0):
        self.logger.debug("Read value %f" % float(voltVal))
        tempV = (voltVal * GLB.ADC_3_3V_RATIO)
        tempV -= GLB.iref
        self.logger.debug("Vout %f" % float(tempV))
        currentVal = tempV * 62.5 * slopemult + calibref
        self.logger.debug("Returning value %f" % float(currentVal))
        return currentVal

    # get voltage value
    def getVoltageReading(self, voltVal, multiplier, slopemult, calibref=0.0):
        voltVal *= multiplier
        if voltVal < GLB.vref:
            voltageVal = (GLB.vref - voltVal)
        else:
            voltageVal = voltVal - GLB.vref
        return voltageVal * slopemult + calibref

    # get last 6 digit of mac and use it as an id
    def getDeviceId(self):
        # Read MAC from file
        myMAC = open('/sys/class/net/eth0/address').read()
        macToken = myMAC.split(":")
        uniqueId = macToken[3] + macToken[4] + macToken[5]
        return uniqueId.replace("\n", "")

    # use this function to reset pic24
    def resetPic24(self):
        self.initPicResetGPIO()
        GPIO.output(GLB.NRESET_PIC24_GPIO_PIN, False)
        time.sleep(GLB.NRESET_PIC24_HOLD_TIME)
        GPIO.output(GLB.NRESET_PIC24_GPIO_PIN, True)
        self.releaseGPIO()
        return

    # use this function to reset entire system
    def resetSystem(self):
        self.initNPorSysGPIO()
        GPIO.output(GLB.NPOR_SYS_GPIO_PIN, False)
        time.sleep(GLB.NPOR_SYS_HOLD_TIME)
        GPIO.output(GLB.NPOR_SYS_GPIO_PIN, True)
        self.releaseGPIO()
        return

    # open connection and setup spi so we can talk to the pic
    def initSPI(self):
        # GLB.spi = spidev.SpiDev()
        GLB.spi.open(0, 0)
        return

    # close spi connection
    def closeSPI(self):
        GLB.spi.close()
        return

    # init pic reset gpio
    def initPicResetGPIO(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  ## Use bcm numbering
        GPIO.setup(GLB.NRESET_PIC24_GPIO_PIN, GPIO.OUT)  ## Setup NRESET_PIC24_PIN as output
        return

    # init npor gpio
    def initNPorSysGPIO(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  ## Use board pin numbering
        GPIO.setup(GLB.NPOR_SYS_GPIO_PIN, GPIO.OUT)  ## Setup NPOR_SYS_PIN as output
        return

    # release gpio pins
    def releaseGPIO(self):
        GPIO.cleanup()
        return

    def calibrate(self):
        self.logger.info("Calibration initiating...")
        tsData = []

        for i in range(GLB.GET_RTC_YEAR, GLB.GET_ADC_DATA6 + 1):
            data = self.getPinReading(i)
            tsData.append(data)

        v1Reading = GLB.REFERENCE_VOLTAGE - self.getVoltageReading(tsData[GLB.TS_DATA_V1], GLB.ADC_VOLT3vRATIO)
        v2Reading = GLB.REFERENCE_VOLTAGE - self.getVoltageReading(tsData[GLB.TS_DATA_V2], GLB.ADC_VOLT3vRATIO)
        v3Reading = GLB.REFERENCE_VOLTAGE - self.getVoltageReading(tsData[GLB.TS_DATA_V3], GLB.ADC_VOLT3vRATIO)
        c1Reading = GLB.REFERENCE_CURRENT - self.getCurrReading(tsData[GLB.TS_DATA_C1])
        c2Reading = GLB.REFERENCE_CURRENT - self.getCurrReading(tsData[GLB.TS_DATA_C2])
        collectedData = str(v1Reading) + "," + str(v2Reading) + "," + str(v3Reading) + "," + \
                        str(c1Reading) + "," + str(c2Reading) + "\n"
        self.storeToFile(GLB.CALIB_FILE_NAME, collectedData, False)
        self.logger.info("Calibration complete")

		
    def initialize_calibrated_values(self):
        try:
            with open(GLB.CALIB_FILE_NAME) as cfile:
                line = cfile.readline()
                line = line.strip()
                cfile.close()
                cdata = line.split(",", 5)
                self.logger.debug("Num calibration values available:%d" % len(cdata))
                if len(cdata) == 5:
                    self.logger.debug("Adding calibration values:")
                    self.logger.debug(cdata)
                    self.v1reference = float(cdata[0])
                    self.v2reference = float(cdata[1])
                    self.v3reference = float(cdata[2])
                    self.c1reference = float(cdata[3])
                    self.c2reference = float(cdata[4])
        except Exception, e:
                self.logger.critical("Exception while reading calibration file %s:%s" % (GLB.CALIB_FILE_NAME, e))

    def initialize_slope_multipliers(self):
	    try:
                with open(GLB.SLOPEADJ_FILE_NAME) as sfile:
                    line = sfile.readline()
                    line = line.strip()
                    sfile.close()
                    sdata = line.split(",", 5)
                    self.logger.debug("Slope Multiplier values available:%d" % len(sdata))
                    if len(sdata) == 5:
                        self.logger.debug("Adding slope multiplier values:")
                        self.logger.debug(sdata)
                        self.v1slope = float(sdata[0])
                        self.v2slope = float(sdata[1])
                        self.v3slope = float(sdata[2])
                        self.c1slope = float(sdata[3])
                        self.c2slope = float(sdata[4])

            except Exception, e:
                self.logger.critical("Exception while reading Slope Multiplier file %s:%s" % (GLB.SLOPEADJ_FILE_NAME, e))

    def read_data(self):

        # prepare timestamp data
        self.prepare_time_stamp()
        tsData = []
        for i in range(GLB.GET_RTC_YEAR, GLB.GET_ADC_DATA6 + 1):
            data = self.getPinReading(i)
            tsData.append(data)
        
        #picTime = str(tsData[GLB.TS_DATA_MONTH]) + "/" + \
        #        str(tsData[GLB.TS_DATA_DAY]) + "/" + \
        #        str(tsData[GLB.TS_DATA_YEAR]) + " " + \
        #        str(tsData[GLB.TS_DATA_HOUR]) + ":" + \
        #        str(tsData[GLB.TS_DATA_MINUTE]) + ":" + \
        #        str(tsData[GLB.TS_DATA_SECOND])
       
        v1Reading = round(
            self.getVoltageReading(tsData[GLB.TS_DATA_V1],
                                   GLB.ADC_VOLT3vRATIO,
                                   self.v1slope,
                                   self.v1reference),
            GLB.DECIMAL_ACCURACY)
        v2Reading = round(
            self.getVoltageReading(tsData[GLB.TS_DATA_V2],
                                   GLB.ADC_VOLT3vRATIO,
                                   self.v2slope,
                                   self.v2reference),
            GLB.DECIMAL_ACCURACY)
        v3Reading = round(
            self.getVoltageReading(tsData[GLB.TS_DATA_V3],
                                   GLB.ADC_VOLT3vRATIO,
                                   self.v3slope,
                                   self.v3reference),
            GLB.DECIMAL_ACCURACY)
        c1Reading = round(
            self.getCurrReading(tsData[GLB.TS_DATA_C1],
                                self.c1slope,
                                self.c1reference),
            GLB.DECIMAL_ACCURACY)
        c2Reading = round(
            self.getCurrReading(
                tsData[GLB.TS_DATA_C2],
                self.c2slope,
                self.c2reference),
            GLB.DECIMAL_ACCURACY)
        return c1Reading, c2Reading, v1Reading, v2Reading, v3Reading

    def verfiyDataRange(self, dataType, value):
        goodRange = False
        # check boundaries of voltage
        if dataType == GLB.DATA_TYPE_VOLTAGE:
            if GLB.MIN_VOLTAGE <= value <= GLB.MAX_VOLTAGE:
                goodRange = True
        # check boundaries of current
        elif dataType == GLB.DATA_TYPE_CURRENT:
            if GLB.MIN_ABS_CURRENT <= math.fabs(value) <= GLB.MAX_ABS_CURRENT:
                goodRange = True
        return goodRange

	

    # collect time stamp data
    def validate_readings(self, picTime, v1Reading, v2Reading, v3Reading, c1Reading, c2Reading):
        self.logger.debug("Validating Readings...")
        # check if data pass range test
        validVoltage1Range = self.verfiyDataRange(GLB.DATA_TYPE_VOLTAGE, float(v1Reading))
        validVoltage2Range = self.verfiyDataRange(GLB.DATA_TYPE_VOLTAGE, float(v2Reading))
        validVoltage3Range = self.verfiyDataRange(GLB.DATA_TYPE_VOLTAGE, float(v3Reading))
        validCurrent1Range = self.verfiyDataRange(GLB.DATA_TYPE_CURRENT, float(c1Reading))
        validCurrent2Range = self.verfiyDataRange(GLB.DATA_TYPE_CURRENT, float(c2Reading))

        # Substitute NULL for error values
        if not validVoltage1Range:
            v1Reading = None
        if not validVoltage2Range:
            v2Reading = None
        if not validVoltage3Range:
            v3Reading = None
        if not validCurrent1Range:
            c1Reading = None
        if not validCurrent2Range:
            c2Reading = None

        collectedData = picTime + "," + self.getDeviceId() + "," + \
                        str(v1Reading) + "," + str(v2Reading) + "," + str(v3Reading) + "," + \
                        str(c1Reading) + "," + str(c2Reading) + "," + "," + "\n"
        return collectedData

    def collectTimeStampData(self):
        dataCount = 0
        #start_time = time.time()
        #t1 = start_time
        #t2 = t1
        #time.sleep(1 - time.monotonic() % 1))
        #time.sleep(1)
        currentFileName = GLB.LOG_FILE_NAME
        #rtemp = None
        #try:
        #    rtemp = ReadTemp()
        #except Exception, e:
        #    self.logger.critical("Temperature reading unavailable: %s" % e)

        # scan pic every 1 sec for new adc data until stopped
        while True:
            time.sleep(1 - monotonic_time() % 1)
            #f()
            # get a new file name in the beginning of the data collection cycle
            if dataCount == 0:
                currentFileName = self.getNewFileName()

            now = datetime.now()
            self.currentSecond = now.second
            picTime = now.strftime("%Y-%m-%d %H:%M:%S")
            #picTime = str(tsData[GLB.TS_DATA_MONTH]) + "/" + \
            #    str(tsData[GLB.TS_DATA_DAY]) + "/" + \
            #    str(tsData[GLB.TS_DATA_YEAR]) + " " + \
            #    str(tsData[GLB.TS_DATA_HOUR]) + ":" + \
            #    str(tsData[GLB.TS_DATA_MINUTE]) + ":" + \
            #    str(TSdata[GLB.TS_DATA_SECOND])   

            c1Reading, c2Reading, v1Reading, v2Reading, v3Reading = self.read_data()
            # discard duplicates
            if self.is_dup():
                #time.sleep(.8)
                continue
            #endtime = time.time()
            #self.logger.info("Starttime: %s" % str(start_time))
            #self.logger.info("Endtime: %s" % str(endtime))
            #sleeptime = (endtime - start_time)
            #time.sleep(sleeptime)
            collectedData = self.validate_readings(
                picTime, v1Reading, v2Reading, v3Reading, c1Reading, c2Reading)



            # store data
            self.storeToFile(currentFileName, collectedData)

            log_data = "[TIME] " + picTime + "\n" + \
                       "[ID] " + self.getDeviceId() + "\n" + \
                       "[V1] " + str(v1Reading) + "\n" + \
                       "[V2] " + str(v2Reading) + "\n" + \
                       "[V3] " + str(v3Reading) + "\n" + \
                       "[C1] " + str(c1Reading) + "\n" + \
                       "[C2] " + str(c2Reading) + "\n"
            self.logger.info(log_data)
            #self.streamer.log("[TIME] ", picTime)
            #self.streamer.log("[ID] ", self.getDeviceId())
            #self.streamer.log("[Vpack] ", str(v1Reading))
            #self.streamer.log("[Vyello] ", str(v2Reading))
            #self.streamer.log("[Vblue] ", str(v3Reading))
            #self.streamer.log("[Iyello] ", str(c1Reading))
            #self.streamer.log("[Iblue] ", str(c2Reading))
             
            dataCount += 1
            #dataCountimp = float(dataCount)
            #test = dataCountimp %2
            #t1 = start_time
            #t2 = t1
            #period = 1.0
            #if (t2 - t1 < period) :
            #     t2 = time.time()	
            #t1+=period 
	
            #if (t2 -t1 >= period):
            #     self.streamer.log("[Vpack] ", str(v1Reading))
            #     self.streamer.log("[Vyello] ", str(v2Reading))
            #     self.streamer.log("[Vblue] ", str(v3Reading))
            #     self.streamer.log("[Iyello] ", str(c1Reading))
            #     self.streamer.log("[Iblue] ", str(c2Reading))
	    self.logger.info("ENDoLOOP")
            if dataCount > 59:
                dataCount = 0
            
        return

    def is_dup(self):
        dup = False
        #self.newSecond = datetime.now().second
        #if self.currentSecond == self.newSecond:
        #    dup = True
        #    self.logger.info("Duplicate reading found at second %s" % str(self.newSecond))
        #self.currentSecond = self.newSecond
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

    # create rtc log file path if it does not exist
    def createRTCFilePath(self):
        # if directory rtclog does not exist, create one
        if not (os.path.isdir(GLB.RTC_FILE_PATH)):
            os.mkdir(GLB.RTC_FILE_PATH)
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
    def getNewFileName(self):
        return GLB.LOG_FILE_NAME + self.getTimeString() + ".txt"

    # get new file name based on current time
    def getDebugNewFileName(self):
        return GLB.DEBUG_FILE_NAME + self.getTimeString() + ".csv"

    # use this function to print or save debug msg
    def log(self, logType, msg):
        if logType == GLB.DEBUG_DETAIL:
            self.storeToFile(GLB.DEBUG_LOG_FILE_NAME, self.getTimeString() + " " + msg)
        elif logType == GLB.DEBUG_SAVE:
            self.storeToFile(GLB.DEBUG_LOG_FILE_NAME, self.getTimeString() + " " + msg)

    

    # set up rtc time in pic
    def setupPIC24RTC(self):

        # init retry attempt counter
        retryAttempt = 0

        currentPICResetCount = 0

        # get sys time in hex
        sysTimeHex = self.getSystemTimeInHex()
        rtcSetupDone = False

        while not rtcSetupDone:
            for i in range(GLB.SET_RTC_YEAR, GLB.SET_RTC_SECOND + 1):
                my16bitSPIData = self.get16bitSPIData(
                    self.sendSPIDataWithMarking(self.createCommandData(i, sysTimeHex[i])))
                SPIAck = self.removeSPIDataMarking(my16bitSPIData)

                # no ack from pic that we set up rtc
                if not SPIAck:
                    retryAttempt = retryAttempt + 1
                    self.logger.warning("rtc variable %s set up failed, retry setup in 1 second, attempt #%s" % (
                        str(i), str(retryAttempt)))
                    time.sleep(GLB.SETUP_FAILED_DELAY)

                    # reset pic if max number of retry attempts is reached
                    if retryAttempt >= GLB.MAX_RETRY_ATTEMPT:

                        # reset system if max number of resets on pic still does not resolve issue
                        if currentPICResetCount >= GLB.MAX_PIC_RESET:
                            self.logger.critical("max number of pic reset for rtc setup reached, resetting system")
                            # catastrophic failure, reset entire board and exit program
                            self.resetSystem()
                            sys.exit()

                        # reset pic to see if we can fix the rtc setup issue
                        else:
                            self.logger.critical("max number of retry attempt for rtc setup is reached, resetting pic")
                            self.resetPic24()
                            time.sleep(GLB.NRESET_PIC24_HOLD_TIME * 2)
                            retryAttempt = 0
                            currentPICResetCount = currentPICResetCount + 1
                    break

                # rtc variable got set up correctly
                self.logger.info("rtc variable %s set up correctly" % str(i))

                # rtc setup is done
                if i == GLB.SET_RTC_SECOND:
                    self.logger.info("rtc set up successful")
                    rtcSetupDone = True
                    time.sleep(GLB.PIC_SETUP_DELAY)
        return

    def prepare_time_stamp(self):
        # prepare time stamp in pic
        timeStampDone = False

        while not timeStampDone:
            SPIAck = self.getPinReading(GLB.PREPARE_TS)

            # no ack from pic that we set up time stamp
            if not SPIAck:
                retryAttempt = retryAttempt + 1
                self.logger.warning(
                    "prepare time stamp failed, retry setup in 1 second, attempt #%s" % str(retryAttempt))
                time.sleep(GLB.SETUP_FAILED_DELAY)

                # reset pic if max number of retry attempts is reached
                if retryAttempt >= GLB.MAX_RETRY_ATTEMPT:

                    # reset system if max number of resets on pic still does not resolve issue
                    if currentPICResetCount >= GLB.MAX_PIC_RESET:
                        self.logger.critical("max number of pic reset  for ts collection reached, resetting system")
                        # catastrophic failure, reset entire board and exit program
                        self.resetSystem()
                        sys.exit()

                    # reset pic to see if we can fix the ts collection issue
                    else:
                        self.logger.critical("max number of retry attempt for ts collection is reached, resetting pic")
                        self.resetPic24()
                        time.sleep(GLB.NRESET_PIC24_HOLD_TIME * 2)
                        retryAttempt = 0
                        currentPICResetCount = currentPICResetCount + 1

            else:
                self.logger.info("prepare time stamp success")
                timeStampDone = True
                time.sleep(GLB.PIC_SETUP_DELAY)
                retryAttempt = 0
