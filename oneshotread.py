import sys
import argparse
from picreader import PICReader
from readtemp import ReadTemp
from datetime import datetime
import logging.handlers as handlers
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
    handler = handlers.RotatingFileHandler(
        "/usr/local/fdl/oneshot_log.txt", maxBytes=10485760, backupCount=5)
    logger = logging.getLogger('root')
    logger.addHandler(handler)
    logger.setLevel(args.loglevel)
    try:
        reader = PICReader()
        rtemp = ReadTemp()
        now = datetime.now()
        picTime = now.strftime("%Y-%m-%d %H:%M:%S")
        c1Reading, c2Reading, t1Reading, t2Reading, v1Reading, v2Reading, v3Reading = reader.read_data(rtemp)
        collectedData = picTime + "," + reader.getDeviceId() + "," + \
                        str(v1Reading) + "," + str(v2Reading) + "," + str(v3Reading) + "," + \
                        str(c1Reading) + "," + str(c2Reading) + "," + \
                        str(t1Reading) + "," + str(t2Reading) + "\n"
        print collectedData

    except Exception, e:
        logger.critical("Exception caught in main %s" % e)


if __name__ == "__main__":
    sys.exit(main())
