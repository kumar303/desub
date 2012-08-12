#!/user/bin/env python
import sys
import time

if __name__ == '__main__':
    sys.stdout.write('stdout')
    sys.stdout.flush()
    sys.stderr.write('stderr')
    sys.stderr.flush()
    while 1:
        time.sleep(1000)
