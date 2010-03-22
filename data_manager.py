import multiprocessing
from multiprocessing import *    
class DataManager:
    def __init__(self):
        self.mgr = multiprocessing.Manager()
        self.mTaskInfo = self.mgr.dict() 
        # key: taskid, value: list of attrib (t.s., x, y,  phi)
        self.mTaskInfoAvailable = self.mgr.Event() 
        # set by taskinfo updater 
        self.mTaskWorkers = self.mgr.dict()  
        # key:robotid v: taskid recvd. by dbus client
        ## Manage task server's task info updtater state 
        #(pause/play style) by a dbus signal
        self.mTaskUpdaterState =  self.mgr.dict() 
        self.mTaskUpdaterStateUpdated = self.mgr.Event() 

