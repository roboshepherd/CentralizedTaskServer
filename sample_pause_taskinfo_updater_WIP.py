#!/usr/bin/env python
import time, os, sys, sched, subprocess, re, signal, traceback
import gobject, dbus, dbus.service, dbus.mainloop.glib 

from RILCommonModules.RILSetup import *

class TaskInfoUpdaterInterruptor(dbus.service.Object):
    def __init__(self, object_path):
        dbus.service.Object.__init__(self, dbus.SessionBus(), object_path)
    @dbus.service.signal(dbus_interface= DBUS_IFACE_TASK_SERVER,\
            signature='s')
    def UpdateState(self, state):
        # The signal is emitted when this method exits
        print "TaskInfoUpdater state signal: %s  " % (state)
        #print taskinfo
    def Exit(self):
        global loop
        loop.quit()

##Emit DBus-Signal
#def emit_interrupt_signal(state):
        #print "At emit_interrupt_signal():"        
        #global datamgr_proxy,  interrupt_signal       
        #interrupt_signal.UpdateState(TASK_INFO_UPDATER_PAUSE)

def emitter_main(dbus_iface= DBUS_IFACE_TASK_SERVER,\
            dbus_path = DBUS_PATH_TASK_SERVER, \
            sig1= SIG_TASK_INFO_UPDTAER):
        global interrupt_signal,  loop
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        session_bus = dbus.SessionBus()        
        try:
            name = dbus.service.BusName(dbus_iface, session_bus)
            interrupt_signal = TaskInfoUpdaterInterruptor(dbus_path)
            loop = gobject.MainLoop()
            print "Running TaskInfoUpdaterInterruptor."
        except dbus.DBusException:
            traceback.print_exc()
            sys.exit(1)
        try:
                ##Emit DBus-Signal
                interrupt_signal.UpdateState(TASK_INFO_UPDATER_PAUSE)
                loop.run()
        except (KeyboardInterrupt, dbus.DBusException, SystemExit):
                print "User requested exit... shutting down now"
                interrupt_signal.Exit()
                pass
                sys.exit(0)
