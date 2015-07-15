import sys
import os
import re
import collections

participants = "@Participants:\tSIL Silence LENA, MAN Male_Adult_Near Male,  MAF Male_Adult_Far Male, FAN\n\
\tFemale_Adult_Near Female, FAF Female_Adult_Far Female, CHN Key_Child_Clear Target_Child, CHF\n\
\tKey_Child_Unclear Target_Child, CXN Other_Child_Near Child, CXF Other_Child_Far Child, NON\n\
\tNoise_Near LENA, NOF Noise_Far LENA, OLN Overlap_Near LENA, OLF Overlap_Far LENA, TVN\n\
\tElectronic_Sound_Near Media, TVF Electronic_Sound_Far Media\n"

ids = ["@ID:\teng|LENA|SIL|||||LENA||Silence|",
        "@ID:\teng|LENA|MAN|||||Male||Male_Adult_Near|",
        "@ID:\teng|LENA|MAF|||||Male||Male_Adult_Far|",
        "@ID:\teng|LENA|FAN|||||Female||Female_Adult_Near|",
        "@ID:\teng|LENA|FAF|||||Female||Female_Adult_Far|",
        "@ID:\teng|LENA|CHN|1;|female|||Target_Child||Key_Child_Clear|",
        "@ID:\teng|LENA|CHF|1;|female|||Target_Child||Key_Child_Unclear|",
        "@ID:\teng|LENA|CXN|||||Child||Other_Child_Near|",
        "@ID:\teng|LENA|CXF|||||Child||Other_Child_Far|",
        "@ID:\teng|LENA|NON|||||LENA||Noise_Near|",
        "@ID:\teng|LENA|NOF|||||LENA||Noise_Far|",
        "@ID:\teng|LENA|OLN|||||LENA||Overlap_Near|",
        "@ID:\teng|LENA|OLF|||||LENA||Overlap_Far|",
        "@ID:\teng|LENA|TVN|||||Media||Electronic_Sound_Near|",
        "@ID:\teng|LENA|TVF|||||Media||Electronic_Sound_Far|"
    ]

class ClanFile:
    def __init__(self, clan_path, its_path, out_path):
        self.path = clan_path
        self.its_path = its_path
        self.out_path = out_path
        self.id = os.path.split(self.path)[1][0:5]

        self.words = []     # list of (word, interval) tuples
        self.grouped_words = None

        re1='((?:[a-z][a-z]+))' # the word
        re2='(\\s+)'	        # whitespace
        re3='(&)'	            # &
        re4='(.)'	            # utterance_type
        re5='(\\|)'	            # |
        re6='(.)'	            # object_present
        re7='(\\|)'	            # |
        re8='((?:[a-z][a-z]+))' # speaker

        self.entry_regx = re.compile(re1+re2+re3+re4+re5+re6+re7+re8, re.IGNORECASE | re.DOTALL)
        self.interval_regx = re.compile("(\d+_\d{3,})")

        self.parse_clan_words_comments()
        self.merge_its_and_clan()

    def parse_clan(self):

        with open(self.path, "rU") as input_file:
            with open(self.out_path, "w") as output_file:
                output_file.write("@UTF8\n")
                output_file.write("@Begin\n")
                output_file.write("@Languages:\teng\n")
                output_file.write(participants)
                output_file.write("\n@Options:\tmulti\n")
                for id in ids:
                    output_file.write(id + "\n")
                media = os.path.split(self.path)[1][0:5]
                output_file.write("@Media:\t{}, audio".format(media))

                prev_line = ""
                for line in input_file:
                    if line.startswith("@New Episode:"):
                        output_file.write("\n" + line.replace("@New Episode:", "@Comment:"))

                    if line.startswith("*"):
                        line_split = line.split()

                        if len(line_split) == 2:    # empty
                            output_file.write(line_split[0] + "\t" + "0. " + line_split[1] + "\n")

                        entries = re.findall(self.entry_regx, line)
                        print entries

                        if entries:
                            output_file.write(line_split[0] + "\t")
                            for index, entry in enumerate(entries):
                                output_file.write(entry[0] + " &={}_{}_{}".format(entry[3], entry[5], entry[7] + " "))
                            output_file.write(". ")
                            output_file.write(line_split[-1] + "\n")
                        else:
                            output_file.write(line)
                        # if len(line_split) == 4:    #
                        #     output_file.write(line_split[0] + "\t" + line_split)

                    if line.startswith("%com:") and\
                        ("silence" not in line and "subregion" not in line):
                        output_file.write(line)

                    prev_line = line

                output_file.write("@End")

    def parse_clan_words_comments(self):
        """
        Reads all the annotated words in a CLAN file
        and fills a list of tuples with the word and onset/offsets
        :return:
        """

        last_line = ""
        prev_interval = [None, None]
        curr_interval = [None, None]

        with open(self.path, "rU") as clan_file:
            for index, line in enumerate(clan_file):

                if line.startswith("*"):
                    # parse out the line interval
                    interval_reg_result = self.interval_regx.search(line)

                    # if the line starts with a "*" and there is no
                    # interval on the line (regex search returned None),
                    # it must be on a following line. We save the previous
                    # line and move forward
                    if interval_reg_result is None:
                        print "interval regex was none"
                        last_line = line
                        continue

                    interval_str = interval_reg_result.group()
                    interval = interval_str.split("_")
                    curr_interval[0] = int(interval[0])
                    curr_interval[1] = int(interval[1])

                # this is for lines that wrapped around past a single line
                if not (line.startswith("*") or line.startswith("@")):
                    line = last_line + line

                # if there are "word &=d_y_BRO" entries within the line, parse them out
                entries = re.findall(self.entry_regx, line)

                # if there are entries on this line, fill them into self.words
                if entries:
                    for entry in entries:
                        self.words.append((entry[0],            # word
                                           entry[3],            # utterance_type
                                           entry[5],            # object_present
                                           entry[7],            # speaker
                                           curr_interval[0],    # onset
                                           curr_interval[1]))   # offset

                # if line.startswith("%com:") and ("|" not in line):


        print self.words
        self.grouped_words = self.chunk_words(self.words)
        print self.grouped_words

    def merge_its_and_clan(self):

        grouped_words = collections.deque(self.grouped_words)
        words = grouped_words.popleft()

        curr_interval = [None, None]
        prev_interval = [None, None]

        with open(self.its_path, "rU") as its_file:
            with open(self.out_path, "w") as output:
                for line in its_file:
                    if line.startswith("@"):
                        output.write(line)
                    # if line.startswith("@Participants"):
                    #     output.write(participants)
                    elif line.startswith("%com:") and ("|" in line):
                        output.write(line)
                    elif line.startswith("*"):
                        line_split = line.split()

                        # parse out the line interval
                        interval_str = self.interval_regx.search(line).group()
                        interval = interval_str.split("_")
                        curr_interval[0] = int(interval[0])
                        curr_interval[1] = int(interval[1])

                        if curr_interval[0] == words[0][4] and\
                            curr_interval[1] == words[0][5]:

                            output.write(line_split[0] + "\t")
                            for entry in words:
                                output.write(entry[0] + " &={}_{}_{} ".format(entry[1], entry[2], entry[3]))

                            output.write(". " + line_split[-1] + "\n")
                            words = grouped_words.popleft()
                        else:
                            output.write(line)
                    elif not (line.startswith("*") or\
                           line.startswith("@")):
                        output.write(line)

    def chunk_words(self, words):
        """
        Given a list of word entry tuples:

            (word, utterance_type, present, speaker, onset, offset)

        This function chunks them into a list of lists. Each inner list
        contains words that were in the same time interval. This arranges
        the words so that we can easily handle the case were there are
        multiple words per line.
        :return: list of lists containing words taken from clan file
        """

        result = []

        temp_group = []

        prev_word = None
        for word in words:
            if prev_word is None:
                temp_group.append(word)
                prev_word = word
                continue
            if word[4] != prev_word[4]:
                result.append(temp_group)
                temp_group = []
                temp_group.append(word)
                prev_word = word
            else:
                temp_group.append(word)

        return result
class ITSFile:

    def __init__(self, its_path, clan_path):
        self.path = its_path
        self.clan_path = clan_path

    # def parse_its(self):
    #
    #     with open(self.path, "rU") as  its_file:
    #         with open(self.clan_path) as clan_file:


def print_usage():
    print "USAGE: \n"
    print "python newclan.py input_clan its_file output"

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print_usage()

    clan_file = ClanFile(sys.argv[1], sys.argv[2], sys.argv[3])
