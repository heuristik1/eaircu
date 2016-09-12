#!/usr/bin/env python
#
# networkChecker
#
# Checks whether a server is available to the Raspberry Pi.
# If it's not available, the RasPi is told to restart
# To be run periodically (cron job)
#
# AJH 2014


import argparse
import os
from datetime import datetime
import logging


def check_for_sudo():
	"""Check whether we are dealing with the root user."""
	if os.geteuid() == 0:
		return True
	else:
		return False

def get_current_time():
	d = datetime.now()
	time = {}
	time["timestring_long"] = "{0}-{1:02d}-{2:02d} at {3:02d}:{4:02d}:{5:02d}".format(d.year, d.month, d.day, d.hour, d.minute, d.second)
	time["timestring_short"] = "{:02d}:{:02d}:{:02d}".format(d.hour, d.minute, d.second)
	return time

def setup_logging(logfilename):
	# Set up a log file
	logging.basicConfig(filename=str(logfilename), format='%(levelname)s:%(message)s', level=logging.INFO)
	ct = get_current_time()	
	logging.debug(" networkChecker -- START -- {}".format(ct['timestring_long']))

def ping_the_server(args):
	"""Send a ping to the server"""
	cmd = "ping -q -c {} {}".format(args.n, args.host)
	response = os.system(cmd)
	logging.debug("Sending command: {}".format(cmd))
	return response
	
def main(args):
	"""Check whether server is up"""
	# set up log file
	if not args.logfile:
		setup_logging("{}/networkchecker.log".format(os.getcwd()))
	else:
		setup_logging(args.logfile)
	is_sudo = check_for_sudo()
	if is_sudo:
	    logging.debug("Running as sudo user")
	if not is_sudo:
	    logging.debug("Not running as sudo user")
	# send a ping to the server
	response = ping_the_server(args)
	if response == 0:
		ct = get_current_time()	
		logging.info("{0} is up. ({1})".format(args.host, ct['timestring_long']))
		#everything is fine, don't do anything else
	else:
		logging.info("{0} is not reachable".format(args.host))
		# Restart Raspberry Pi when host is not reachable;
		# this should hopefully make network drive available again
		if is_sudo and args.restart:
			ct = get_current_time()
			logging.info("System shutting down now for restart at {}".format(ct['timestring_long']))
			try:
				os.system("sudo shutdown -r now") # this has to be run as sudo
			except:
				logging.info("Shutdown command unsuccessful.")
		elif args.restart and not is_sudo:
			logging.debug("Not shutting down. Sudo permissions required")
	ct = get_current_time()	
	logging.debug(" networkChecker -- STOP -- {}".format(ct['timestring_long']))

	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Network Checker')
	parser.add_argument('-s', '--server', dest='host', help="Server to ping at regular intervals")
	parser.add_argument('-n', '--number', dest='n', default=10, help="Number of pings to send")
	parser.add_argument('-r', '--restart', dest='restart', help="Restart RasPi if server is down", action="store_true")
	parser.add_argument('-l', '--log', dest='logfile', help="Log file name and path")
	args = parser.parse_args()
	main(args)
	
	
