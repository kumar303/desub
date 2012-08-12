import os
import shutil
import sys
import tempfile
import time
import unittest

from nose.tools import eq_, raises
import psutil

import subd


class Test(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.proc = self.join()

    def tearDown(self):
        self.proc.stop()
        shutil.rmtree(self.tmp)

    def join(self):
        return subd.join([sys.executable,
                          self.cmd('loop.py')], root=self.tmp)

    def cmd(self, name):
        return os.path.join(os.path.dirname(__file__), 'cmd', name)

    def test_start(self):
        pp = psutil.Process(self.proc.pid)
        eq_(pp.status, 'running')

    @raises(psutil.NoSuchProcess)
    def test_stop(self):
        pid = self.proc.pid
        self.proc.stop()
        psutil.Process(pid)

    def test_stop_clears_root(self):
        self.proc.stop()
        assert not os.path.exists(self.proc.root)

    def test_output(self):
        time.sleep(1)
        eq_(self.proc.stdout.read(), 'stdout')
        eq_(self.proc.stderr.read(), 'stderr')

    def test_join(self):
        proc2 = self.join()
        eq_(self.proc.pid, proc2.pid)

    def test_default_root(self):
        pr = subd.join([sys.executable, self.cmd('loop.py')])
        self.addCleanup(lambda: shutil.rmtree(pr.root))
        assert pr.pid != self.proc.pid, (
                            'new root should make separate procs')
