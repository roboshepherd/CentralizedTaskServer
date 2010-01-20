import time, os, sys, sched, subprocess, re, signal, traceback
import gobject, dbus, dbus.service, dbus.mainloop.glib 
import multiprocessing
import logging,  logging.config,  logging.handlers

from RILCommonModules.RILSetup import *
from data_manager import *

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("EpcLogger")

def save_task_status(robotid,  taskid):
    global datamgr_proxy
    try:
        datamgr_proxy.mTaskWorkers[taskid].append(robotid)
        print datdatamgr_proxy.mTaskWorkers
    except:
       print "Err in save_task_status()"

def robot_signal_handler(sig,  robotid,  taskid):
    print "Caught signal  %s (in taskinfo signal handler) "  %(sig)
    #print "Val: ",  val
    save_task_status(robotid,  taskid)

def main_loop():
    try:
        loop = gobject.MainLoop()
        loop.run()
    except (KeyboardInterrupt, SystemExit):
        print "User requested exit... shutting down now"
        pass
        sys.exit(0)

def receiver_main(data_mgr,  dbus_iface= DBUS_IFACE_EPUCK,\
        dbus_path = DBUS_PATH_BASE,  robots=1, \
        sig= SIG_TASK_STATUS,  delay=3):
    global datamgr_proxy,  robot_signal
    datamgr_proxy = data_mgr
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    # prepare dbus_paths
    print "Robot paths %i"  %robots
    dbus_paths = []
    for x in range(1, robots+1):
        p = dbus_path + str(x)
        dbus_paths.append(p)
    try:
        for x in range(robots):
            bus.add_signal_receiver(robot_signal_handler, dbus_interface =\
                                 dbus_iface, path= dbus_paths[x],  signal_name = sig)
        main_loop()
    except dbus.DBusException:
        traceback.print_exc()
        sys.exit(1)
