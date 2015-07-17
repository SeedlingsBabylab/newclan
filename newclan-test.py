import sys
import os
import csv
import re

re1='((?:[a-z][a-z0-9_]*))' # the word
re2='(\\s+)'	        # whitespace
re3='(&)'	            # &
re4='(.)'	            # utterance_type
re5='(\\|)'	            # |
re6='(.)'	            # object_present
re7='(\\|)'	            # |
re8='((?:[a-z][a-z0-9_]*))' # speaker

class Clan:

    def __init__(self, path):
        entry_regx = re.compile(re1+re2+re3+re4+re5+re6+re7+re8, re.IGNORECASE | re.DOTALL)
        interval_regx = re.compile("(\d+_\d{3,})")

        self.clan_file = path
        self.words = []


    def parse_words(self):

        with open(self.clan_file) as file:

            for line in file:
                if line.startswith("*")


class Cha:

    def __init__(self, path):
        entry_regx = re.compile(re1+re2+re3+'(&=)'+re4+'(_)'+re6+'(_)'+re8)
        interval_regx = re.compile("(\d+_\d{3,})")

        self.words = []



def print_usage():
    print "USAGE:"
    print "python newclan-test.py old_clan new_cha"

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print_usage()
