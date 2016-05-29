#!/usr/bin/env python3
"""
An MQTT node that runs a camera scheduler for one or more foscams.
The camera scheduler takes care of managing the use of the cameras
"""
__author__ = "Daniel Casner <www.danielcasner.org>"

import sys, os, json
import camscheduler
import paho.mqtt.client as mqtt

class CamqttServer(mqtt.Client):
    "ISA MQTT client, HAS several cam schedulers"

    REQUEST_SUFFIX = "_request"

    def on_snapshot(self, snapshot, preset, final, userdata):
        self.publish(userdata, json.dumps({'preset': preset, 'final': final}).encode() + b'\0' + snapshot)

    def on_connect(self, userdata, flags, rc):
        "Subscribe to topics on connect in case of disconnection"
        for camName in self.schedulers.keys():
            self.subscribe(name + self.REQUEST_SUFFIX, qos=2)
            
    def on_message(self, userdata, msg):
        if not msg.topic.endswith(self.REQUEST_SUFFIX):
            sys.stderr.write("Received unexpected topic: \"{}\"{}".format(msg.topic, os.linesep))
        else:
            camera = msg.topic[:-len(self.REQUEST_SUFFIX)]
            if not camera in self.schedulers:
                sys.stderr.write("Received request for camera \"{}\" but we only have{linesep}\t{}{linesep}".format(camera, repr(self.schedulers.keys(), linesep=os.linesep)))
            else:
                try:
                    command, args = json.loads(msg.payload)
                    args.update({'callback': self.on_snapshot, 'userdata': cammera})
                    if command == 'snapshot':
                        self.schedulers[camera].snapshot(**args)
                    elif command == 'internal':
                        self.schedulers[camera].interval(**args)
                    else:
                        raise ValueError("Invalid scheduler command: " + command)
                except Exception as e:
                    sys.stderr.write(str(e))
    
    
    def __init__(self, clientID, broker, cameras):
        """Initalize camera server
        @param clientID The MQTT client ID for the server
        @param The host name / IP address of the broker
        @param cameras A dictionary of named foscam instances. The names of the cameras be used as base names for MQTT
        topics for requesting and receiving images. The server will subscribe to a topic <NAME>_request for each camera
        to receive snapshot requests. Snapshots will be published as <NAME>_snapshot
        """
        mqtt.Client.__init__(self, clientID, True)
        self.schedulers = {name: camscheduler.FoscamScheduler(camera) for name, camera in cameras.items()}
        self.connect(broker)

class CamqttClient(mqtt.Client):
    "ISA MQTT client for requesting scheduled snapshots"
    
    def on_connect(self, userdata, flags, rc):
        
