import logging
import logging.config
import yaml
import os
from datetime import datetime
from ConfigParser import SafeConfigParser
from time import sleep
from coilstring.coilstring import CoilString
import RPi.GPIO as GPIO

def setup_logging(default_path='logging.yml', default_level=logging.INFO, env_key='LOG_CFG'):
    """
    Setup logging configuration
    :param default_path:
    :param default_level:
    :param env_key:
    :return:
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def rest_callback(coilstring):
    """
    Callback for placing string into resting state. This is a good place
    to send gpio commands
    :param coilstring:  The CoilString object that was rested
    :return:
    """
    GPIO.output(coilstring.control_pin,GPIO.HIGH)
    # logger = logging.getLogger(__ name__)
    # logger.info("{} was placed into a rest state".format(coilstring.name))


def active_callback(coilstring):
    """
    Callback for placing string into active state. This is a good place
    to send gpio commands
    :param coilstring: The CoilString object that was activated
    :return:
    """
    GPIO.output(coilstring.control_pin,GPIO.LOW)

    # logger = logging.getLogger(__name__)
    # logger.info("{} was placed into an active state".format(coilstring.name))


def get_candidate_coil_string(coil_dict):
    """
    Given a dictionary of 'string name'->CoilString pairs, return the coilstring with the
    least rested time
    :param coil_dict:
    :return: CoilString object
    """
    # determine which string has least amount of rest time, and place into rest state
    rested_list = sorted([(x.name, x.report_rest_percentage()) for x in coil_dict.values()], key=lambda data: data[1])
    if rested_list:
        return string_dict[rested_list[0][0]]


def seconds_to_rest(coilstring):
    """
    Given a CoilString object, determine the amount of seconds to rest in order to reach 20% of lifetime
    :param coilstring: CoilString object
    :return: float
    """
    twenty_percent = (datetime.utcnow() - coilstring.bday).total_seconds() * .2
    return twenty_percent - coilstring.total_seconds_rested


def all_active(coil_dict):
    for x in coil_dict.values():
        if x.state == CoilString.REST:
            return False
    return True


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    GPIO.setmode(GPIO.BCM)

    # allstatpins = [5,4,18,24]
    # allcontrolpins = [19,20,21,26]

    string_dict = {}  # dictionary to hold our coilstrings

    # read config file and construct defined strings
    parser = SafeConfigParser()
    parser.read('settings.ini')
    device = parser.get('device', 'name')  # grab device name
    resolution = parser.getint('device', 'resolution')
    allcontrolpins = []
    strings = parser.items('strings')  # setup our coilstrings
    for string, bday in strings:

        bday_split = bday.split(',')[0]
        control_pin_split = int(bday.split(',')[1])
        status_pin_split = bday.split(',')[2]

        string_dict[string] = CoilString(device, string, control_pin_split, status_pin_split, datetime.strptime(bday_split, '%Y-%m-%d %H:%M:%S'))

        # print "Control Pin : %d" % control_pin_split

        allcontrolpins.append(control_pin_split)

    GPIO.setup(allcontrolpins, GPIO.OUT)
    GPIO.output(allcontrolpins, GPIO.LOW)

    while True:
        if not all_active(string_dict):
            sleep(1)
            continue
        # determine which string has least amount of rest time, and place into rest state
        coil_in_rest = get_candidate_coil_string(string_dict)
        if coil_in_rest:
            rest_for = seconds_to_rest(coil_in_rest)
            logger.info(
                "Would place string {} in a rest state for {} seconds ".format(coil_in_rest.name, rest_for))
            #rest_for = 60  # TODO REMOVE BEFORE DEPLOY TESTING ONLY
            coil_in_rest.rest(rest_for, resolution, rest_callback, active_callback)
        else:
            logger.error("Unable to find candidate CoilString to rest")
        sleep(1)

