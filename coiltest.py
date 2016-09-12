from datetime import datetime, timedelta
from time import sleep
import logging
from logging import handlers

class Coilstring:
    REST = 0
    ACTIVE = 1

    def __init__(self, bday=datetime.utcnow()):
        self.logger = logging.getLogger(__name__)
        self.bday = bday  # datetime
        self.rest_periods = []  # durations
        self.active_periods = []  # durations
        self.last_state = Coilstring.ACTIVE
        self.last_event_start = datetime.utcnow()

    def rest(self):
        self.logger.info("Resting!")
        if self.last_state == Coilstring.REST:
            self.logger.warning("Already in rest state!")
            pass  # REST to REST has no effect
        self.last_state = Coilstring.REST
        now = datetime.utcnow()
        self.active_periods.append(now - self.last_event_start)
        self.last_event_start = now

    def activate(self):
        self.logger.info("Activating!")
        if self.last_state == Coilstring.ACTIVE:
            self.logger.warning("Already in active state!")
            pass  # ACTIVE to ACTIVE has no effect
        self.last_state = Coilstring.ACTIVE
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
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cs = Coilstring()
    cs.activate()  # no-op...already active
    cs.rest()
    sleep(10)  # rest 10
    cs.activate()
    sleep(10)
    print "RESTed for {}% of lifetime".format(cs.report_rest_percentage())

