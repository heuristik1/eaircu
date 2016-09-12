# imports
import glob
import time

# Using TR1 and TR2 Sensors

def get_tempc(sensor_number):
   base_dir = '/sys/bus/w1/devices/'
   device_folder = glob.glob(base_dir + '28*')[sensor_number]
   device_file = device_folder + '/w1_slave'
   f = open(device_file, 'r')
   lines = f.readlines()
   f.close()

#   Uncomment the following line to see the RAW output from the sensors
   print lines

   while lines[0].strip()[-3:] !='YES':
      time.sleep(0.2)
      lines = get_tempc(sensor_number)
   equals_pos = lines[1].find('t=')
   if equals_pos != -1:
      temp_string = lines[1][equals_pos+2:]
      temp_c = float(temp_string) / 1000.0
   return temp_c



# OK Lets test it!
while True: 
 TR1 = get_tempc(0)
 TR2 = get_tempc(1)
 
 print TR1
 print TR2
 print ""

