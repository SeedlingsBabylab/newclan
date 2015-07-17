import sys
import os
import csv




def print_usage():
    print "USAGE:"
    print "python newclan-test.py old_clan new_cha"

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print_usage()
