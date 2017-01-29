import globals as GLB
import glob
import spidev
import os, sys, math
from w1thermsensor import W1ThermSensor
import os.path
import time
#import datetime
from azure.storage.blob import BlockBlobService
from datetime import datetime
import RPi.GPIO as GPIO  # Import GPIO library
from monotonic import monotonic as monotonic_time
import logging
import socket
from ConfigParser import SafeConfigParser
from time import sleep
from coilstring.coilstring import *
import yaml
import logging.config
import threading
import get_packv
import numpy as np


class RollingAverager():
    def __init__(self, window):
        self.values = []
        self.window = window
    def addValue(self,value):
        self.values.append(value);  # add value to end of value list
        self.values = self.values[-1 * self.window:]  # keep last "window" num of elements
    def getAvg(self):
        return 1.0 * sum(self.values) / len(self.values)



class PICReader(threading.Thread):
    currentSecond = None
    newSecond = None
    start_time = None
    endtime = None
    currentfilename = None
    killdelaystatus = None
    startup = datetime.now()
    StartTime = startup.strftime("%Y-%m-%d %H:%M:%S")
    host = socket.gethostname()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
   
    #dataCount = None
    
    def __init__(self):
        super(PICReader, self).__init__()
        self.createLogFilePath()
        #self.setup_logging()
        self.logger = logging.getLogger(__name__)
        #self.logging.basicConfig()
        self.initSPI()
        
        #self.logger = logging.getLogger(__init__)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(GLB.allcontrolpins, GPIO.OUT)
        GPIO.output(GLB.allcontrolpins, GPIO.LOW)
        GPIO.setup(GLB.allstatpins, GPIO.IN)
    

    def run(self):
        
        self.log_that_data()




    def calc_voltage(self, adc_code):
        out = int(adc_code, 16)
        #self.logger.info ("RAW CODE {}".format(out))
        count = out
        out >>= 4
        #self.logger.info ("CODE minus lower bits {}".format(out))
        out &= 0x0FFFF
        #self.logger.info ("CODE minus status bits {}".format(out))
        out -= 0x20000
        out=float(out)
        out=out/131072.0
        return ((out*5)+5)*29.76

    # get last 6 digit of mac and use it as an id
    def getDeviceId(self):
        # Read MAC from file
        myMAC = open('/sys/class/net/eth0/address').read()
        macToken = myMAC.split(":")
        uniqueId = macToken[3] + macToken[4] + macToken[5]
        return uniqueId.replace("\n", "")


    def initSPI(self):
        # GLB.spi = spidev.SpiDev() # close spi connection
        GLB.spi0 = spidev.SpiDev()
        GLB.spi0.open(0,0)
        GLB.spi1 = spidev.SpiDev()
        GLB.spi1.open(0,1)
        #GLB.spi.open(0,1) 
        #GLB.spi.open(0,0)
        GLB.spi0.max_speed_hz = 122000
        GLB.spi0.bits_per_word = 8
        GLB.spi0.cshigh = False
        GLB.spi0.lsbfirst = False
        GLB.spi0.mode = 0
        GLB.spi1.max_speed_hz = 122000
        GLB.spi1.bits_per_word = 8
        GLB.spi1.cshigh = False
        GLB.spi1.lsbfirst = False
        GLB.spi1.mode = 0
        return
           
    # close spi connection
    def closeSPI(self): #GPIO.setwarnings(False)
        GLB.spi0.close() #GPIO.setmode(GPIO.BCM) ## Use board pin numbering
        GLB.spi1.close()
        return
        
    #get spi data
    def read_stringdata(self,ch):
        #out = None
        self.initSPI
        r = GLB.spi1.xfer2([ch,ch,ch],0, 65535)
     

        adc1_code =  ''.join('{:02x}'.format(x) for x in r)
      
        time.sleep(.085)      
        return self.calc_voltage(adc1_code)

   #read first ADC for pack voltage.     
    def read_packdata(self,CHN):
        #out=None
        #self.initSPI 
        resp=GLB.spi0.xfer2([CHN,CHN,CHN],0, 65535)
        adc_code = ''.join('{:02x}'.format(x) for x in resp)
        time.sleep(.085)

        return self.calc_voltage(adc_code)

    #Read second ADC for string voltage
    def read_channels(self):  
        dummy = self.read_packdata(0xB0)
        time.sleep(.04)
        v1Reading = round(
            self.read_packdata(0xB0),
            GLB.DECIMAL_ACCURACY)
        dummy = self.read_stringdata(0xB0)
        time.sleep(.04)
        v2Reading = round(
            self.read_stringdata(0xB0),
            GLB.DECIMAL_ACCURACY)
        time.sleep(.04)
        #self.closeSPI
        dummy = self.read_stringdata(0xB8)
        #self.initSPI
        time.sleep(.04)
        v3Reading = round(
            self.read_stringdata(0xB8),
            GLB.DECIMAL_ACCURACY)
        time.sleep(.04)
        #self.closeSPI
        #dummy = self.read_stringdata(0xB1)
        dummy = self.read_stringdata(0xB1)
        #self.initSPI
        time.sleep(.04)
        v4Reading = round(
            self.read_stringdata(0xB9),
            GLB.DECIMAL_ACCURACY)
        time.sleep(.03)
        dummy =  self.read_stringdata(0xB9)
        time.sleep(.03)
        v5Reading = round(
            self.read_stringdata(0xB9),
            GLB.DECIMAL_ACCURACY)
        #t1Reading,t2Reading,t3Reading,t4Reading  = self.read_tempdata()
        return v1Reading, v2Reading, v3Reading, v4Reading, v5Reading 
   
   #when called, kills rest on all strings.
    def killRest(self):
       # Valuecheck Processing for error values
       #allcontrolpins = [19,20,21,26]
       for i in GLB.allcontrolpins:
           GPIO.output(i,GPIO.LOW)
       self.killdelaystatus = "INACTIVE"
       self.logger.info ("killdelaystatus = %s" % self.killdelaystatus)
       time.sleep(.1)
       if not self.stringstatus == "ALLACTIVE":
           self.soundthealarm("PACK","String Rest Malfunction")
         
       return

    def TheftAlarm(self,stringname):
       self.soundthealarm(stringname,"Theft Alarm")
       return
  
    def HiPackAlarm(self,stringname):
       self.soundthealarm(stringname,"HIPackAlarm")
       return
   
    def LOPackAlarm(self,stringname):
       self.soundthealarm(stringname,"LOPackAlarm")        
       return
    
    def stringstatus(self):
       total = 0
       for i in GLB.allstatpins:
           total = total + GPIO.input(i)
           #self.logger.info ("total is %s" % total)
       stringstatus = "ALLACTIVE" if total < 1 else "REST"
       return stringstatus
                  
           

    
    def verifyDataRange(self, dataType, value, stringname):
       goodRange = False
       killdelay = threading.Timer(GLB.KILL_DELAY, self.killRest)
       killdelay.setName('killdelay') 
        #check pack voltage
       if dataType == GLB.DATA_TYPE_PACKVOLTAGE:
            if GLB.MIN_VPACK_REST >= value:
                if self.killdelaystatus == "INACTIVE" and self.stringstatus() == "REST":
                        self.logger.info("Kill delay due to low pack V")
                        
                        #killdelay = threading.Timer(900, self.killRest())
                        #killdelay.setName('killdelay') 
                        killdelay.start()
                        self.killdelaystatus = "ACTIVE"
                        self.soundthealarm(stringname,"Kill Rest-Low Pack Voltage")
                    
                goodRange = True
            elif GLB.MIN_PACKALARM >= value:
                self.soundthealarm(stringname,"LO Pack Alarm")
                self.logger.info("Low Pack Alarm")
                goodRange = True
            elif GLB.MAX_PACKALARM <= value:
                self.soundthealarm(stringname,"Hi Pack Alarm")
                if self.killdelaystatus == "ACTIVE" and self.stringstatus() == "REST":
                        killdelay.cancel()
                        self.logger.info("Kill delay cancelled")
                        self.killdelaystatus = "INACTIVE"
                        self.soundthealarm(stringname,"Cancel KillDelay")
                
                goodRange = True
            elif GLB.MIN_PACKVOLTAGE < value < GLB.MAX_PACKVOLTAGE:
                
                goodRange = True
                                           
        #check string voltage
       elif dataType == GLB.DATA_TYPE_STRINGVOLTAGE:
            if GLB.STOLEN_STRINGALARM >= value:
                self.soundthealarm(stringname, "Theft Alarm")
                
      
                goodRange = True
            
            elif GLB.MIN_VSTRING_REST >= value:
                goodRange = True


            elif GLB.MIN_STRINGVOLTAGE < value < GLB.MAX_STRINGVOLTAGE:
                goodRange = True
              
       return goodRange

    # validate readings
    def validate_readings(self, picTime, v1Reading, v2Reading, v3Reading, v4Reading, v5Reading):
        self.logger.debug("Validating Readings...")
        # check if data pass range test
        packVcheck = self.verifyDataRange(GLB.DATA_TYPE_PACKVOLTAGE, float(v1Reading),"PACK")
        stringRVcheck = self.verifyDataRange(GLB.DATA_TYPE_STRINGVOLTAGE, float(v2Reading),"RED")
        stringGVcheck = self.verifyDataRange(GLB.DATA_TYPE_STRINGVOLTAGE, float(v3Reading),"GREEN")
        stringBVcheck = self.verifyDataRange(GLB.DATA_TYPE_STRINGVOLTAGE, float(v4Reading),"BLUE")
        stringYVcheck = self.verifyDataRange(GLB.DATA_TYPE_STRINGVOLTAGE, float(v5Reading),"YELLOW")

   # Substitute NULL for error values
        if not packVcheck:
            v1Reading = None
        if not stringRVcheck:
            v2Reading = None
        if not stringGVcheck:
            v3Reading = None
        if not stringBVcheck:
            v4Reading = None
        if not stringYVcheck:
            v5Reading = None
                  
        
     
        #if not LASTVY == None:
        #    self.compare_readings(LASTVY,nowVY)
        



        collectedData = picTime + "," + self.getDeviceId() + "," + \
            str(v1Reading) + "," + str(v2Reading) + "," + str(v3Reading) + "," + \
            str(v4Reading) + "," + str(v5Reading) + "\n" #str(STATE) + "\n"
        return collectedData 
    


    

   

    def shipalarms(self):
        #def shiplogs(self):
        apath = '/home/pi/battlog/Alarm*.txt'
        afile = self.get_latest_file(apath)
        #print myfile
        host = self.getDeviceId()
        now = datetime.now()
        picTime = now.strftime("%Y-%m-%d %H:%M:%S")
        myblob = host + "-" + picTime + "-alarms.txt"
        blob_service = BlockBlobService(account_name='restcharge',account_key='dMUZG4LV26lL+YxpCIkokjjQhVS8Gq8Yv2D5gTIaq7lb3VImOQ0zwX2NXm+EaP7JkaSEVuPFMIKLoDui4l+oMw==', protocol='http')
        apath = '/home/pi/battlog/*alarms.txt'
        
        mycontainer = 'rcudrop'
        blob_service.create_blob_from_path(
            #myfile = get_latest_file(apath)
        #print myfile
            #blob_service.create_blob_from_path(
                mycontainer,
                myblob,
                afile
                )
        return

    def soundthealarm(self,Sensor, Alarm):
        host = self.getDeviceId()
        now = datetime.now()
        picTime = now.strftime("%Y-%m-%d")
        alarmfile = GLB.ALARMFILENAME + host + "-" + picTime + "-alarms.txt"
        adata =  str(picTime) + "," +  str(host) + "," + str(Sensor) +"," + str(Alarm) + "\n"
        self.storeToFile(alarmfile, adata, append=True)
        return
          
    def string_log(self, report):
        host = self.getDeviceId()
        now = datetime.now()
        picTime = now.strftime("%Y-%m-%d")
        stringlogfile = GLB.STRINGLOGFILENAME + host + "-" + picTime + "-slog.txt"
        sdata =  str(picTime) + "," +  str(host) + "," + str(report) + "\n"
        self.storeToFile(stringlogfile, sdata, append=True)
        return

    def shipstringlogs(self):
        #def shiplogs(self):
        spath = '/home/pi/battlog/str*.txt'
        sfile = self.get_latest_file(spath)
        #print myfile
        host = self.getDeviceId()
        now = datetime.now()
        picTime = now.strftime("%Y-%m-%d %H:%M:%S")
        myblob = host + "-" + picTime + "-slog.txt"
        blob_service = BlockBlobService(account_name='restcharge',account_key='dMUZG4LV26lL+YxpCIkokjjQhVS8Gq8Yv2D5gTIaq7lb3VImOQ0zwX2NXm+EaP7JkaSEVuPFMIKLoDui4l+oMw==', protocol='http')
        mypath = spath
        
        mycontainer = 'rcudrop'
        blob_service.create_blob_from_path(
                mycontainer,
                myblob,
                sfile
                )
        return
    
    def shiplogs(self):
        #def shiplogs(self):
        mypath = '/home/pi/battlog/my*.txt'
        myfile = self.get_latest_file(mypath)
        #print myfile
        host = self.getDeviceId()
        now = datetime.now()
        picTime = now.strftime("%Y-%m-%d %H:%M:%S")
        myblob = host + "-" + picTime + "-vlogs.txt"
        blob_service = BlockBlobService(account_name='restcharge',account_key='dMUZG4LV26lL+YxpCIkokjjQhVS8Gq8Yv2D5gTIaq7lb3VImOQ0zwX2NXm+EaP7JkaSEVuPFMIKLoDui4l+oMw==', protocol='http')
        mypath = '/home/pi/battlog/my*.txt'
        
        mycontainer = 'rcudrop'
        blob_service.create_blob_from_path(
                mycontainer,
                myblob,
                myfile
                )
        return

    def get_latest_file(self,path):
        newest = max(glob.iglob(path), key=os.path.getctime)
        return newest

    


    def log_that_data(self):
        dataCount = 0
        start_delay = 0
        discharge_delay = 0
        restcheck_count = 0
        validate_rest_count = 0
        rest_report = None
        string_report = None
        killdelaystatus = "INACTIVE"
        currentFileName = GLB.LOG_FILE_NAME
        coil_dict = {}  # dictionary to hold our coilstrings
        parser = SafeConfigParser()
        parser.read('settings.ini')
        device = socket.gethostname() # grab device name
        resolution = parser.getint('device', 'resolution')
        allcontrolpins = []
        allstatpins = []
        strings = parser.items('strings')  # setup our coilstrings
        for string, bday in strings:
            bday_split = bday.split(',')[0]
            control_pin_split = int(bday.split(',')[1])
            status_pin_split = int(bday.split(',')[2])
            coil_dict[string] = CoilString(device, string, control_pin_split, status_pin_split, datetime.strptime(bday_split, '%Y-%m-%d %H:%M:%S'))
        allcontrolpins.append(control_pin_split)
        allstatpins.append(status_pin_split)
        GPIO.setup(allcontrolpins, GPIO.OUT)
        GPIO.output(allcontrolpins, GPIO.LOW)
        GPIO.setup(allstatpins, GPIO.IN)
        last_coil_inrest = None
        STATE = "FLOAT"
        Last_smoothed_Vpack = 0
        Current_smoothed_Vpack = 0
        Vpack = 0
        no_rest = None
        no_rest_count = 0
        option_a = None
        option_b = None

        def check_string_state(coil_dict):
            stringvoltages = (v4Reading, v3Reading, v2Reading, v5Reading)
            string_list = sorted([(x.name) for x in coil_dict.values()])
            string_state = zip(string_list,stringvoltages)
            self.logger.info("stringstate = %s" %string_state)
            return

        def rest_callback(coilstring):
            """ 
            Callback for placing string into resting state. 
            """
            #logger.info("coilstring to rest is %s" %coilstring)
            GPIO.output(coilstring.control_pin,GPIO.HIGH)
            # logger = logging.getLogger(__ name__)
            # logger.info("{} was placed into a rest state".format(coilstring.name))
            
            return  

        def rest_check(coilstring):
            GPIO.setup(coil_in_rest.status_pin, GPIO.IN)

        def active_callback(coilstring):
            """
            Callback for placing string into active state. 
            """
            GPIO.output(coilstring.control_pin,GPIO.LOW)

            # logger = logging.getLogger(__name__)
            # logger.info("{} was placed into an active state".format(coilstring.name))
            #restcheck_count = 0
            return

        def get_candidate_coil_string(coil_dict):
            """
            Given a dictionary of 'string name'->CoilString pairs, return the coilstring with the
            least rested time
            """
            # determine which string has least amount of rest time, and place into rest state
            rested_list = sorted([(x.name, x.report_rest_percentage()) for x in coil_dict.values()], key=lambda data: data[1])
            if rested_list:
                self.logger.info("String Rest Report: {}".format(rested_list))
                string_report ="[TIME]" + str(picTime) + "," + ("STRING_REST_REPORT: {}".format(rested_list))
                self.string_log(string_report)
                option_a = coil_dict[rested_list[0][0]]
                option_b = coil_dict[rested_list[1][0]]
                option_c = coil_dict[rested_list[2][0]]
                if option_a == no_rest and option_b == no_rest:
                   return  coil_dict[rested_list[2][0]]
                elif option_a == no_rest:
                   return coil_dict[rested_list[1][0]]
                else:
                   return coil_dict[rested_list[0][0]]

        def seconds_to_rest(coilstring):
            """
            Given a CoilString object, determine the amount of seconds to rest in order to reach 20% of lifetime
            :return: float
            """
            twenty_percent = (datetime.utcnow() - coilstring.bday).total_seconds() * .2
            return twenty_percent - coilstring.total_seconds_rested


        def all_active(coil_dict):
            for x in coil_dict.values():
                if not x == None:
                    if x.state == CoilString.REST:
                        return False
            return True
     
        # here we define our exponential moving average of Vpack.  
        #The period represents the number of Vpack readings we need to establish the moving average.
        #Once we have 5 readings, we then build our moving average and use it to determine changes in state.

        def getpack_v():
            return self.get_packv.run()
      


        while True:
            if self.killdelaystatus == None:
                self.killdelaystatus = "INACTIVE"
            if dataCount == 0:
                currentFileName = self.getNewFileName()
            
            now = datetime.now()
            self.currentSecond = now.second
            picTime = now.strftime("%Y-%m-%d %H:%M:%S")
    
            v1Reading, v2Reading, v3Reading, v4Reading, v5Reading = self.read_channels()
            # discard duplicates
            if self.is_dup():
                #time.sleep(.8)
                continue
            
            collectedData = self.validate_readings(
                picTime, v1Reading, v2Reading, v3Reading, v4Reading, v5Reading)

            roll = RollingAverager(5)
            roll.addValue(v1Reading)
            if start_delay > 4:
                Current_smoothed_Vpack = roll.getAvg()
                            #ema = exponential_moving_avaerage()
            #next(ema)
            
                #return Current_smoothed_Vpack
            #Current_smoothed_Vpack =  smoothed_Vpack(v1Reading)
           
           
                        
            
            

            collectedData = collectedData + "," + str(STATE)
            # store data
            self.storeToFile(currentFileName, collectedData)        
            log_data = "[TIME]" + picTime + "\n" + \
                       "[ID] " + self.getDeviceId() + "\n" + \
                       "[Vpack] " + str(v1Reading) + "\n" + \
                       "[VSR] " + str(v2Reading) + "\n" + \
                       "[VSG] " + str(v3Reading) + "\n" + \
                       "[VSB] " + str(v4Reading) + "\n" + \
                       "[VSY] " + str(v5Reading) + "\n" + \
                       "[STATE]" + str(STATE) + "\n" + \
                       "[SMOOTHEDVPACK]" + str(Current_smoothed_Vpack) + "\n"
        
               
                    
                    
       
          

            start_delay += 1
            dataCount += 1
           
            self.logger.info("Stringstatus = %s" % self.stringstatus())

            
                        
            self.logger.info(log_data)
            if dataCount > 1800:
                #dataCount = 0
                self.shiplogs()
                self.shipalarms()
                dataCount = 0
            if  Current_smoothed_Vpack > GLB.MIN_VPACK_REST: #and start_delay > GLB.startdelay:
             
                if all_active(coil_dict):
                    
                   # determine which string has least amount of rest time, and place into rest state
                    coil_in_rest = get_candidate_coil_string(coil_dict)
                    #if coils_2_rest[0] == "no_rest":
                    #    coil_in_rest = coils_2_rest[1]
                    #    no_rest_count +=1
                    #else:
                    #    coil_in_rest = coils_2_rest[0]
                        
                    if coil_in_rest:
                        rest_for = seconds_to_rest(coil_in_rest)
                        if rest_for > (GLB.MIN_REST_DURATION * GLB.timefactor):
                            self.logger.info(
                            "Placing string {} in a rest state for {} seconds ".format(coil_in_rest.name, rest_for))
                            coil_in_rest.rest(rest_for, resolution, rest_callback, active_callback)
                            rest_report = "[TIME]" + str(picTime) + "," + "[ON_REST]:" + str(coil_in_rest.name) + "," +\
                                           "[REST_DURATION]:" + str(round(rest_for,GLB.DECIMAL_ACCURACY)) + "," + "[PREV_REST_STR]: "  + "\n"      
                           
                        else:
                            self.logger.error("No string meets min duration.")
                        self.string_log(rest_report)
                        self.shipstringlogs()
                        last_coil_inrest = coil_in_rest
                        if no_rest_count > 2:
                            no_rest_count = 0
                            no_rest = None
                        restcheck_count +=1
                       
    
                    else:
                        self.logger.error("Unable to find candidate CoilString to rest")
                    
           
                if restcheck_count >5:
                   self.logger.info("Stringrest check = %s" % rest_check(coil_in_rest))
                   if not rest_check(coil_in_rest):
                    
                       coil_in_rest.cancel_rest()
                       no_rest = coil_in_rest
                       self.logger.info("Cancel Rest due to interruption.")
                       restcheck_count = 0
                      
          

                Current_smoothed_Vpack = Last_smoothed_Vpack
            
        return


    def is_dup(self):
        dup = False
        #self.newSecond = datetime.now().second

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

    def getTimeString(self):
        return time.strftime("%m%d%y%H")

    # get current time in a string formatted for reading
    def getFormatTimeString(self):
        return time.strftime("%m/%d/%y %H:%M:%S")

    # get new file name based on current time
    def getNewFileName(self):
        return GLB.LOG_FILE_NAME + self.getTimeString() + ".txt"

    def daily_validation(self):
        return "Test"
   

