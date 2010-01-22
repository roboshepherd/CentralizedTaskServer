#!/usr/bin/python
import multiprocessing
import logging, logging.config, logging.handlers
import time
import sys

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("EpcLogger")
multiprocessing.log_to_stderr(logging.DEBUG)

from RILCommonModules.RILSetup import *
from data_manager import *
import dbus_emitter
import dbus_listener
import taskinfo_updater

def main():
        logging.debug("--- Start EPC---")
        updater .start()
        emitter.start()
        listener.start()
        # Ending....
        time.sleep(3)
        updater.join()
        emitter.join()
        listener.join()
        logging.debug("--- End EPC---")


if __name__ == '__main__':
    # arg parsing
    numargs = len(sys.argv) - 1
    if numargs > 1 or numargs < 1:
        print "usage:" + sys.argv[0] + "<robot-path cfg_file>"
        sys.exit(1) 
    else:
        robots_cfg = sys.argv[1]
    # init stuff
	dm = DataManager()
    sig1 = SIG_TASK_INFO
    sig2 = SIG_TASK_STATUS
    delay = TASK_INFO_EMIT_FREQ # interval between signals

    updater = multiprocessing.Process(\
        target=taskinfo_updater. updater_main,\
        name="TaskInfoUpdater",  args=(dm, ))
    emitter= multiprocessing.Process(\
        target= dbus_emitter.emitter_main,\
        name="TaskInfoEmitter",\
        args=(dm,  DBUS_IFACE_TASK_SERVER,\
        DBUS_PATH_TASK_SERVER, sig1,   delay,  ))
    listener = multiprocessing.Process(\
        target=dbus_listener.listener_main,\
        name="TaskStatusReceiver",\
        args=(dm,  DBUS_IFACE_EPUCK, DBUS_PATH_BASE, robots_cfg,\
            sig2,   delay))
    main()   




