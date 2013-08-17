#!/usr/bin/env python

import time, threading
import control

class Scheduler(object):
    """An object to manage multiple competing requests for the camera.
    Multiple callers can schedule single snapshots or seriese via the
    scheduler. Priority is an honor system among callers with higher
    numbers getting presidence."""
    
    def __init__(self, foscam):
        "Set up the scheduler."
        self.cam = foscam
        self.queue = PriorityQueue()
    
    def snapshot(self, priority, preset, callback, expire=None):
        """Request a snapshot at a given preset.
        snapshots will go into the priority queue and execute when it is their
        turn. A snapshot will not be canceled if another request with higher 
        priority arrives while it is being executed.
        @param priority honor system priority number for this request, larger numbers = higher priority.
        @param preset The preset to take the picture at.
        @param callback Function to call with the photo data
        @param expire Latest time that the caller wants the photo. None for no expiration.
        @return True if the snapshot will happen imeediately, false if it is queued."""
        def execute_snapshot(preset):
            self.foscam.goto_preset(preset)
            def return_snapshot():
                callback(self.foscam.snapshot())
            threading.Timer(10.0, return_snapshot)
        self.priority_queue.