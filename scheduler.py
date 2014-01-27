#!/usr/bin/env python

import time, threading
import control

class Scheduler(object):
    """An object to manage multiple competing requests for the camera.
    Multiple callers can schedule single snapshots or seriese via the
    scheduler. Priority is an honor system among callers with higher
    numbers getting presidence."""
    
    SEEK_TIME = 10.0
    
    def __init__(self, foscam):
        "Set up the scheduler."
        self.cam = foscam
        self.queue = PriorityQueue()
    
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
        def execute_snapshot(cam, preset, callback, expire):
            if time.time() > expire: return
            cam.goto_preset(preset)
            time.sleep(SEEK_TIME)
            callback(cam.snapshot())
        self.queue.append([execute_snapshot, cam, preset, callback, expire], priority)
    
    def interval(self, priority, preset, callback, number, period):
        """Requests a series of snapshots at a given present.
        @param priority honor system priority number for this request, larger numbers = higher priority.
        @param preset The preset to take the picture at.
        @param callback Function to call each successive frame.
        @param number How many pictures to take.
        @param period How many seconds between pictures.
        """
        def execute_seriese(cam, preset, callback, number, period):
            cam.goto_preset(preset)
            time.sleep(SEEK_TIME)
            count = 0
            while count < number:
                callback(cam.snapshot())
                count += 1
                time.sleep(period)
        if period < seek_time:
            
            
                