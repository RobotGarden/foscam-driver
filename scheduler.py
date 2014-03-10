#!/usr/bin/env python
"""
Snapshot and interval capture scheduler module for FOSCAM.
"""
__author__  = "Daniel Casner <www.danielcasner.org>"
__version__ = "0.0.1"

import time, threading
import control

SEEK_TIME = 10.0

class PriorityQueue(object):
    """A priority queue where objects are added with a priority and popped based on
their priority."""

    def __init__(self):
        "Initialize empty priority queue."
        self.q = []
        self.s = threading.Semaphore()
    
    def __del__(self):
        "Clean up safely."
        assert self.s.acquire() # Wait for everyone else clear
    
    def __len__(self):
        "Length of the queue"
        return len(self.q)
    
    @property
    def empty(self):
        "True if there are no elements in the queue."
        return len(self.q) == 0
    
    def acquire(self):
        "Acquire the queue semaphore."
        return self.s.acquire()
        
    def release(self):
        "Release the queue semaphore."
        return self.s.release()
    
    def append(self, priority, obj):
        "Add an new object to the queue at the specified priority."
        for i, o in enumerate(self.q):
            if priority <= o[0]:
                self.q.insert(i, (priority, obj))
                return
        else:
            self.q.append((priority, obj))
            
    def pop(self):
        "Return the latest next (highest priority) object from the queue."
        return self.q.pop()


class SnapshotAction(object):
    """An class to store the necessary information to execute 1 or more snapshots
    immediately or at a time in the future."""
    
    def __init__(self, foscam, preset, callback, number=1, interval=None, expire=None):
        """Setup the action closure.
        @param foscam driver object
        @param preset Preset to take snapshots at
        @param callback Function to call with image data
        @param number Count of snapshots to take
        @param interval If number > 1, interval between snapshots
        @param expire If time passes expire, delete the task
        """
        self.cam      = foscam
        self.preset   = preset
        self.callback = callbakc
        self.number   = number
        self.interval = interval
        self.expire   = expire
        self.lastTime = 0.0
        
    def run(self):
        """Run the snapshot action.
        @return True if this action is done and can be removed from the queue.
        False if the action has more to do."""
        if time.time() > expire: return True
        else:
            self.cam.goto_preset(self.preset)
            time.sleep(SEEK_TIME)
            remaining = self.interval - (time.time() - self.lastTime)
            if remaining > 0.0: time.sleep(remaining)
            while self.number > 0:
                self.lastTime = time.time()
                self.callback(self.cam.snapshot())
                self.number -= 1
                if self.interval <= SEEK_TIME:
                    time.sleep(self.interval)
                else:
                    return False
            return True

            
class Scheduler(object):
    """An object to manage multiple competing requests for the camera.
    Multiple callers can schedule single snapshots or seriese via the
    scheduler. Priority is an honor system among callers with higher
    numbers getting presidence."""
    
    
    def __init__(self, foscam):
        "Set up the scheduler."
        self.cam = foscam
        self.queue = PriorityQueue()
        self.thread = None
    
    def snapshot(self, priority, preset, callback, expire=None):
        """Request a snapshot at a given preset.
        snapshots will go into the priority queue and execute when it is their
        turn. A snapshot will not be cancelled if another request with higher 
        priority arrives while it is being executed.
        @param priority honor system priority number for this request, larger numbers = higher priority.
        @param preset The preset to take the picture at.
        @param callback Function to call with the photo data
        @param expire Latest time that the caller wants the photo. None for no expiration.
        """
        self.queue.acquire()
        self.queue.append(priority, SnapshotAction(self.cam, preset, callback, expire=expire))
        self.scheduleThread()
        self.queue.release()
    
    def interval(self, priority, preset, callback, number, period):
        """Requests a series of snapshots at a given present.
        @param priority honor system priority number for this request, larger numbers = higher priority.
        @param preset The preset to take the picture at.
        @param callback Function to call each successive frame.
        @param number How many pictures to take.
        @param period How many seconds between pictures.
        """
        self.queue.acquire()
        self.queue.append(priority, SnapshotAction(self.cam, preset, callback, number, period, expire))
        self.scheduleThread()
        self.queue.release()
    
    def scheduleThread(self):
        """Fire off the priority queue processing thread if it isn't."""
        if self.thread is None or self.thread.isAlive() is False:
            self.thread = threading.Thread(target=self.processQueue)
            self.thread.start()
            
    
    def processQueue(self):
        """Execute anything from the priorityQueue"""
        while True:
            self.queue.acquire()
            if self.queue.empty:
                self.queue.release()
                break
            else:
                priority, task = self.queue.pop()
                self.queue.release()
                done = task.run()
                if not done:
                    self.queue.acquire()
                    self.queue.append(priority, task)
                    self.queue.release()