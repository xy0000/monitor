#!/usr/bin/env python

import psutil

print(psutil.cpu_count())
print(psutil.cpu_count(False))
print(psutil.cpu_freq())

print(psutil.pid_exists())
