import sys
import time
import traceback
import greenlet
import gevent.hub

# The maximum amount of time that the eventloop can be blocked
# without causing an error to be logged, in seconds.

MAX_BLOCKING_TIME = 0.01

# A global variable for tracking the time of the last greenlet switch.
# For server processes that use a single OS-level thread, a global works fine.
# You might like to use a threadlocal for complicated setups.

_last_switch_time = None

# A trace function that gets executed on every greenlet switch.
# It checks how much time has elapsed and logs an error if it was excessive.
# The Hub gets an exemption, because it's allowed to block on I/O.

def switch_time_tracer(what, (origin, target)):
    global _last_switch_time
    then = _last_switch_time
    now = _last_switch_time = time.time()
    if then is not None:
        blocking_time = now - then
        if origin is not gevent.hub.get_hub():
            if blocking_time > MAX_BLOCKING_TIME:
                msg = "Greenlet blocked the eventloop for %.4f seconds\n"
                msg = msg % (blocking_time, )
                print >> sys.stderr, msg
                traceback.print_stack()


greenlet.settrace(switch_time_tracer)