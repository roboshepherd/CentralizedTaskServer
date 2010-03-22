import multiprocessing
import logging, logging.config
import time
import copy
import random
import sys

from RILCommonModules.RILSetup import  *
from RILCommonModules.task_info import *
from CentralizedTaskServer.data_manager import *

logger = logging.getLogger("EpcLogger")

#  Setup Initial Task Info 
# Fix: Change it to reading from a config file
ti = TaskInfo()
task1 = ShopTask(id=1,  x=950,  y=840)
task2 = ShopTask(id=2,  x=1797,  y=713)
task3 = ShopTask(id=3,  x=1848,  y=1713)
task4 = ShopTask(id=4,  x=535,  y=1596)
#task5 = ShopTask(id=5,  x=2431,  y=2264)
#task6 = ShopTask(id=6,  x=1042,  y=1973)
ti.AddTaskInfo(1,  task1.Info()) 
ti.AddTaskInfo(2,  task2.Info())
ti.AddTaskInfo(3,  task3.Info())
ti.AddTaskInfo(4,  task4.Info()) 
#ti.AddTaskInfo(5,  task5.Info())
#ti.AddTaskInfo(6,  task6.Info())

taskinfo = copy.deepcopy(ti.all)

# LogFiles
TASK_URGENCY_LOG = "UrgencyLog-" +\
    time.strftime("%Y%b%d-%H%M%S", time.gmtime()) + ".txt"
TASK_WORKERS_LOG = "WorkersLog-" +\
    time.strftime("%Y%b%d-%H%M%S", time.gmtime()) + ".txt"
urgency_log = ''
workers_log = ''
updater_step = 0

def TimeStampLogMsg():
    global   urgency_log,  workers_log, updater_step
    updater_step = updater_step + 1
    urgency_log = str(time.time()) + "; " +\
        time.strftime("%H:%M:%S", time.gmtime())\
        + "; " + str(updater_step)
    workers_log = str(time.time()) + "; " +\
        time.strftime("%H:%M:%S", time.gmtime())\
        + "; " + str(updater_step)
    
def PrepareLogMsg(urgency,  workers):
    global   urgency_log,  workers_log
    urg_msg = "; " + str(urgency) 
    urgency_log += urg_msg
    workers_msg = "; " + str(workers)
    workers_log += workers_msg

def GetTaskUrgency(taskid,  urg):
    global  datamgr_proxy
    # urgency 0~1
    urgency = urg
    workers = 0
    worker_list = []
    try:
        worker_dict = datamgr_proxy.mTaskWorkers
        for k, v in worker_dict.items():
            rid = eval(str(k))
            tid = eval(str(v))
            if(tid == taskid):
                worker_list.append(rid)
        logger.info("Task %d Workers searched", taskid)
        print "Task %d Workers: %s" %taskid
        print worker_list
    except Exception, e:
        logger.warn("@GetTaskUrgency(): worker count unavailable %s", e)
    workers= len(worker_list)
    if workers > 0:
        urgency = urg - workers * DELTA_TASK_URGENCY_DEC
    elif workers == 0:
        urgency = urg +  DELTA_TASK_URGENCY_INC
    else:
        logger.warn("worker count not updated")
    if urgency > 1:
        urgency = 1
    elif urgency < 0:
        urgency = 0
   # Save data into log
    PrepareLogMsg(urgency,  workers)
    logger.info("task %d, urgency:%f", taskid, urgency)
    print "task %d, urgency:%f" %(taskid, urgency)
    return urgency

def UpdateTaskInfo():
    global  datamgr_proxy
    #print "DMP ti2 %s" %id(datamgr_proxy.mTaskInfo)
    # Put TimeStamp on logs
    TimeStampLogMsg()
    #try:
    for taskid, ti  in  datamgr_proxy.mTaskInfo.items():
        urg= ti[TASK_INFO_URGENCY] 
        ti[TASK_INFO_URGENCY] =   GetTaskUrgency(taskid,  urg)
        datamgr_proxy.mTaskInfo[taskid] = ti
            #print task
    #except Exception, e:
        #print "Err @UpdateTaskInfo(): %s", e
        datamgr_proxy.mTaskInfoAvailable.set()
    #print "Updated ti %s" %datamgr_proxy.mTaskInfo

def InitLogFiles():
    f1 = open(TASK_URGENCY_LOG,  "w")
    f2 = open(TASK_WORKERS_LOG,  "w")
    header = "##;##"
    header += "Time; Time(HH:MM:SS); Step#"
    for x in xrange(1, MAX_SHOPTASK+1):
        header += "; "
        header += "Task"
        header += str(x)
    header += "\n"
    f1.writelines(header)
    f2.writelines(header)
    f1.close()
    f2.close()
    
def AppendMsg(file,  msg):
    f = open(file,  'a')
    f.write(msg)
    f.write('\n')
    f.close()
    
def UpdateLogFiles():
    global   urgency_log,  workers_log
    AppendMsg(TASK_URGENCY_LOG, urgency_log )
    AppendMsg(TASK_WORKERS_LOG,  workers_log)
    # reset log msg
    urgency_log = ''
    workers_log = ''

def updater_main(datamgr):
    InitLogFiles()
    global datamgr_proxy,  taskurg
    datamgr_proxy = datamgr
    #print "DMP ti1 %s" %id(datamgr_proxy.mTaskInfo)
    taskurg = INIT_TASK_URGENCY
    for k,  v in taskinfo.iteritems():
        datamgr_proxy.mTaskInfo[k] =v
    print "@updater:"
    print datamgr_proxy.mTaskInfo
    datamgr_proxy.mTaskInfoAvailable.set()
    datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE] =\
        TASK_INFO_UPDATER_RUN
    
    try:
        while True:
            state =  str(datamgr_proxy.mTaskUpdaterState[TASK_INFO_UPDTAER_STATE])
            datamgr_proxy.mTaskUpdaterStateUpdated.clear()
            print "@TaskInfoUpdater:"
            if state == TASK_INFO_UPDATER_RUN:            
                UpdateTaskInfo()
                UpdateLogFiles()
                time.sleep(TASK_INFO_UPDATE_FREQ)
                print "\t TI updated."
            elif state == TASK_INFO_UPDATER_PAUSE:
                datamgr_proxy.mTaskUpdaterStateUpdated.wait()
                print "\t updater waiting..."
            
    except (KeyboardInterrupt, SystemExit):
            print "User requested exit... TaskInfoUpdater shutting down now"
            sys.exit(0)
        

