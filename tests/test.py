import os
import shutil
import sys
import tempfile
import time
import unittest

from nose.tools import eq_, raises
import psutil

import desub


class Test(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.proc = self.join()

    def tearDown(self):
        self.proc.stop()
        shutil.rmtree(self.tmp)

    def join(self):
        return desub.join([sys.executable,
                           self.cmd('loop.py')], root=self.tmp)

    def cmd(self, name):
        return os.path.join(os.path.dirname(__file__), 'cmd', name)

    def test_start(self):
        self.proc.start()
        pp = psutil.Process(self.proc.pid)
        eq_(pp.status, 'running')
        self.proc.stop()
        self.assertRaises(psutil.NoSuchProcess, lambda: pp.status)

    @raises(psutil.NoSuchProcess)
    def test_stop(self):
        self.proc.start()
        pid = self.proc.pid
        self.proc.stop()
        psutil.Process(pid)

    def test_stop_preserves_root(self):
        self.proc.start()
        assert os.path.exists(self.proc.root)
        self.proc.stop()
        assert os.path.exists(self.proc.root)

    def test_output(self):
        self.proc.start()
        time.sleep(1)
        eq_(self.proc.stdout.read(), 'stdout')
        eq_(self.proc.stderr.read(), 'stderr')

    def test_join(self):
        self.proc.start()
        proc2 = self.join()
        proc2.start()
        eq_(self.proc.pid, proc2.pid)

    def test_default_root(self):
        self.proc.start()
        tmp = tempfile.mkdtemp()
        pr = desub.join([sys.executable, self.cmd('loop.py')], root=tmp)
        try:
            assert pr.pid != self.proc.pid, (
                            'new root should make separate procs')
        finally:
            shutil.rmtree(pr.root)
