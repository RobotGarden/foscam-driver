#!/usr/bin/env python

import unittest
from PIL import Image
import tempfile
import os
import control

class ControllerTest(unittest.TestCase):
    "Test suite for the Foscam controller."
    
    @classmethod
    def setUpClass(cls):
        CACHE_FN = '.testbench_args_cache'
        if os.path.isfile(CACHE_FN):
            url, user = open(CACHE_FN).read().split()
        else:
            url  = raw_input("Foscam URL>>> ")
            user = raw_input("Foscam User>>> ")
            open(CACHE_FN, 'w').write('%s\n%s' % (url, user))
        cls.cam = control.FoscamControl(url, user, None)
            
    def test_snapshot(self):
        # Load snapshot into PIL
        fh = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        fn = fh.name
        fh.write(self.cam.snapshot())
        fh.close()
        os.startfile(fn)
        result = raw_input("Does the image look appropriate? (y/N)").lower()
        os.remove(fn)
        self.assertEqual(result, 'y')
        
    def test_videostream(self):
        self.skipTest("Don't have a good way to test video streams yet.")
        
    def test_get_status(self):
        self.assertIsInstance(self.cam.get_status(), dict)
        
    def test_get_camera_params(self):
        self.assertIsInstance(self.cam.get_camera_params(), dict)

if __name__ == '__main__':
    unittest.main()