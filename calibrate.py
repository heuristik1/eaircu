#!/usr/bin/python
from picreader import PICReader
import logging

# only run if it is main
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename="/usr/local/fdl/fdl_calibration.log", level=logging.INFO)
    try:
        preader = PICReader()
        preader.calibrate()
    except Exception, e:
        logger.critical("Exception caught in main %s" % e)

