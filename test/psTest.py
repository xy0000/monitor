#!/usr/bin/env python
import commands
import re

cmd = "ps -ef"

code, out = commands.getstatusoutput(cmd)

# print(code)
# print(out)
a = []

for i in out.split("\n"):
    if re.search("^root ", i):
        if re.search("falcon", i):
            a.append(i)

print(a)
print(len(a))

