=====
desub
=====

.. highlight:: python


desub is a Python module to work with a detached `subprocess`_.

This is useful for making a web interface (or whatever) to monitor a
process running in the background. You can start a
process from a web request and serve subsequent requests
to report status on and show output for the process you started earlier.

Think of it as a way to monitor a long running command without
having to manage PIDs yourself. You can either start or join a
command (same executable, same args). Desub is not designed for running
multiple instances of the same command. You can just use a regular
subprocess for that.

.. contents::
    :local:

.. _`subprocess`: http://docs.python.org/library/subprocess.html

Installation
============

 ::

    pip install desub

This pulls in `psutil`_ as a requirement.

.. _psutil: http://code.google.com/p/psutil/

API
===

.. autofunction:: desub.join

.. autoclass:: desub.Desub
    :members: pid, stdout, stderr, start, stop, is_running

Developers
==========

Hello!
To work on this module, check out the `source from git`_ and be sure
you have the tox_ tool. To run the test suite, cd into the root and type::

    tox

This will run all tests in a virtualenv using the supported versions of Python.

To the build the docs run::

    pip install -r docs/requirements.txt
    make -C docs html

The issue tracker can be found on github.

.. _`source from git`: https://github.com/kumar303/desub
.. _tox: http://tox.testrun.org/latest/


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
