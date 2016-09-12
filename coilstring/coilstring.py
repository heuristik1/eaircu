import logging
from ConfigParser import SafeConfigParser
import pymongo
from datetime import datetime, timedelta
import threading
from time import sleep


class StopableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StopableThread, self).__init__(*args, **kwargs)
        self._stopper = threading.Event()

    def stop(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.isSet()


class CoilString:
    REST = 0
    ACTIVE = 1

    def __init__(self, device, string, control_pin, status_pin, bday=datetime.utcnow(), config_file='settings.ini'):
        self._logger = logging.getLogger(__name__)
        self._bday = bday  # datetime
        self._device = device  # device identifier
        self._string = string  # string identifier
        self._last_state = CoilString.ACTIVE
        self._config = SafeConfigParser()
        self._config.read(config_file)
        self._db = self._connect()
        self._add_stop_entry()  # try and add a stop entry in case we rebooted while in rest
        self._rest_thread = None
        self.control_pin = control_pin
        self.status_pin = status_pin

    def _connect(self):
        """
        Connects to the mongo database specified in the configuration file
        :return:
        """
        conn = pymongo.MongoClient(self._config.get('mongodb', 'host'), self._config.getint('mongodb', 'port'))
        db = conn[self._config.get('mongodb', 'db')]
        return db[self._config.get('mongodb', 'collection')]

    def _run_rest(self, rest_seconds, resolution, activate_callback):
        """
        Thread that runs during a strings rest period. The thread will run for rest_seconds, and
        write to the database every resolution seconds. Once the thread exits, a stop record will be written,
        and the activate_callback will be called with a reference to the CoilString object
        :param rest_seconds:
        :param resolution:
        :param activate_callback:
        :return:
        """
        try:
            d_id = self._add_start_entry()
            if d_id:
                rest_until = datetime.utcnow() + timedelta(seconds=rest_seconds)
                next_write = datetime.utcnow() + timedelta(seconds=resolution)
                while datetime.utcnow() < rest_until:
                    # update rest period
                    if datetime.utcnow() > next_write:
                        self._logger.info("Updating duration for {} by {}".format(self.name, resolution))
                        update = {"$inc": {'duration': resolution}}
                        self._db.find_one_and_update({'_id': d_id}, update)
                        next_write = datetime.utcnow() + timedelta(seconds=resolution)
                    sleep(1)
        except Exception as e:
            self._logger.error("Rest thread interrupted {}".format(e.message))
        finally:
            now = datetime.utcnow()
            remainder = resolution - (next_write - now).total_seconds()
            self._logger.info("Adding remainder of duration for {} by {}".format(self.name, remainder))
            update = {"$inc": {'duration': remainder}}
            self._db.find_one_and_update({'_id': d_id}, update)
            self._add_stop_entry()
            self._last_state = CoilString.ACTIVE  # set to active when done
            if activate_callback:  # call user active func
                activate_callback(self)

    def _add_start_entry(self):
        """
        Adds a start entry to the database for this device and string
        :return: Mongo document id
        """
        return self._db.insert(
            {'device': self._device, 'string': self._string, 'start': datetime.utcnow(), 'duration': 0})

    def _add_stop_entry(self):
        """
        Updates an existing start entry for the given device and string with a stop entry, and duration
        :return: Updated mongo document
        """
        entry = self._db.find({'device': self._device, 'string': self._string}).sort('start', pymongo.DESCENDING).limit(
            1)
        try:
            data = entry.next()
            if data.get('stop', None) is None:
                now = datetime.utcnow()
                update = {"$set": {'stop': now}}
                d_id = data.get('_id')
                return self._db.find_one_and_update({'_id': d_id}, update, return_document=pymongo.ReturnDocument.AFTER)
            else:
                self._logger.warning("No start entry to stop!!")
        except Exception:
            pass

    @property
    def state(self):
        return self._last_state

    @property
    def name(self):
        return self._string

    @property
    def control_pin(self):
        return self._control_pin

    @property
    def status_pin(self):
        return self._status_pin
    
    @property
    def bday(self):
        """
        Returns the strings birthday
        :return: datetime
        """
        return self._bday

    @property
    def total_seconds_rested(self):
        """
        Total lifetime seconds rested for this device string
        :return: integer
        """
        pipeline = [
            {"$match": {'device': self._device, 'string': self._string}},
            {"$group": {"_id": '$device', 'total': {"$sum": '$duration'}}}
        ]
        results = list(self._db.aggregate(pipeline))
        try:
            return results[0].get('total', None)
        except Exception as e:
            self._logger.warning("No duration results found {}".format(e.message))
            return 0

    def rest(self, seconds_to_rest, resolution, rest_func=None, active_func=None):
        """
        Places the string into a rest state. Will optionally execute a user supplied function
        :param func:
        :return: None
        """
        self._logger.info("Resting string {}".format(self.name))
        if self._last_state == CoilString.REST:
            self._logger.warning("Already in rest state!")
            return  # REST to REST has no effect
        try:
            if rest_func:
                rest_func(self)  # execute user function
            self._last_state = CoilString.REST
            self._rest_thread = StopableThread(target=self._run_rest, args=(seconds_to_rest, resolution, active_func)).start()
        except Exception as e:
            self._logger.error("Error trying to initiate REST state {}".format(e.message))

    def report_rest_percentage(self):
        """
        Returns the percentage of the strings lifetime spent in a resting state
        :return: float
        """
        self._logger.info("Running report for device {}".format(self.name))
        tot_time_since_bday = (datetime.utcnow() - self.bday).total_seconds()  # duration
        time_at_rest = self.total_seconds_rested
        return time_at_rest / float(tot_time_since_bday) * 100

