import sys
import logging
import argparse
from readtemp import ReadTemp
from daemon import Daemon


class TempDaemon(Daemon):
    temp = None

    def __init__(self, pidfile):
        Daemon.__init__(self, pidfile)
        self.temp = ReadTemp()

    def run(self):
        self.temp.start()
        
    def stop(self):
        self.temp.join()
        super(TempDaemon, self).stop()


def main():
    argv = sys.argv
    daemon = TempDaemon('/tmp/temp-daemon.pid')
    parser = argparse.ArgumentParser(prog="readmain")
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
    logging.basicConfig(level=args.loglevel, file='temp.log')
    if args.action == "start":
        daemon.start()
    elif args.action == "stop":
        daemon.stop()
    elif args.action == "restart":
        daemon.restart()


if __name__ == "__main__":
    sys.exit(main())