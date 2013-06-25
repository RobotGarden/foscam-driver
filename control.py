#!/usr/bin/env python
"""A basic python interface for the FOSCAM IP cameras to control motion and
parameters, not retrieve video or audio.
Eventually this will turn into a ROS driver."""
__author__="Daniel Casner <www.danielcasner.org>"

from getpass import getpass
import urllib


class FoscamControl(object):

    def __init__(self, url, user, password):
        self.url  = url
        self.auth = {'user': user, 'pwd': password}

    def call(self, **kwargs):
        "Calls the FOSCAM API with the specified args"
        kwargs.update(self.auth) # Add authentication to call
        
