#!/usr/bin/env python
"""
A general purpose action scheduling module.
The Scheduler class includes a priority queue and it's own thread which executes runables from the queue in priority
order.
"""
__author__  = "Daniel Casner <www.danielcasner.org>"

import threading

class PriorityQueue:
    """
    A priority queue where objects are added with a priority and popped based on their priority.
    Complexity is pushed on the append method rather than pop.
    This priority queue also includes it's own mutex for thread safety.
    """

    def __init__(self):
        "Initialize empty priority queue."
        self.q = []
        self.s = threading.Lock()
    
    def __del__(self):
        "Clean up safely."
        assert self.s.acquire() # Wait for everyone else clear
    
    def __len__(self):
        "Length of the queue, thread safe but not garunteed consistant"
        return len(self.q)
    
    @property
    def empty(self):
        "True if there are no elements in the queue, thread safe but not garunteed consistant"
        self.aquire()
        ret = len(self.q) == 0
        self.release()
        return ret
    
    def acquire(self):
        "Acquire the queue semaphore."
        return self.s.acquire()
        
    def release(self):
        "Release the queue semaphore."
        return self.s.release()
    
    def append(self, priority, obj):
        "Add an new object to the queue at the specified priority."
        self.s.acquire()
        for i, o in enumerate(self.q):
            if priority <= o[0]:
                self.q.insert(i, (priority, obj))
                break
        else:
            self.q.append((priority, obj))
        self.s.release()
            
    def pop(self):
        "Return the latest next (highest priority) object from the queue."
        self.s.acquire()
        retval = self.q.pop()
        self.s.release()
        return retval


            
class Scheduler:
    """A priorized action runner using threads thread action runner"""
        
    def __init__(self):
        "Set up the scheduler."
        self.queue = PriorityQueue()
        self.thread = None

    def append(self, priority, runnable):
        """Schedules a new action to be run.
        Runnable may be any object with a run method. The method should return True if the runnable wants to be re-
        posted to the queue after being run."""
        self.queue.append(priority, runnable)
        self.scheduleThread()
    
    def scheduleThread(self):
        """Fire off the priority queue processing thread if it isn't."""
        if self.thread is None or self.thread.isAlive() is False:
            self.thread = threading.Thread(target=self.processQueue)
            self.thread.start()
    
    def processQueue(self):
        """Execute anything from the priorityQueue"""
        while True:
            if self.queue.empty:
                break
            else:
                priority, task = self.queue.pop()
                self.queue.release()
                repost = task.run()
                if repost:
                    self.queue.append(priority, task)

