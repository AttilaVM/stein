#!/usr/bin/python
import time
from pyo import *

s=Server(nchnls=2, duplex=0)
# s.setInOutDevice(0)
s.boot()
s.start()

time.sleep(10)
