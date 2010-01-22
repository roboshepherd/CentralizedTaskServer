import multiprocessing
import logging, logging.config
import time
import copy
import random
import sys

from RILCommonModules.RILSetup import  *
from RILCommonModules.task_info import *
from data_manager import *

logging.config.fileConfig("logging.conf")
#create logger
logger = logging.getLogger("EpcLogger")

#  Setup Initial Task Info 
# Fix: Change it to reading from a config file
ti = TaskInfo()
task1 = ShopTask(id=1,  x=1507,  y=944)
task2 = ShopTask(id=2,  x=2431,  y=2264)
task3 = ShopTask(id=3,  x=1042,  y=1973)
ti.AddTaskInfo(1,  task1.Info()) 
ti.AddTaskInfo(2,  task2.Info())
ti.AddTaskInfo(3,  task3.Info())
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
	urgency_log = time.strftime("%H:%M:%S", time.gmtime())\
		+ "; " + str(updater_step)
	workers_log = time.strftime("%H:%M:%S", time.gmtime())\
		+ "; " + str(updater_step)
    
def PrepareLogMsg(urgency,  workers):
    global   urgency_log,  workers_log
    urg_msg = "; " + str(urgency) 
    urgency_log += urg_msg
    workers_msg = "; " + str(workers)
    workers_log += workers_msg

def GetTaskUrgency(taskid,  urg):
	global  datamgr_proxy
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
		print "Task %d Workers:" %taskid
		print worker_list
	except Exception, e:
		print "@GetTaskUrgency(): worker count unavailable", e
	workers= len(worker_list)
	if workers > 0:
		urgency = urg - workers * DELTA_TASK_URGENCY 
	elif workers == 0:
		urgency = urg +  DELTA_TASK_URGENCY
	else:
		print "worker count not updated"
   # Save data into log
	PrepareLogMsg(urgency,  workers)
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
    header = "#Time(HH:MM:SS); Step#"
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
		# simulating task worker signal recv.
		#datamgr_proxy.mTaskWorkers[k] = [random.randint(1, 8)] * (k - 1)
	print "@updater:"
	print datamgr_proxy.mTaskInfo
	datamgr_proxy.mTaskInfoAvailable.set()
	try:
		while True:
			print "@updater:"
			UpdateTaskInfo()
			UpdateLogFiles()
			time.sleep(TASK_INFO_UPDATE_FREQ)
	except (KeyboardInterrupt, SystemExit):
			print "User requested exit... TaskInfoUpdater shutting down now"
			sys.exit(0)
        

