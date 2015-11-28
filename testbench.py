#!/usr/bin/env python3

import unittest
from PIL import Image
import tempfile
import sys
import os
import platform
import control
import time
from getpass import getpass

def instantiateFoscam():
    CACHE_FN = '.testbench_args_cache'
    if os.path.isfile(CACHE_FN):
        url, user, pwd = open(CACHE_FN).read().split()
    else:
        url  = input("Foscam URL>>> ")
        user = input("Foscam User>>> ")
        pwd  = getpass("Foscam Password>>> ")
        open(CACHE_FN, 'w').write('%s\n%s\n%s' % (url, user, pwd))
    return control.FoscamControl(url, user, pwd)


class ControllerTest(unittest.TestCase):
    "Test suite for the Foscam controller."
    
    @classmethod
    def setUpClass(cls):
        cls.cam = instantiateFoscam()
            
    def test_snapshot(self):
        # Load snapshot into PIL
        fh = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        fn = fh.name
        fh.write(self.cam.snapshot())
        fh.close()
        if os.name == 'nt':
            os.startfile(fn)
        elif platform.system() == 'Darwin':
            os.system("open {}".format(fn))
        else:
            raise Exception("Unsupported OS for test snapshot")
        result = input("Does the image look appropriate? (y/N)").lower()
        os.remove(fn)
        self.assertEqual(result, 'y')
        
    def test_videostream(self):
        self.skipTest("Don't have a good way to test video streams yet.")
        time.sleep(1.0)
        
    def test_get_status(self):
        self.assertIsInstance(self.cam.get_status(), dict)
        time.sleep(1.0)
        
    def test_get_camera_params(self):
        self.assertIsInstance(self.cam.get_camera_params(), dict)
        time.sleep(1.0)
        
    def test_control(self):
        for command in control.CONTROL_COMMANDS:
            for onestep in [None, True]:
                for degree in [None, 0, 10, 20, 30]:
                    rslt = self.cam.control(command, onestep, degree)
                    sys.stdout.write('FoscamControl({}, {}, {}) --> {}\n'.format(*[repr(a) for a in [command, onestep, degree, rslt]]))
                    self.assertIsInstance(rslt, dict)
                    time.sleep(1.0) # Rate limit
    
    def test_preset(self):
        assertIsInstance(self.cam.goto_preset(1), dict)
        time.sleep(1.0)

if __name__ == '__main__':
    unittest.main()
