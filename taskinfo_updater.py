import multiprocessing
import logging, logging.config
import time
import copy
import random
import sys

from RILCommonModules.RILSetup import  *
from RILCommonModules.LiveGraph import *
from RILCommonModules.task_info import *
from CentralizedTaskServer.data_manager import *

logger = logging.getLogger("EpcLogger")

#  Setup Initial Task Info 
# Fix: Change it to reading from a config file
ti = TaskInfo()
task1 = ShopTask(id=1,  x=2032,  y=555)
task2 = ShopTask(id=2,  x=2720,  y=877)
task3 = ShopTask(id=3,  x=3502,  y=865)
task4 = ShopTask(id=4,  x=3394,  y=1514)
task5 = ShopTask(id=5,  x=2735,  y=1661)
task6 = ShopTask(id=6,  x=2703,  y=2415)
task7 = ShopTask(id=7,  x=1605,  y=1901)
task8 = ShopTask(id=8,  x=1617,  y=1122)
ti.AddTaskInfo(1,  task1.Info()) 
ti.AddTaskInfo(2,  task2.Info())
ti.AddTaskInfo(3,  task3.Info())
ti.AddTaskInfo(4,  task4.Info()) 
ti.AddTaskInfo(5,  task5.Info())
ti.AddTaskInfo(6,  task6.Info())
ti.AddTaskInfo(7,  task7.Info())
ti.AddTaskInfo(8,  task8.Info())

taskinfo = copy.deepcopy(ti.all)

# log robot workers status
#---------------------Log recevd. signal/data  ---------------------
class StatusLogger():
    def __init__(self):
        self.writer = None  # for logging recvd. pose signal      
        self.step = 0

    def InitLogFiles(self):
        name = "TaskStatus"
        now = time.strftime("%Y%b%d-%H%M%S", time.gmtime())
        desc = "logged in centralized communication mode from: " + now
        # prepare label
        label = "TimeStamp;HH:MM:SS;StepCounter;TaskID;RobotCount;RobotList \n"
        # Data context
        ctx = DataCtx(name, label, desc)
        # Signal Logger
        self.writer = DataWriter("TIUpdater", ctx, now)

    def _GetCommonHeader(self):
        sep = DATA_SEP
        ts = str(time.time()) + sep + time.strftime("%H:%M:%S", time.gmtime())
        self.step = self.step + 1
        header = ts + sep + str(self.step)
        return header
    
    def AppendLog(self, taskid, robotlist):        
        sep = DATA_SEP
        len = len(robotlist)
        robotlist.sort() 
        log = self._GetCommonHeader()\
         + sep + str(len) + sep + str(robotlist) + "\n"
        try: 
            self.writer.AppendData(log)
        except:
            print "TaskStatus logging failed"


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
    global  datamgr_proxy, status_logger
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
        status_logger.writer.AppendLog(taskid, worker_list)
    except Exception, e:
        logger.warn("@GetTaskUrgency(): err %s", e)
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
    global datamgr_proxy,  taskurg, status_logger
    datamgr_proxy = datamgr
    #print "DMP ti1 %s" %id(datamgr_proxy.mTaskInfo)
    taskurg = INIT_TASK_URGENCY
    for k,  v in taskinfo.iteritems():
        datamgr_proxy.mTaskInfo[k] =v
    # setup logging
    status_logger = StatusLogger()
    status_logger.InitLogFiles()
    # real work starts
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
            datamgr_proxy.mTrackerAlive.wait()
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
        

