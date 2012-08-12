"""
Work with a detached subprocess.
"""
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess

import psutil

non_id_chars = re.compile(r'[^a-zA-Z0-9_\.-]+')


def join(cmd_args, **kw):
    """
    Join a subprocess or start one if it's not running.

    The return value is a :class:`desub.Desub` object.

    Example::

        >>> import desub
        >>> proc = desub.join(['python', 'tests/cmd/loop.py'])
        >>> proc.pid
        1987
        >>> proc.stdout.read()
        'stdout'
        >>> proc.stderr.read()
        'stderr'
        >>> proc.stop()
        >>> proc.is_running()
        False
    """
    return Desub(cmd_args, **kw)


class Desub:
    """
    A joined subprocess.

    This object represents a command with **cmd_args** that may or may
    not be running yet. If it's not running, the command will be started
    otherwise you will join the command. Two processes can be running
    at the same time but only if their args are different.

    The interface is similar to
    `subprocess.Popen <http://docs.python.org/library/subprocess.html#popen-constructor>`_
    when appropriate. All extra keyword arguments are passed into the Popen
    constructor.

    Keyword arguments

    **root**
        The root directory to store subprocess artifacts like a PID file
        and stdout/stderr logs.
        By default this is ``~/.desub``.

    Members
    """

    def __init__(self, cmd_args, **kw):
        self.cmd_args = cmd_args
        self.name = self.make_name(cmd_args)
        self.kw = kw
        root = kw.pop('root', None)
        if not root:
            root = os.path.join(os.path.expanduser('~'), '.desub')
        self.root = os.path.join(root, self.name)
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        self.data = self.load_data()
        self.data['cmd_args'] = cmd_args
        self.data['keyword_args'] = repr(kw)
        self.save_data()
        if not self.is_running():
            self.start()

    def is_running(self):
        """True if the subprocess is running."""
        pp = self.pid
        if pp:
            try:
                psutil.Process(pp)
                return True
            except psutil.NoSuchProcess:
                pass
        return False

    @property
    def stdout(self):
        """An open read-only file to stdout."""
        return open(self.path('cmd.stdout'), 'r')

    @property
    def stderr(self):
        """An open read-only file to stderr."""
        return open(self.path('cmd.stderr'), 'r')

    @property
    def pid(self):
        """
        The integer PID of the subprocess or None.
        """
        pf = self.path('cmd.pid')
        if not os.path.exists(pf):
            return None
        with open(pf, 'r') as f:
            return int(f.read())

    def start(self):
        """Start the subprocess."""
        c_out, c_err = (open(self.path('cmd.stdout'), 'w'),
                        open(self.path('cmd.stderr'), 'w'))
        kw = self.kw.copy()
        kw['stdout'] = c_out
        kw['stderr'] = c_err
        if not kw.get('cwd', None):
            kw['cwd'] = os.getcwd()
        pr = subprocess.Popen(self.cmd_args, **kw)
        with open(self.path('cmd.pid'), 'w') as f:
            f.write(str(pr.pid))

    def stop(self):
        """Stop the subprocess."""
        pp = self.pid
        if pp:
            try:
                kill_process_nicely(pp)
                shutil.rmtree(self.root)
            except psutil.NoSuchProcess:
                pass

    def make_name(self, cmd_args):
        sh = hashlib.sha1()
        for v in cmd_args:
            sh.update(v)
        return '%s.%s' % (non_id_chars.sub('_', cmd_args[0]), sh.hexdigest())

    def load_data(self, update=None):
        dd = self.path('data.json')
        if not os.path.exists(dd):
            return {}
        with open(dd) as f:
            return json.load(f)

    def path(self, fname):
        return os.path.join(self.root, fname)

    def save_data(self):
        with open(self.path('data.json'), 'wb') as f:
            json.dump(self.data, f)


def kill_process_nicely(pid):
    p = psutil.Process(pid)
    for child in p.get_children():
        kill_process_nicely(child.pid)
    p.send_signal(signal.SIGINT)
    p.wait(timeout=10)
