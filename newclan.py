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

        self.comments = []

        #re1='((?:[a-z][a-z]+))' # the word
        re1='((?:[a-z][a-z0-9_+]*))' # the word
        re2='(\\s+)'	        # whitespace
        re3='(&)'	            # &
        re4='(.)'	            # utterance_type
        re5='(\\|)'	            # |
        re6='(.)'	            # object_present
        re7='(\\|)'	            # |
        re8='((?:[a-z][a-z0-9_]*))' # speaker

        self.entry_regx = re.compile(re1+re2+re3+re4+re5+re6+re7+re8, re.IGNORECASE | re.DOTALL)
        self.interval_regx = re.compile("(\025\d+_\d+)")

        re9='(&)'	# Any Single Character 1
        re10='(=)'	# Any Single Character 2
        re11='(w)'	# Any Single Character 3
        re12='(\\d+)'	# Integer Number 1
        re13='(_)'	# Any Single Character 4
        re14='(\\d+)'	# Integer Number 2

        self.word_cnt_regx = re.compile(re9+re10+re11+re12+re13+re14,re.IGNORECASE|re.DOTALL)

        self.parse_clan_words_comments()
        self.merge_its_and_clan()

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
                        print "interval regex was none, clan line: " + str(index)
                        last_line = line
                        continue

                    # rearrange previous and current intervals
                    prev_interval[0] = curr_interval[0]
                    prev_interval[1] = curr_interval[1]

                    # set the new curr_interval
                    interval_str = interval_reg_result.group().replace("\025", "")
                    interval = interval_str.split("_")
                    curr_interval[0] = int(interval[0])
                    curr_interval[1] = int(interval[1])

                # this is for lines that wrapped around past a single line
                if line.startswith("\t"):
                    line = last_line + line

                # if there are "word &=d_y_BRO" entries within the line, parse them out
                entries = re.findall(self.entry_regx, line)

                # if there are entries on this line, fill them into self.words
                if entries:
                    for entry in entries:
                        self.words.append([entry[0],            # word
                                           entry[3],            # utterance_type
                                           entry[5],            # object_present
                                           entry[7],            # speaker
                                           curr_interval[0],    # onset
                                           curr_interval[1]])   # offset


                if line.startswith("%com:") and ("|" not in line):
                    self.comments.append((line, curr_interval[0], curr_interval[1]))

        print self.words
        self.grouped_words = self.chunk_words(self.words)
        print self.grouped_words
        print self.comments
        self.check_words()

    def merge_its_and_clan(self):
        comment_written_cnt = 0
        grouped_words = collections.deque(self.grouped_words)
        words = grouped_words.popleft()

        comments = collections.deque(self.comments)
        sil_subr_comment = ""
        regular_comment = ""
        curr_comment = comments.popleft()

        silsubr_comment_ready = False
        regular_comment_ready = False

        curr_interval = [None, None]
        prev_interval = [None, None]

        prev_line = ""

        with open(self.its_path, "rU") as its_file:
            with open(self.out_path, "w") as output:
                for index, line in enumerate(its_file):

                    # in the case where we have adjacent comments, we check against
                    # the last interval again, since it hasn't been updated yet (previous
                    # line was a comment too)
                    if curr_interval[0] == curr_comment[1]:
                        if "subregion" in curr_comment[0] or\
                             "silence" in curr_comment[0]:
                            curr_interval[1] = curr_comment[2]
                            sil_subr_comment = curr_comment[0].replace("%com", "%xcom")
                            silsubr_comment_ready = True
                            if comments:
                                curr_comment = comments.popleft()
                            print "curr_comment: " + str(curr_comment)
                        else:
                            regular_comment = curr_comment[0].replace("%com", "%xcom")
                            regular_comment_ready = True
                            if comments:
                                curr_comment = comments.popleft()
                            print "curr_comment: " + str(curr_comment)

                    # if subregion/silence/regular comment is ready to write,
                    # write it out and reset the flag
                    if silsubr_comment_ready:
                        output.write(sil_subr_comment.replace("\t ", "\t"))
                        comment_written_cnt += 1
                        print "wrote subregion:  " + sil_subr_comment
                        print "curr_interval: " + str(curr_interval)
                        silsubr_comment_ready = False
                    if regular_comment_ready:
                        output.write(regular_comment)
                        comment_written_cnt += 1
                        print "wrote regular comment:  " + regular_comment
                        print "curr_interval: " + str(curr_interval)
                        regular_comment_ready = False


                    # we skip over the birth date header
                    if line.startswith("@Birth"):
                        continue
                    # we just write out all the other headers
                    elif line.startswith("@"):
                        output.write(line)
                    # we write out all the clan/lena comments
                    elif line.startswith("%com:") and ("|" in line):
                        output.write(line)
                    # we write out all the decibel comments
                    elif line.startswith("%xdb:"):
                        output.write(line)
                    elif line.startswith("*"):
                        line_split = line.split()

                        # rearrange previous and current intervals
                        prev_interval[0] = curr_interval[0]
                        prev_interval[1] = curr_interval[1]

                        # parse out the new current line interval and set it
                        interval_str = self.interval_regx.search(line).group().replace("\025", "")
                        interval = interval_str.split("_")
                        curr_interval[0] = int(interval[0])
                        curr_interval[1] = int(interval[1])

                        if curr_interval[0] == curr_comment[1]:
                            if "subregion" in curr_comment[0] or\
                                 "silence" in curr_comment[0]:
                                curr_interval[1] = curr_comment[2]
                                sil_subr_comment = curr_comment[0].replace("%com", "%xcom")
                                silsubr_comment_ready = True
                                if comments:
                                    curr_comment = comments.popleft()
                                print "curr_comment: " + str(curr_comment)

                            else:
                                #output.write(curr_comment[0].replace("%com", "%xcom"))
                                regular_comment = curr_comment[0].replace("%com", "%xcom")
                                regular_comment_ready = True
                                if comments:
                                    curr_comment = comments.popleft()
                                print "curr_comment: " + str(curr_comment)



                        if curr_interval[0] == words[0][4] and\
                            curr_interval[1] == words[0][5]:

                            output.write(line_split[0] + "\t")

                            # write back all the special codes before writing our
                            # own annotations
                            if "&=vocalization" in line:
                                output.write("&=vocalization ")
                            if "&=vfx" in line:
                                output.write("&=vfx ")
                            if "&=crying" in line:
                                output.write("&=crying ")

                            # if there's an adult word count code in the line, write it out
                            word_count_reg_result = self.word_cnt_regx.search(line)
                            if word_count_reg_result:
                                output.write(word_count_reg_result.group() + " ")

                            # write all our entries for this interval
                            for entry in words:
                                output.write(entry[0] + " &={}_{}_{} ".format(entry[1], entry[2], entry[3]))

                            if "." not in line and not (silsubr_comment_ready or regular_comment_ready):
                                output.write(line_split[-1] + "\n")
                            else:
                                output.write(". " + line_split[-1] + "\n")
                            if grouped_words:
                                words = grouped_words.popleft()
                        else:
                            # if we're about to write a comment after the start of a multi line
                            # entry, then we need to add a "." on this line before going to the next
                            if "." not in line and (silsubr_comment_ready or regular_comment_ready):
                                output.write(line.replace("\025" + interval_str,
                                                      ". \025{}_{}".format(curr_interval[0],
                                                                     curr_interval[1])))
                            else:
                                output.write(line.replace(interval_str,
                                                          "{}_{}".format(curr_interval[0],
                                                                         curr_interval[1])))

                    elif line.startswith("\t"):
                        line_split = line.split()

                        interval_regx_result = self.interval_regx.search(line)

                        # if there is no other interval on the line, just write
                        # it out to the output .cha
                        if interval_regx_result is None:
                            output.write(line)
                        else:   # this is part of a multi line entry (with multiple intervals)
                            interval_str = interval_regx_result.group().replace("\025", "")
                            interval = interval_str.split("_")
                            curr_interval[0] = int(interval[0])
                            curr_interval[1] = int(interval[1])

                            if curr_interval[0] == curr_comment[1]:
                                if "subregion" in curr_comment[0] or\
                                     "silence" in curr_comment[0]:
                                    curr_interval[1] = curr_comment[2]
                                    sil_subr_comment = curr_comment[0].replace("%com", "%xcom")
                                    silsubr_comment_ready = True
                                    curr_comment = comments.popleft()
                                    print "curr_comment: " + str(curr_comment)

                                else:
                                    regular_comment = curr_comment[0].replace("%com", "%xcom")
                                    regular_comment_ready = True
                                    curr_comment = comments.popleft()
                                    print "curr_comment: " + str(curr_comment)

                            if curr_interval[0] == words[0][4] and\
                               curr_interval[1] == words[0][5]:

                                output.write("\t")

                                # write back all the special codes before writing our
                                # own annotations
                                if "&=vocalization" in line:
                                    output.write("&=vocalization ")
                                if "&=vfx" in line:
                                    output.write("&=vfx ")
                                if "&=crying" in line:
                                    output.write("&=crying ")

                                for entry in words:
                                    output.write(entry[0] + " &={}_{}_{} ".format(entry[1],
                                                                                  entry[2],
                                                                                  entry[3]))
                                if "." not in line:
                                    output.write(line_split[-1] + "\n")
                                else:
                                    output.write(". " + line_split[-1] + "\n")

                                if grouped_words:
                                    words = grouped_words.popleft()
                            else:
                                output.write(line)

        print "\n\n# of comments written: " + str(comment_written_cnt)
        print "total # of comments: " + str(len(self.comments))
    def check_words(self):
        """
        Makes sure formatting on entries is correct
        :return:
        """

        # make sure compound words only have the first
        # letter capitalized (if necessary)
        for entry in self.words:
            if "+" in entry[0] and entry[0][0].isupper():
                line = entry[0].lower()
                line = line[0].upper() + line[1:]
                print "line: " + line
                entry[0] = line

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
    print "python newclan.py input_clan its_skeleton output"



if __name__ == "__main__":

    if len(sys.argv) < 3:
        print_usage()

    clan_file = ClanFile(sys.argv[1], sys.argv[2], sys.argv[3])
