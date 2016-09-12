#!/usr/bin/python -x
#
# Basic class to handle gathering temperature from the
# w1 devicesfor sensor in W1ThermSensor.get_available_sensors():
from w1thermsensor import W1ThermSensor
class ReadTemp():

	#from w1thermsensor import W1ThermSensor
	def read_temp(self):
        	readings = {}
        	trnum = 1
		for sensor in W1ThermSensor.get_available_sensors():
			label = "TR" + str(trnum)
			temp_c = sensor.get_temperature()
			if 2 < temp_c < 100:
				readings[label] = temp_c
			trnum += 1
		return readings

    


