import sys
import os

print(sys.argv[0].split("/")[-1])

print(os.path.dirname(os.path.abspath(sys.argv[0])) + '/log')

