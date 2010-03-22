import time, os, sys, sched, subprocess, re, signal, traceback
import gobject, dbus, dbus.service, dbus.mainloop.glib 
import multiprocessing
import logging,  logging.config,  logging.handlers

from RILCommonModules.RILSetup import *
from CentralizedTaskServer.data_manager import *

logger = logging.getLogger("EpcLogger")

#ROBOTS_PATH_CFG_FILE = "robots_dbus_path.conf"

def updater_interrupt_handler(state):
    global datamgr_proxy
    print "New server state requested %s" %(state)
    try:
        datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE] = str(state)
        datamgr_proxy.mTaskUpdaterStateUpdated.set()
        print "Req. datamgr_proxy.mTaskUpdaterState: "
        print datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE]
    except Exception, e:
        print "Err in updater_interrupt_handler():", e

def save_task_status(robotid,  taskid):
    global datamgr_proxy
    print "Robot id %d" %robotid
    try:
        robotid = eval(str(robotid))
        taskid = eval(str(taskid))
        datamgr_proxy.mTaskWorkers[robotid] = taskid
        print "Save Task Status:"
        print datamgr_proxy.mTaskWorkers
    except Exception, e:
        print "Err in save_task_status():", e

def robot_signal_handler(sig,  robotid,  taskid):
    print "Caught signal  %s (in robot signal handler) "  %(sig)
    print "Robot: %i, engaged in %i" %(robotid, taskid)  
    save_task_status(robotid,  taskid)

def main_loop():
    try:
        loop = gobject.MainLoop()
        loop.run()
    except (KeyboardInterrupt, SystemExit):
        print "User requested exit... shutting down now"
        pass
        sys.exit(0)

def listener_main(data_mgr,  dbus_iface= DBUS_IFACE_EPUCK,\
        dbus_path = DBUS_PATH_BASE,  robots_cfg="", \
        sig= SIG_TASK_STATUS,  delay=1):
    global datamgr_proxy,  robot_signal, transition_signal
    datamgr_proxy = data_mgr
    print "@RecvrMain: Task workers"
    print datamgr_proxy.mTaskWorkers
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    # prepare dbus_paths
    #print "Robot paths %i"  %robots
    dbus_paths = []
    f = open(robots_cfg, 'r')
    for line in f.readlines():
        if line.endswith('\n'):
            line = line[:-1]
        if(line[0] == '/'):
            dbus_paths.append(line)
    f.close()
    try:
        for p in dbus_paths:
            bus.add_signal_receiver(robot_signal_handler, dbus_interface =\
                dbus_iface, path= p,  signal_name = sig)
        
        # catch interrupt signals for task info updater
        bus.add_signal_receiver(updater_interrupt_handler, dbus_interface =\
                DBUS_IFACE_TASK_SERVER, path= DBUS_PATH_TASK_SERVER,  signal_name = SIG_TASK_INFO_UPDTAER )
        main_loop()
    except dbus.DBusException:
        traceback.print_exc()
        sys.exit(1)
