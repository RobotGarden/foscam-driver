#!/usr/bin/env python
"""
Camera action scheduler.
"""
__author__ = "Daniel Casner <www.danielcasner.org>"

import time
import scheduler
import control

SEEK_TIME = 20.0

class CameraAction:
    """A general class for camera actions to queue"""
    
    def __init__(self, foscam, expire=None):
        """Store basic action closure
        @param foscam driver object
        @param expire If time passes expire, delete the task
        """
        self.cam = foscam
        self.expire = expire
        
    def run(self):
        raise ValueError("CameraAction subclasses must implement run method")

class SnapshotAction:
    """An class to store the necessary information to execute 1 or more snapshots
    immediately or at a time in the future."""
    
    def __init__(self, foscam, preset, callback, number=1, interval=0.0, expire=None, userdata=None):
        """Setup the action closure.
        @param foscam driver object
        @param preset Preset to take snapshots at
        @param callback Function to call with image data
               arguments will be (image data, final image, userdata)
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
        self.userdata = userdata
        self.nextTime = 0.0
        
    def run(self):
        """Run the snapshot action.
        @return True if this action is done and can be removed from the queue.
        False if the action has more to do."""
        if self.expire is not None and time.time() > self.expire:
            return False
        elif time.time() < self.nextTime - SEEK_TIME: # Not ready to run yet, snooze to the scheduler
            return True
        else:
            self.cam.goto_preset(self.preset)
            time.sleep(SEEK_TIME)
            while self.number > 0:
                self.callback(self.cam.snapshot(), self.preset, self.number==1, self.userdata)
                self.number -= 1
                if self.interval <= SEEK_TIME:
                    time.sleep(self.interval)
                else:
                    self.nextTime = time.time() + self.interval - SEEK_TIME
                    return True
            return False



class FoscamScheduler(scheduler.Scheduler):
    "A scheduler specific for a given foscam"
    
    def __init__(self, foscam):
        scheduler.Scheduler.__init__(self)
        self.cam = foscam
    
    def snapshot(self, priority, preset, callback, expire=None, userdata=None):
        """Request a snapshot at a given preset.
        snapshots will go into the priority queue and execute when it is their
        turn. A snapshot will not be cancelled if another request with higher 
        priority arrives while it is being executed.
        @param priority honor system priority number for this request, larger numbers = higher priority.
        @param preset The preset to take the picture at.
        @param callback Function to call with the photo data
        @param expire Latest time that the caller wants the photo. None for no expiration.
        """
        self.append(priority, SnapshotAction(self.cam, preset, callback, expire=expire, userdata=userdata))
    
    def interval(self, priority, preset, callback, number, period, expire=None, userdata=None):
        """Requests a series of snapshots at a given present.
        @param priority honor system priority number for this request, larger numbers = higher priority.
        @param preset The preset to take the picture at.
        @param callback Function to call each successive frame.
        @param number How many pictures to take.
        @param period How many seconds between pictures.
        @param expire Latest time that the caller wants the photo. None for no expiration.
        """
        self.append(priority, SnapshotAction(self.cam, preset, callback, number, period, expire, userdata))
        
    def queueDone(self):
        "Action when there are no more requests on the camera"
        self.cam.goto_preset(self.cam.defaultPreset)
    
