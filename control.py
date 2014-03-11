#!/usr/bin/env python
"""A basic python interface for the FOSCAM IP cameras to control motion and
parameters."""
__author__="Daniel Casner <www.danielcasner.org>"
import sys
from getpass import getpass
if sys.version_info.major > 2:
    from urllib.request import urlopen
else:
    from urllib import urlopen

VIDEO_RESOLUTIONS = {
    'VGA':  '32', 
    'QVGA':  '8',
    'QQVGA': '2',
}
VIDEO_RATES = {
    'full': '0',
    20: '1',
    15: '3',
    10: '6',
    5: '11',
    4: '12',
    3: '13',
    2: '14',
    1: '15',
    1.0/2.0: '17',
    1.0/3.0: '19',
    1.0/4.0: '21',
    1.0/5.0: '23',
}
VIDEO_MODES = {
    '50Hz': '0',
    '60Hz': '1',
    'outdoor': '2',
}

CONTROL_COMMANDS = {
    'UP': '0',
    'STOP_UP': '1',
    'DOWN': '2',
    'STOP_DOWN': '3',
    'LEFT': '4',
    'STOP_LEFT': '5',
    'RIGHT': '6',
    'STOP_RIGHT': '7',
    'CENTER': '25',
    'UP_DOWN_PATROL': '26',
    'STOP_UP_DOWN_PATROL': '27',
    'LEFT_RIGHT_PATROL': '28',
    'STOP_LEFT_RIGHT_PATROL': '29',
    'UPPER_LEFT': '90',
    'UPPER_RIGHT': '91',
    'DOWN_LEFT': '92',
    'DOWN_RIGHT': '93',
}
PATROL_MODES = {
    'initial': '0',
    'vertical': '1',
    'horizontal': '2',
    'vertical+horizontal': '3',
}

def dict2querry(dict):
    return urlencode('&'.join(['='.join(i) for i in dict.items()]))

class FoscamControl(object):

    def __init__(self, url, user, password):
        self.url  = url
        if password is None: password = getpass('Password for %s@%s>' % (user, url))
        self.auth = {'user': user, 'pwd': password}

    @staticmethod
    def _read_raw(url):
        fh = urlopen(url)
        retval = fh.read()
        fh.close()
        return retval
    
    @classmethod
    def _read_and_parse(cls, url):
        raw = cls._read_raw(url)
        ret = {}
        for l in raw.split('\n'):
            if not (l.startswith('var ') and l.endswith(';')): continue
            k, v = l[4:-1].split('=')
            if v.isdigit(): # and int
                ret[k] = int(v)
            elif v.startswith("'") and v.endswith("'"): # a string
                ret[k] = v[1:-1]
            else: # A ???
                ret[k] = v
        return ret
    
    def snapshot(self, resolution='VGA'):
        "Gets a still image (jpeg)"
        if not resolution in VIDEO_RESOLUTIONS.keys(): raise ValueError('resolution must be one of %s' % repr(VIDEO_RESOLUTIONS.keys()))
        else: return self._read_raw('%s/snapshot.cgi?user=%s&pwd=%s&resolution=%s' % (self.url, self.auth['user'], self.auth['pwd'], VIDEO_RESOLUTIONS[resolution]))
    
    def videostream(self, resolution='VGA', rate='full', format='mjpeg'):
        "Start a video stream and return the file handle"
        if format == 'mjepg':
            url = self.url + '/videostream.cgi?'
        elif format == 'asf':
            url = self.url + '/videostream.asf?'
        else:
            raise ValueError('Unsupported format code, must be "mjpeg" or "asf".')
        if not rate in VIDEO_RATES.keys():
            raise ValueError('Unsupported frame rate, must be one of %s' % repr(VIDEO_RATES.keys()))
        if not resolution in VIDEO_RESOLUTIONS.keys():
            raise ValueError('Unsupported resolution, must be one of %s' % repr(VIDEO_RESOLUTIONS.keys()))
        args = {'resolution': resolution, 'rate': VIDEO_RATES[rate]}
        args.update(self.auth)
        return urlopen(url + dict2querry(args))
        
    def get_status(self):
        "Obtain device status"
        return self._read_and_parse(self.url + '/get_status.cgi')
        
    def get_camera_params(self):
        "Obtain current camera parameters"
        return self._read_and_parse(self.url + '/get_camera_params.cgi?' + dict2querry(self.auth))
        
    def control(self, command, onestep=None, degree=None):
        "Control's FOSCAM's motion hardware"
        args = {'command': str(command)}
        if onestep: args['onestep'] = '1'
        if degree is not None: args['degree'] = str(degree)
        args.update(self.auth) # Add authentication to call
        return self._read_and_parse('%s/decoder_control.cgi?%s' % (self.url, dict2querry(args)))
    
    def goto_preset(self, preset):
        "Go to numbered preset pan and tilt position"
        args = {'command': str(30 + ((preset-1)*2))}
        args.update(self.auth)
        self._read_raw('%s/decoder_control.cgi?%s' % (self.url, dict2querry(args)))
    
    def set_preset(self, preset):
        "Save the current pan and tilt position of the camera as a numbered preset"
        args = {'command': str(31 + ((preset-1)*2))}
        args.update(self.auth)
        self._read_raw('%s/decoder_control.cgi?%s' % (self.url, dict2querry(args)))
    
    def camera_control(self, resolution=None, brightness=None, contrast=None, mode=None, partol=None):
        "Set a parameter for the camera sensor. Only one of: resolution, brightness, contrast, mode or patrol may be not None."
        if resolution is not None:
            if not resolution in VIDEO_RESOLUTIONS.keys(): raise ValueError("resolution must be None or one of %s" % repr(VIDEO_RESOLITIONS.keys()))
            args = {'param': '0', 'value': VIDEO_RESOLUTIONS[resolution]}
        elif brightness is not None:
            if brightness < 0 or brightness > 255: raise ValueError('brightness must be None or an int between 0 and 255')
            args = {'param': '1', 'value': str(int(brightness))}
        elif contrast is not None:
            if contrast < 0 or contrast > 6: raise ValueError('contrast must be None or an int between 0 and 6')
            args = {'param': '2', 'value': str(int(contrast))}
        elif mode is not None:
            if not mode in VIDEO_MODES.keys(): raise ValueError('mode must be None or one of %s' % repr(VIDEO_MODES.keys()))
            args = {'param': '3', 'value': VIDEO_MODES[mode]}
        elif patrol is not None:
            if not patrol in PATROL_MODES.keys(): raise ValueError('patrol must be None or one of %s' % repr(PATROL_MODES.keys()))
            args = {'param': '5', 'value': PATROL_MODES[patrol]}
        else:
            raise ValueError('Exactly one argument to this function must be not None')
        args.update(self.auth) # Add authentication to call
        return self.read_and_parse('%s/camera_control.cgi?%s' % (self.url, dict2querry(args)))
        
    def reboot(self):
        "Reboot the remote camera"
        self._read_raw('%s/reboot.cgi?%s' % (self.url, dict2querry(self.auth)))
        
    def get_params(self):
        "Obtain device settings"
        return self._read_and_parse('%s/get_params.cgi?%s' % (self.url, dict2querry(self.auth)))
        
    def set_ftp(self, server, user, password, directory, port=21, retain=False, interval=0):
        "Configure FTP upload settings"
        args = {'svr': server, 'user': user, 'pwd': password, 'dir': directory, 'port': str(port), 'retain': str(int(retain)), 'upload_interval': str(interval), 'cam_user': self.auth['user'], 'cam_pwd': self.auth['pwd']}
        self._read_daw('%s/set_ftp.cgi?%s' % (self.url, dict2querry(args)))
        
    def get_misc(self):
        "Get camera misc parameter settings"
        return self._read_and_parse('%s/get_misc.cgi?%s' % (self.url, dict2querry(self.auth)))
        
    def set_misc(self, **args):
        "Set camera misc parameters"
        args.update(self.auth)
        self._read_raw('%s/set_misc.cgi?%s' % (self.url, dict2querry(args)))
        
    def open_log(self):
        "Open a file pointer to the camera log, caller must read and close"
        return urlopen('%s/get_log.cgi?%s' % (self.url, dict2querry(self.auth)))

        