import numpy as np
import globals as GLB
import spidev, os, sys, math
from datetime import datetime
import RPi.GPIO as GPIO  # Import GPIO library
import time
import logging
import cPickle
import pymongo
from os import path

class rester():

    def __init__(self):
        self.logger = logging.getLogger('root')
        self.createLogFilePath()
        self.initSPI()
        #Status Pin Definitions:
        Ycoilstat = 5
        Bcoilstat = 6
        Gcoilstat = 18
        Rcoilstat = 24
        Allcoilstat = [Rcoilstat,Ycoilstat,Bcoilstat,Gcoilstat]
        #Control Pin Definitions:
        Ycontrol = 19
        Bcontrol = 20
        Gcontrol = 21
        Rcontrol = 26
        Allcontrols = [Ycontrol,Bcontrol,Gcontrol,Rcontrol]
        # Pin Setup:
        GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
        # Set Status Pin to input
        GPIO.setup(Allcoils, GPIO.IN)

        #Set Event Detection on Status Change
        GPIO.add_event_detect(Ycoilstat, GPIO.BOTH)
        GPIO.add_event_detect(Bcoilstat, GPIO.BOTH)
        GPIO.add_event_detect(Gcoilstat, GPIO.BOTH)
        GPIO.add_event_detect(Rcoilstat, GPIO.BOTH)
        # Set Control Pin to output
        GPIO.output (Allcontrols,0)
        GPIO.setup(Allcontrols, GPIO.OUT)

        #Time Variables
        bootdelay = 3600 # seconds
        charge2restdelay = 86400
        maxrest = .20 # 20% of Time in Service
        minrest = 604800 #7 DAYS
        minoutage = 600 #10 mins

    def getCoilState(self,Allcoilstat):
        for coil in Allcoils:
            now = datetime.now()
            CoilChangeTime = now.strftime("%Y-%m-%d %H:%M:%S")
            if GPIO.event_detected(coil, GPIO.RISING):
                coil.STARTrest = "START,%d" % (CoilChangeTime)
            elif GPIO.event_detected(coil, GPIO.FALLING):
                coil.STOPrest = "STOP,%d" % (CoilChangeTime)

            return


    def getCoilbirthdays (self,Allcoils):
        Allcoils = [Bcoil,Gcoil,Rcoil,Ycoil]
        for coil in Allcoils:
          coilday = "%d.bday" % (coil)
          try:
            if not os.path.exists (coilday):
                open(coilday, 'w').close()
          with open(coilday, 'r') as f:
              coilbday = path.getmtime(coilday)
              file.close(coilday)
        return coilbday

    def serviceduration (self,coilbday):
        now = datetime.now()
        for coil in Allcoils:
            serviceduration = now - coilbday

    def getLowRestCoil (self,self.bdays)




xResttime/xStarttime = xRestState

# return the lowest valued string
RestCoil =  np.amin(xRestState)

# At this point we rest string and write RestCoil to activeCoil Global Variables (to persist reboot)
If ActiveString != RestCoil
              Write ActiveString to PreviousRestString
               AND Write RestCoil to ActiveString
Else
              Continue

# now we set the pin to Low
If GPIO.input(restCoil,0) AND GPIO.input(restControl,1)
     GPIO.output(restControl,0)
Elseif
   GPIO.input(restcoil,1) AND GPIO.input(restControl,0)
           Continue
Elseif
    #We need an alarm function if the string is in the wrong state.
    GPIO.input(restcoil,0) AND GPIO.input(restcontrol,1)
         ALARM
Elseif
    GPIO.input(restcoil,1) AND GPIO.input(restcontrol,1)
       GPIO.output(restControl,0)
#we need to talk the above section out a bit more, specifically about reboot persistence.

#last thing we need to do is log the durations to a file for each strings rest time.
#these durations are going to be used in the customer portal to show the amount of time each string has been rested.
 # store info into file
    def storeToFile(self, fileName, data, append=True):
        if append:
            myFileOutput = open(fileName, "a")
        else:
            myFileOutput = open(fileName, "w")
        myFileOutput.write(data)
        myFileOutput.close()
        return

   def rw_bday (self, filename)
        now = datetime.now
        if not os.path.exists(filename):
            open(f_loc, 'w').close()

        with open(f_loc) as f:
            f.write (string, now)

from datetime import datetime, timedelta
from time import sleep
import logging


class CoilString:
    REST = 0
    ACTIVE = 1

    def __init__(self, bday=datetime.utcnow()):
        self.logger = logging.getLogger(__name__)
        self.bday = bday  # datetime
        self.rest_periods = []  # durations
        self.active_periods = []  # durations
        self.last_state = CoilString.ACTIVE
        self.last_event_start = datetime.utcnow()

    def rest(self):
        self.logger.info("Resting!")
        if self.last_state == CoilString.REST:
            self.logger.warning("Already in rest state!")
            pass  # REST to REST has no effect
        self.last_state = CoilString.REST
        now = datetime.utcnow()
        self.active_periods.append(now - self.last_event_start)
        self.last_event_start = now

    def activate(self):
        self.logger.info("Activating!")
        if self.last_state == CoilString.ACTIVE:
            self.logger.warning("Already in active state!")
            pass  # ACTIVE to ACTIVE has no effect
        self.last_state = CoilString.ACTIVE
        now = datetime.utcnow()
        self.rest_periods.append(now - self.last_event_start)
        self.last_event_start = now

    def report_rest_percentage(self):
        self.logger.info("Running report...")
        tot_time_since_bday = (datetime.utcnow() - self.bday).seconds  # duration
        time_at_rest = sum([x.seconds for x in self.rest_periods])
        return time_at_rest / float(tot_time_since_bday) * 100

    def write_stats(self):
        # thread on timer for 10mins...write to file/db etc....
        client = pymongo.MongoClient('127.0.0.1', 27017)
        db = client["RestDB"]   #create/connect to the Library Database


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cs = CoilString()
    cs.activate()  # no-op...already active
    cs.rest()
    sleep(10)  # rest 10
    cs.activate()
    sleep(10)
    print "RESTed for {}% of lifetime".format(cs.report_rest_percentage())



    #!/usr/bin/python
# coding=utf-8
#
# controller_log.py - Log controller to periodically query influxdb
#                     and append a log file
#

import datetime
import RPi.GPIO as GPIO
import logging
import subprocess
import threading
import time
import timeit
from influxdb import InfluxDBClient

from config import LOG_PATH
from config import SQL_DATABASE_MYCODO
from config import INFLUXDB_HOST
from config import INFLUXDB_PORT
from config import INFLUXDB_USER
from config import INFLUXDB_PASSWORD
from config import INFLUXDB_DATABASE
from config import MAX_AMPS
from databases.mycodo_db.models import Relay
from databases.mycodo_db.models import RelayConditional
from databases.mycodo_db.models import SMTP
from databases.utils import session_scope
from mycodo_client import DaemonControl
from daemonutils import email, write_influxdb

MYCODO_DB_PATH = 'sqlite:///' + SQL_DATABASE_MYCODO


class RelayController(threading.Thread):
    """
    class for controlling relays

    """

    def __init__(self, logger):
        threading.Thread.__init__(self)

        self.thread_startup_timer = timeit.default_timer()
        self.thread_shutdown_timer = 0
        self.logger = logger
        self.control = DaemonControl()

        self.relay_id = {}
        self.relay_name = {}
        self.relay_pin = {}
        self.relay_amps = {}
        self.relay_trigger = {}
        self.relay_start_state = {}
        self.relay_on_until = {}
        self.relay_last_duration = {}
        self.relay_on_duration = {}

        self.logger.debug("[Relay] Initializing relays")
        try:
            # Setup GPIO (BCM numbering) and initialize all relays in database
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            with session_scope(MYCODO_DB_PATH) as new_session:
                smtp = new_session.query(SMTP).first()
                self.smtp_max_count = smtp.hourly_max
                self.smtp_wait_time = time.time() + 3600
                self.smtp_timer = time.time()
                self.email_count = 0
                self.allowed_to_send_notice = True

                relays = new_session.query(Relay).all()

                self.all_relays_initialize(relays)
            # Turn all relays off
            self.all_relays_off()
            # Turn relays on that are set to be on at start
            self.all_relays_on()
            self.logger.info("[Relay] Finished initializing relays")

        except Exception as except_msg:
            self.logger.exception("[Relay] Problem initializing "
                                  "relays: {}", except_msg)

        self.running = False


    def run(self):
        try:
            self.running = True
            self.logger.info("[Relay] Relay controller activated in "
                             "{}ms".format((timeit.default_timer()-self.thread_startup_timer)*1000))
            while (self.running):
                current_time = datetime.datetime.now()
                for relay_id in self.relay_id:
                    if (self.relay_on_until[relay_id] < current_time and
                            self.relay_on_duration[relay_id] and 
                            self.relay_pin[relay_id]):
                        
                        # Use threads to prevent a slow execution of a
                        # process that could slow the loop
                        turn_relay_off = threading.Thread(
                            target=self.relay_on_off,
                            args=(relay_id, 'off',))
                        turn_relay_off.start()

                        if self.relay_last_duration[relay_id] > 0:
                            write_db = threading.Thread(
                                target=write_influxdb,
                                args=(self.logger, INFLUXDB_HOST,
                                      INFLUXDB_PORT, INFLUXDB_USER,
                                      INFLUXDB_PASSWORD, INFLUXDB_DATABASE,
                                      'relay', relay_id, 'duration_sec',
                                      float(self.relay_last_duration[relay_id]),))
                            write_db.start()

                time.sleep(0.01)
        finally:
            self.all_relays_off()
            self.running = False    
            self.logger.info("[Relay] Relay controller deactivated in "
                             "{}ms".format((timeit.default_timer()-self.thread_shutdown_timer)*1000))


    def relay_on_off(self, relay_id, state,
                     duration=0.0, trigger_conditionals=True):
        """
        Turn a relay on or off
        The GPIO may be either HIGH or LOW to activate a relay. This trigger
        state will be referenced to determine if the GPIO needs to be high or
        low to turn the relay on or off.

        Conditionals will be checked for each action requested of a relay, and
        if true, those conditional actions will be executed. For example:
            'If relay 1 turns on, turn relay 3 off'

        :param relay_id: Unique ID for relay
        :type relay_id: str
        :param state: What state is desired? 'on' or 'off'
        :type state: str
        :param duration: If state is 'on', a duration can be set to turn the relay off after
        :type duration: float
        :param trigger_conditionals: Whether to trigger condionals to act or not
        :type trigger_conditionals: bool
        """
        # Check if relay exists
        if relay_id not in self.relay_id:
            self.logger.warning("[Relay] Cannot turn {} Relay with ID {}. It "
                                "doesn't exist".format(state, relay_id))
            return 1
        if state == 'on':
            if not self.relay_pin[relay_id]:
                self.logger.warning("[Relay] Cannot turn a relay "
                                    "{} ({}) on with a pin of "
                                    "0.".format(self.relay_id[relay_id],
                                                self.relay_name[relay_id]))
                return 1

            current_amps = self.current_amp_load()
            if current_amps+self.relay_amps[relay_id] > MAX_AMPS:
                self.logger.warning("[Relay] Cannot turn relay {} "
                                    "({}) On. If this relay turns on, "
                                    "there will be {} amps being drawn, "
                                    "which exceeds the maximum set draw of {}"
                                    " amps.".format(self.relay_id[relay_id],
                                                    self.relay_name[relay_id],
                                                    current_amps,
                                                    MAX_AMPS))
                return 1

            else:
                if duration:
                    time_now = datetime.datetime.now()
                    if self.is_on(relay_id) and self.relay_on_duration[relay_id]:
                        if self.relay_on_until[relay_id] > time_now:
                            remaining_time = (self.relay_on_until[relay_id]-time_now).seconds
                        else:
                            remaining_time = 0
                        time_on = self.relay_last_duration[relay_id] - remaining_time
                        self.logger.debug("[Relay] Relay {} ({}) is already "
                                            "on for a duration of {:.1f} seconds (with "
                                            "{:.1f} seconds remaining). Recording the "
                                            "amount of time the relay has been on ({:.1f} "
                                            "sec) and updating the on duration to {:.1f} "
                                            "seconds.".format(self.relay_id[relay_id],
                                                              self.relay_name[relay_id],
                                                              self.relay_last_duration[relay_id],
                                                              remaining_time,
                                                              time_on,
                                                              duration))
                        if time_on > 0:
                            write_db = threading.Thread(
                                target=write_influxdb,
                                args=(self.logger, INFLUXDB_HOST,
                                      INFLUXDB_PORT, INFLUXDB_USER,
                                      INFLUXDB_PASSWORD, INFLUXDB_DATABASE,
                                      'relay', relay_id, 'duration_sec',
                                      float(time_on),))
                            write_db.start()

                        self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                        self.relay_last_duration[relay_id] = duration
                        return 0
                    elif self.is_on(relay_id) and not self.relay_on_duration:
                        self.relay_on_duration[relay_id] = True
                        self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                        self.relay_last_duration[relay_id] = duration

                        self.logger.debug("[Relay] Relay {} ({}) is currently"
                                          " on without a duration. Turning "
                                          "into a duration  of {:.1f} "
                                          "seconds.".format(self.relay_id[relay_id],
                                                            self.relay_name[relay_id],
                                                            duration))
                        return 0
                    else:
                        self.relay_on_until[relay_id] = time_now+datetime.timedelta(seconds=duration)
                        self.relay_on_duration[relay_id] = True
                        self.relay_last_duration[relay_id] = duration
                        self.logger.debug("[Relay] Relay {} ({}) on for {:.1f} "
                                          "seconds.".format(self.relay_id[relay_id],
                                                             self.relay_name[relay_id],
                                                             duration))
                        GPIO.output(self.relay_pin[relay_id], self.relay_trigger[relay_id])

                else:
                    if self.is_on(relay_id):
                        self.logger.warning("[Relay] Relay {} ({}) is already on.".format(
                                self.relay_id[relay_id],
                                self.relay_name[relay_id]))
                        return 1
                    else:
                        GPIO.output(self.relay_pin[relay_id],
                                    self.relay_trigger[relay_id])

        else:
            if self._is_setup() and self.relay_pin[relay_id]:  # if pin not 0
                self.relay_on_duration[relay_id] = False
                self.relay_on_until[relay_id] = datetime.datetime.now()
                GPIO.output(self.relay_pin[relay_id], not self.relay_trigger[relay_id])
                self.logger.debug("[Relay] Relay {} ({}) turned off.".format(
                        self.relay_id[relay_id],
                        self.relay_name[relay_id]))

        if trigger_conditionals:
            with session_scope(MYCODO_DB_PATH) as new_session:
                conditionals = new_session.query(RelayConditional)
                new_session.expunge_all()
                new_session.close()

            conditionals = conditionals.filter(RelayConditional.if_relay_id == relay_id)
            conditionals = conditionals.filter(RelayConditional.activated == True)

            if self.is_on(relay_id):
                conditionals = conditionals.filter(RelayConditional.if_action == 'on')
                conditionals = conditionals.filter(RelayConditional.if_duration == 0)
            else:
                conditionals = conditionals.filter(RelayConditional.if_action == 'off')

            for each_conditional in conditionals.all():
                message = None
                if (each_conditional.do_relay_id or
                        each_conditional.execute_command or
                        each_conditional.email_notify):
                    message = "[Relay Conditional {}] " \
                              "If relay {} ({}) turns " \
                              "{}: ".format(each_conditional.id,
                                            each_conditional.if_relay_id,
                                            self.relay_name[each_conditional.if_relay_id],
                                            each_conditional.if_action)

                if each_conditional.do_relay_id:
                    message += "Turn relay {} ({}) {}".format(
                            each_conditional.do_relay_id,
                            self.relay_name[each_conditional.do_relay_id],
                            each_conditional.do_action)

                    if each_conditional.do_duration == 0:
                        self.relay_on_off(each_conditional.do_relay_id,
                                          each_conditional.do_action)
                    else:
                        message += " for {} seconds".format(each_conditional.do_duration)
                        self.relay_on_off(each_conditional.do_relay_id,
                                          each_conditional.do_action,
                                          each_conditional.do_duration)
                    message += ". "


                if each_conditional.execute_command:
                    #################################
                    #        DANGEROUS CODE         #
                    #################################
                    # This code is not secure at all#
                    # and could cause serious       #
                    # damage to your software and   #
                    # hardware.                     #
                    #################################

                    # TODO: SECURITY: FIX THIS This runs arbitrary as ROOT
                    #       Make sure this works (currently untested)

                    message += "Execute '{}'. ".format(each_conditional.execute_command)
                    pass
                    # p = subprocess.Popen(each_conditional.execute_command, shell=True,
                    #                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # output, errors = p.communicate()
                    # self.logger.debug("[Relay Conditional {} ({})] "
                    #                   "Execute command: {} "
                    #                   "Command output: {} "
                    #                   "Command errors: {}".format(each_conditional.id,
                    #                                               each_conditional.name,
                    #                                               each_conditional.execute_command,
                    #                                               output, errors))

                
                      
                    else:
                        self.logger.debug("[Relay Conditional {}] True: "
                                          "{:.0f} seconds left to be "
                                          "allowed to email again.".format(
                                          each_cond.id,
                                          (self.smtp_wait_time-time.time())))

                

                if (each_conditional.do_relay_id or
                        each_conditional.execute_command:
                    self.logger.debug("{}".format(message))


    def all_relays_initialize(self, relays):
        for each_relay in relays:
            self.relay_id[each_relay.id] = each_relay.id
            self.relay_name[each_relay.id] = each_relay.name
            self.relay_pin[each_relay.id] = each_relay.pin
            self.relay_amps[each_relay.id] = each_relay.amps
            self.relay_trigger[each_relay.id] = each_relay.trigger
            self.relay_start_state[each_relay.id] = each_relay.start_state
            self.relay_on_until[each_relay.id] = datetime.datetime.now()
            self.relay_last_duration[each_relay.id] = 0
            self.relay_on_duration[each_relay.id] = False
            self.setup_pin(each_relay.pin)
            self.logger.debug("[Relay] {} ({}) Initialized".format(each_relay.id, each_relay.name))


    def all_relays_off(self):
        """Turn all relays off"""
        for each_relay_id in self.relay_id:
            self.relay_on_off(each_relay_id, 'off', 0, False)


    def all_relays_on(self):
        """Turn all relays on that are set to be on at startup"""
        for each_relay_id in self.relay_id:
            if self.relay_start_state[each_relay_id]:
                self.relay_on_off(each_relay_id, 'on', 0, False)


    def add_mod_relay(self, relay_id, do_setup_pin=False):
        """
        Add or modify local dictionary of relay settings form SQL database

        When a relay is added or modified while the relay controller is
        running, these local variables need to also be modified to
        maintain consistency between the SQL database and running controller.

        :return: 0 for success, 1 for fail, with success for fail message
        :rtype: int, str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        :param do_setup_pin: If True, initialize GPIO (when adding new relay)
        :type do_setup_pin: bool
        """
        try:
            with session_scope(MYCODO_DB_PATH) as new_session:
                relay = new_session.query(Relay).filter(
                    Relay.id == relay_id).first()
                self.relay_id[relay_id] = relay.id
                self.relay_name[relay_id] = relay.name
                self.relay_pin[relay_id] = relay.pin
                self.relay_amps[relay_id] = relay.amps
                self.relay_trigger[relay_id] = relay.trigger
                self.relay_start_state[relay_id] = relay.start_state
                self.relay_on_until[relay_id] = datetime.datetime.now()
                self.relay_last_duration[relay_id] = 0
                self.relay_on_duration[relay_id] = False
                message = "[Relay] Relay {} ({}) ".format(
                    self.relay_id[relay_id], self.relay_name[relay_id])
                if not do_setup_pin:
                    message += "added"
                else:
                    self.setup_pin(relay.pin)
                    message += "initiliazed"
                self.logger.debug(message)
            return 0, "success"
        except Exception as msg:
            return 1, "Error: {}".format(msg)


    def del_relay(self, relay_id):
        """
        Delete local variables

        The controller local variables must match the SQL database settings.
        Therefore, this is called when a relay has been removed from the SQL
        database.

        :return: 0 for success, 1 for fail (with error message)
        :rtype: int, str

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        try:
            self.logger.debug("[Relay] Relay {} ({}) Deleted.".format(
                self.relay_id[relay_id], self.relay_name[relay_id]))
            # Ensure relay is off before removing it, to prevent
            # it from being stuck on
            self.relay_on_off(relay_id, 'off')

            self.relay_id.pop(relay_id, None)
            self.relay_name.pop(relay_id, None)
            self.relay_pin.pop(relay_id, None)
            self.relay_amps.pop(relay_id, None)
            self.relay_trigger.pop(relay_id, None)
            self.relay_start_state.pop(relay_id, None)
            self.relay_on_until.pop(relay_id, None)
            self.relay_last_duration.pop(relay_id, None)
            self.relay_on_duration.pop(relay_id, None)
            return 0, "success"
        except Exception as msg:
            return 1, "Error: {}".format(msg)


    def current_amp_load(self):
        """
        Calculate the current amp draw from all the devices connected to
        all relays currently on.

        :return: total amerage draw
        :rtype: float
        """
        amp_load = 0.0
        for each_relay_id, each_relay_amps in self.relay_amps.iteritems():
            if self.is_on(each_relay_id):
                amp_load += each_relay_amps
        return amp_load


    def setup_pin(self, pin):
        """
        Setup pin for this relay
        :rtype: None
        """
        # TODO add some extra checks here.  Maybe verify BCM?
        GPIO.setup(pin, GPIO.OUT)


    def is_on(self, relay_id):
        """
        :return: Whether the relay is currently "ON"
        :rtype: bool

        :param relay_id: Unique ID for each relay
        :type relay_id: str
        """
        return self.relay_trigger[relay_id] == GPIO.input(self.relay_pin[relay_id])


    def _is_setup(self):
        """
        This function checks to see if the GPIO pin is setup and ready
        to use. This is for safety and to make sure we don't blow anything.

        # TODO Make it do that.

        :return: Is it safe to manipulate this relay?
        :rtype: bool
        """
        return True


    def isRunning(self):
        return self.running


    def stopController(self):
        """Signal to stop the controller"""
        self.thread_shutdown_timer = timeit.default_timer()
        self.running = False