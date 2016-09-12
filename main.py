import sys
import argparse
from picreader import PICReader
#from tempreader import TEMPReader
import log
import logging

def main():
    argv = sys.argv
    parser = argparse.ArgumentParser(prog="main")
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    args = parser.parse_args()
    logger = log.setup_custom_logger('root', args.loglevel)
    try:
        reader1 = PICReader()
        reader1.run()
    except Exception, e:
        logger.critical("Exception caught in main %s" % e)
    #try:
    #    reader2 = TEMPReader()
    #    reader2.run()
    #except Exception, e:
    #    logger.critical("Exception caught in main %s" % e)


if __name__ == "__main__":
    sys.exit(main())
