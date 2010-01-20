import multiprocessing
import logging, logging.config
import time
import copy
import random

from RILCommonModules.RILSetup import  *
from RILCommonModules.task_info import *
from data_manager import *

logging.config.fileConfig("logging.conf")
#create logger
logger = logging.getLogger("EpcLogger")

#  Setup Initial Task Info 
# Fix: Change it to reading from a config file
ti = TaskInfo()
task1 = ShopTask(id=1,  x=900,  y=1100)
task2 = ShopTask(id=2,  x=1500,  y=1200)
task3 = ShopTask(id=3,  x=2500,  y=1800)
ti.AddTaskInfo(1,  task1.Info()) 
ti.AddTaskInfo(2,  task2.Info())
ti.AddTaskInfo(3,  task3.Info())
taskinfo = copy.deepcopy(ti.all)

# LogFiles
TASK_URGENCY_LOG = "TaskUrgencyLog-" +\
    time.strftime("%Y%b%H%M%S", time.gmtime()) + ".txt"
TASK_WORKERS_LOG = "TaskWorkersLog-" +\
    time.strftime("%Y%b%H%M%S", time.gmtime()) + ".txt"
urgency_log = ''
workers_log = ''

def TimeStampLogMsg():
    global   urgency_log,  workers_log
    urgency_log = str(int(time.time()))
    workers_log = str(int(time.time()))
    
def PrepareLogMsg(urgency,  workers):
    global   urgency_log,  workers_log
    urg_msg = ";" + str(urgency) 
    urgency_log += urg_msg
    workers_msg = ";" + str(workers)
    workers_log += workers_msg

def GetTaskUrgency(taskid,  urg):
        global  datamgr_proxy
        workers = len(datamgr_proxy.mTaskWorkers[taskid])
        print "Task %d Workers:" %taskid
        print  datamgr_proxy.mTaskWorkers[taskid]
        if workers > 0:
            urgency = urg - workers * DELTA_TASK_URGENCY 
        else:
            urgency = urg +  DELTA_TASK_URGENCY
       # Save data into log
        PrepareLogMsg(urgency,  workers)
        return urgency

def UpdateTaskInfo():
        global  datamgr_proxy
        #print "DMP ti2 %s" %id(datamgr_proxy.mTaskInfo)
        # Put TimeStamp on logs
        TimeStampLogMsg()
        for taskid, ti  in  datamgr_proxy.mTaskInfo.items():
            urg= ti[TASK_INFO_URGENCY] 
            ti[TASK_INFO_URGENCY] =   GetTaskUrgency(taskid,  urg)
            datamgr_proxy.mTaskInfo[taskid] = ti
            #print task
        datamgr_proxy.mTaskInfoAvailable.set() 
        print "Updated ti %s" %datamgr_proxy.mTaskInfo

def InitLogFiles():
    f1 = open(TASK_URGENCY_LOG,  "w")
    f2 = open(TASK_WORKERS_LOG,  "w")
    header = "TimeStamp"
    for x in xrange(MAX_SHOPTASK+1):
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
        # simulating task worker signal recv.
        datamgr_proxy.mTaskWorkers[k] = [random.randint(1, 8)] * (k - 1)
    print "@updater:"
    print datamgr_proxy.mTaskInfo
    datamgr_proxy.mTaskInfoAvailable.set()
    while True:
        print "@updater:"
        UpdateTaskInfo()
        UpdateLogFiles()
        time.sleep(2)
