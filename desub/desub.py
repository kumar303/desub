"""
Work with a detached subprocess.
"""
import hashlib
import json
import os
import re
import signal
import subprocess

import psutil

non_id_chars = re.compile(r'[^a-zA-Z0-9_\.-]+')


def join(cmd_args, **kw):
    """
    Join a subprocess or start one if it's not running.

    The return value is a :class:`desub.Desub` object.

    Start by joining a command that may or may not
    already be running.

    .. doctest::
        :hide:

        >>> import desub

    .. doctest::

        >>> proc = desub.join(['python', 'tests/cmd/loop.py'])

    There will only ever be one instance of that command
    running unless you specify a custom *root*.
    Check to see if the command is running:

        >>> proc.is_running()
        False

    OK. It's not running, so start it up:

        >>> proc.start()
        >>> proc.is_running()
        True
        >>> type(proc.pid)
        <type 'int'>

    .. doctest::
        :hide:

        >>> import time
        >>> time.sleep(1)

    Fetch the output:

        >>> proc.stdout.read()
        'stdout'
        >>> proc.stderr.read()
        'stderr'

    Stop the command, if you want to:

        >>> proc.stop()
        >>> proc.is_running()
        False

    When you read the output of a stopped command,
    that's the output from a subsequent run.

        >>> proc.stdout.read()
        'stdout'

    """
    return Desub(cmd_args, **kw)


class Desub:
    """
    A detached subprocess.

    This object represents a command with **cmd_args** that may or may
    not be running yet. Two processes can be running
    at the same time but only if their args are different or if their
    **roots** are different.

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

    def is_running(self):
        """
        True if the subprocess is running.

        If it's a zombie then we call
        :func:`desub.Desub.stop` to kill it with fire and return False.
        """
        pp = self.pid
        if pp:
            try:
                proc = psutil.Process(pp)

                # Possible status:
                # "STATUS_RUNNING", "STATUS_IDLE",
                # "STATUS_SLEEPING", "STATUS_DISK_SLEEP",
                # "STATUS_STOPPED", "STATUS_TRACING_STOP",
                # "STATUS_ZOMBIE", "STATUS_DEAD",
                # "STATUS_WAKING", "STATUS_LOCKED",

                if proc.status in (psutil.STATUS_STOPPED,
                                   psutil.STATUS_DEAD,
                                   psutil.STATUS_ZOMBIE):
                    # The PID is still in the process table so call stop to
                    # remove the PID.
                    self.stop()
                    return False
                else:
                    # OK, it's running.
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

    def stop(self, timeout=15):
        """Stop the subprocess.

        Keyword Arguments

        **timeout**
          Time in seconds to wait for a process and its
          children to exit.
        """
        pp = self.pid
        if pp:
            try:
                kill_process_nicely(pp, timeout=timeout)
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


def kill_process_nicely(pid, timeout=15):
    p = psutil.Process(pid)
    for child in p.get_children():
        kill_process_nicely(child.pid)
    p.send_signal(signal.SIGINT)
    p.wait(timeout=timeout)
