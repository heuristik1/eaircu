import sys
import argparse
from picreader import PICReader
from daemon import Daemon
import logging
import log

logger = None

class PICDaemon(Daemon):
    reader = None

    def __init__(self, pidfile):
        Daemon.__init__(self, pidfile)
        self.reader = PICReader()

    def run(self):
        try:
            self.reader.run()
        except Exception, e:
            logger.critical("Exception caught in run: %s" % e)
        finally:
            self.reader.closeSPI()


def main():
    argv = sys.argv
    parser = argparse.ArgumentParser(prog="main")
    parser.add_argument('action', choices=['start', 'stop', 'restart'])
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
    daemon = PICDaemon('/tmp/temp-daemon.pid')
    if args.action == "start":
        daemon.start()
    elif args.action == "stop":
        daemon.stop()
    elif args.action == "restart":
        daemon.restart()


if __name__ == "__main__":
    sys.exit(main())