#!/usr/bin/env python
"""A basic python interface for the FOSCAM IP cameras to control motion and
parameters, and still images but not retrieve video or audio.
Eventually this will turn into a ROS driver."""
__author__="Daniel Casner <www.danielcasner.org>"

from getpass import getpass
import urllib

VGA=32
QVGA=8

def dict2url(dict):
    return '&'.join(['='.join(i) for i in dict.items()])

class FoscamControl(object):

    def __init__(self, url, user, password):
        self.url  = url
        if password is None: password = getpass('Password for %s@%s>' % user, url)
        self.auth = {'user': user, 'pwd': password}

    def control(self, command, onestep=None, degree=None):
        "Calls the FOSCAM API with the specified args"
        args = {'command': str(command)}
        if onestep: args['onestep'] = '1'
        if degree is not None: args['degree'] = str(degree)
        args.update(self.auth) # Add authentication to call
        fh = urllib.urlopen('%s/decoder_control.cgi?%s' % (self.url, args))
        print fh.read()
        fh.close()
        
    def snapshot(self, resolution=VGA):
        "Gets a still image"
        fh = urllib.urlopen('%s/snapshot.cgi?user=%s&pwd=%s&resolution=%d' % (self.url, self.auth['user'], self.auth['pwd'], resolution))
        retval = fh.read()
        fh.close()
        return retval
