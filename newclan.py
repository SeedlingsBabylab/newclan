import sys
import os
import re
import collections

participants = "@Participants:\tSIL Silence LENA, MAN Male_Adult_Near Male,  MAF Male_Adult_Far Male, FAN\n\
\tFemale_Adult_Near Female, FAF Female_Adult_Far Female, CHN Key_Child_Clear Target_Child, CHF\n\
\tKey_Child_Unclear Target_Child, CXN Other_Child_Near Child, CXF Other_Child_Far Child, NON\n\
\tNoise_Near LENA, NOF Noise_Far LENA, OLN Overlap_Near LENA, OLF Overlap_Far LENA, TVN\n\
\tElectronic_Sound_Near Media, TVF Electronic_Sound_Far Media\n"

class ClanFile:
    def __init__(self, orig_clanpath, annot_clanpath, its_path, out_path):
        self.original = orig_clanpath
        self.path = annot_clanpath
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

        if not self.check_intervals():
            return
        self.parse_clan_words_comments()
        self.merge_its_and_clan()

    def parse_clan_words_comments(self):
        """
        Reads all the annotated words in a CLAN file
        and fills a list of tuples with the word and onset/offsets
        :return:
        """
        last_line = ""
        multi_line = ""
        prev_interval = [None, None]
        curr_interval = [None, None]

        with open(self.path, "rU") as clan_file:
            for index, line in enumerate(clan_file):

                if line.startswith("*"):

                    multi_line = ""
                    # parse out the line interval
                    interval_reg_result = self.interval_regx.search(line)

                    # if the line starts with a "*" and there is no
                    # interval on the line (regex search returned None),
                    # it must be on a following line. We save the previous
                    # line and move forward
                    if interval_reg_result is None:
                        #print "interval regex was none, clan line: " + str(index)
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
                    # parse out the line interval
                    interval_reg_result = self.interval_regx.search(line)

                    # if the line starts with a "\t" and there is no
                    # interval on the line (regex search returned None),
                    # it must be on a following line. We save the previous
                    # line and move forward
                    if interval_reg_result is None:
                        multi_line += line
                        continue

                    line = last_line + multi_line + line
                    #print line

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

        self.grouped_words = self.chunk_words(self.words)
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

        curr_interval = [0, 0]
        prev_interval = [0, 0]

        broken_interval = None

        prev_line = ""
        with open(self.its_path, "rU") as its_file:
            with open(self.out_path, "w") as output:
                for index, line in enumerate(its_file):
                    # in the case where we have adjacent comments, we check against
                    # the last interval again, since it hasn't been updated yet (previous
                    # line was a comment too)
                    if (curr_interval[0] == curr_comment[1] or
                        curr_interval[0] == curr_comment[1] - 1 or
                        curr_interval[0] == curr_comment[1] + 1):

                        if "subregion" in curr_comment[0] or\
                             "silence" in curr_comment[0]:
                            curr_interval[1] = curr_comment[2]

                            sil_subr_comment = re.sub(r"%com:\s+", r"%xcom:\t", curr_comment[0])

                            silsubr_comment_ready = True
                            if comments:
                                curr_comment = comments.popleft()
                        else:

                            regular_comment = re.sub(r"%com:\s+", r"%xcom:\t", curr_comment[0])

                            regular_comment_ready = True
                            if comments:
                                curr_comment = comments.popleft()

                    # if subregion/silence/regular comment is ready to write,
                    # write it out and reset the flag
                    if silsubr_comment_ready:
                        output.write(sil_subr_comment.replace("\t ", "\t"))
                        comment_written_cnt += 1
                        silsubr_comment_ready = False
                    if regular_comment_ready:
                        output.write(regular_comment)
                        comment_written_cnt += 1
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
                        #print curr_interval

                        if curr_interval[0] == curr_comment[1]:
                            if "subregion" in curr_comment[0] or\
                                 "silence" in curr_comment[0]:

                                curr_interval[1] = curr_comment[2]
                                sil_subr_comment = re.sub(r"%com:\s+", r"%xcom:\t", curr_comment[0])
                                silsubr_comment_ready = True
                                if comments:
                                    curr_comment = comments.popleft()
                            else:

                                regular_comment = re.sub(r"%com:\s+", r"%xcom:\t", curr_comment[0])
                                regular_comment_ready = True
                                if comments:
                                    curr_comment = comments.popleft()

                        # special case where single interval in .cex is broken
                        # across multiple intervals in .cha
                        # if (prev_interval[1] == words[0][4] and
                        #     curr_interval[0] == words[0][5]):
                        #     #print "found broken interval: " + str(curr_interval)

                        if (self.intervals_match(prev_interval, curr_interval, words)):

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
                            prev_interval[0] = curr_interval[0]
                            prev_interval[1] = curr_interval[1]
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

                                else:
                                    regular_comment = curr_comment[0].replace("%com", "%xcom")
                                    regular_comment_ready = True
                                    if comments:
                                        curr_comment = comments.popleft()

                            # special case where single interval in .cex is broken
                            # across multiple intervals in .cha
                            # if (prev_interval[1] == words[0][4] and
                            #     curr_interval[0] == words[0][5]):
                            #     #print "found broken interval: " + str(curr_interval)

                            if (self.intervals_match(prev_interval, curr_interval, words)):

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


        # print "\n\n# of comments written: " + str(comment_written_cnt)
        # print "total # of comments: " + str(len(self.comments))
        # print "# of words parsed: " + str(len(self.words))

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
        for index, word in enumerate(words):
            if prev_word is None:
                temp_group.append(word)
                prev_word = word
                continue
            if word[4] != prev_word[4]:
                result.append(temp_group)
                temp_group = []
                temp_group.append(word)
                prev_word = word
                if index == len(words) - 1: # that was the last word, put it in the results immediately
                    result.append(temp_group)
            else:
                temp_group.append(word)
        return result

    def check_intervals(self):
        parse_orig_cex(self.original)
        parse_annot_cex(self.path)

        result = compare_intervals(self.id, orig_cex_intervals, annot_cex_intervals)
        return result

    def intervals_match(self, prev_interval, curr_interval, words_interval):
        """
        Checks if the current interval being processed is matched with
        the current word(s) that's waiting to be written in.

        :param prev_interval: previous interval we just passed
        :param curr_interval: current interval being handled
        :param words_interval: the "words" entry that's been popped off the deque
        :return: True if matched, False if not
        """
        if ((curr_interval[0] == words_interval[0][4] and   # perfect match
            curr_interval[1] == words_interval[0][5]) or


            # all the possible +/- 1ms rounding errors
            ((curr_interval[0] - 1) == words_interval[0][4] and
             (curr_interval[1] - 1) == words_interval[0][5]) or

            (curr_interval[0] == words_interval[0][4] and
             (curr_interval[1] - 1) == words_interval[0][5]) or

            ((curr_interval[0] - 1) == words_interval[0][4] and
             curr_interval[1] == words_interval[0][5]) or

            ((curr_interval[0] + 1) == words_interval[0][4] and
             (curr_interval[1] + 1) == words_interval[0][5]) or

            ((curr_interval[0] + 1) == words_interval[0][4] and
             curr_interval[1] == words_interval[0][5]) or

            (curr_interval[0] == words_interval[0][4] and
             (curr_interval[1] + 1) == words_interval[0][5]) or


            # all the +/- 25ms errors
            ((curr_interval[0] - 25) == words_interval[0][4] and
             (curr_interval[1] - 25) == words_interval[0][5]) or

            (curr_interval[0] == words_interval[0][4] and
             (curr_interval[1] - 25) == words_interval[0][5]) or

            ((curr_interval[0] - 25) == words_interval[0][4] and
             curr_interval[1] == words_interval[0][5]) or

            ((curr_interval[0] + 25) == words_interval[0][4] and
             (curr_interval[1] + 25) == words_interval[0][5]) or

            ((curr_interval[0] + 25) == words_interval[0][4] and
             curr_interval[1] == words_interval[0][5]) or

            (curr_interval[0] == words_interval[0][4] and
             (curr_interval[1] + 25) == words_interval[0][5]) or


            # all the +/- 15ms errors
            ((curr_interval[0] - 15) == words_interval[0][4] and
             (curr_interval[1] - 15) == words_interval[0][5]) or

            (curr_interval[0] == words_interval[0][4] and
             (curr_interval[1] - 15) == words_interval[0][5]) or

            ((curr_interval[0] - 15) == words_interval[0][4] and
             curr_interval[1] == words_interval[0][5]) or

            ((curr_interval[0] + 15) == words_interval[0][4] and
             (curr_interval[1] + 15) == words_interval[0][5]) or

            ((curr_interval[0] + 15) == words_interval[0][4] and
             curr_interval[1] == words_interval[0][5]) or

            (curr_interval[0] == words_interval[0][4] and
             (curr_interval[1] + 15) == words_interval[0][5]) or

            # single .cex interval broken across 2 .cha intervals
            (prev_interval[1] == words_interval[0][4] and
             curr_interval[0] == words_interval[0][5])):
            return True
        else:
            return False






# code from clan_intervals:
#
# (makes sure intervals haven't been changed
#  between original .cex and the annotated .cex)
#

interval_regx = re.compile("(\025\d+_\d+)")

orig_cex_intervals = []
annot_cex_intervals = []

adjusted_timestamps = []    # timestamps that were rewritten because of silences/subregions

def parse_orig_cex(path):
    with open(path, "rU") as file:
        for index, line in enumerate(file):
            interv_reg_result = interval_regx.findall(line)
            if interv_reg_result:
                if len(interv_reg_result) > 1:
                    print "More than one interval on a line:  line# " + str(index)
                    return
                for interval_str in interv_reg_result:
                    interval = [None, None]
                    interval_split = interval_str.replace("\025", "").split("_")
                    interval[0] = int(interval_split[0])
                    interval[1] = int(interval_split[1])
                    orig_cex_intervals.append(interval)
            else:
                continue

def parse_annot_cex(path):
    with open(path, "rU") as file:
        for index, line in enumerate(file):
            if line.startswith("%com:") and\
                ("silence" in line) or ("subregion" in line):
                adjusted_timestamps.append(annot_cex_intervals[-1])
            interv_reg_result = interval_regx.findall(line)
            if interv_reg_result:
                if len(interv_reg_result) > 1:
                    print "More than one interval on a line:  line# " + str(index)
                    return
                for interval_str in interv_reg_result:
                    interval = [None, None]
                    interval_split = interval_str.replace("\025", "").split("_")
                    interval[0] = int(interval_split[0])
                    interval[1] = int(interval_split[1])
                    annot_cex_intervals.append(interval)
            else:
                continue

def compare_intervals(id, orig_cex_intervals, annot_cex_intervals):
    problems = []
    off_by_one_count = 0
    off_by_15_count = 0
    off_by_25_count = 0

    for index, interval in enumerate(orig_cex_intervals):

        # +/- 1
        plus_plus = [interval[0]+1, interval[1]+1]
        plus_same = [interval[0]+1, interval[1]]
        same_plus = [interval[0], interval[1]+1]

        minus_minus = [interval[0]-1, interval[1]-1]
        minus_same = [interval[0]-1, interval[1]]
        same_minus = [interval[0], interval[1]-1]

        # +/- 15
        plus_plus15 = [interval[0]+15, interval[1]+15]
        plus_same15 = [interval[0]+15, interval[1]]
        same_plus15 = [interval[0], interval[1]+15]

        minus_minus15 = [interval[0]-15, interval[1]-15]
        minus_same15 = [interval[0]-15, interval[1]]
        same_minus15 = [interval[0], interval[1]-15]


        # +/- 25
        plus_plus25 = [interval[0]+25, interval[1]+25]
        plus_same25 = [interval[0]+25, interval[1]]
        same_plus25 = [interval[0], interval[1]+25]

        minus_minus25 = [interval[0]-25, interval[1]-25]
        minus_same25 = [interval[0]-25, interval[1]]
        same_minus25 = [interval[0], interval[1]-25]



        off_by_ones = (plus_plus, plus_same, same_plus,     #  + 1
                       minus_minus, minus_same, same_minus) #  - 1

        off_by_15s = (plus_plus15, plus_same15, same_plus15,        #  + 15
                     minus_minus15, minus_same15, same_minus15)     # - 15

        off_by_25s = (plus_plus25, plus_same25, same_plus25,       #  + 25
                     minus_minus25, minus_same25, same_minus25)    #  - 25

        if interval not in annot_cex_intervals:
            off_by_one = False
            off_by_15 = False
            off_by_25 = False
            adjusted_by_comment = False

            # check for off by one
            for interv in off_by_ones:
                if interv in annot_cex_intervals:
                    #print "found off by one: " + str(interv)
                    off_by_one = True
                    off_by_one_count += 1

            for interv in off_by_15s:
                if interv in annot_cex_intervals:
                    off_by_15 = True
                    off_by_15_count += 1
                    #print "found off by 15:  {}".format(interv)

            for interv in off_by_25s:
                if interv in annot_cex_intervals:
                    off_by_25 = True
                    off_by_25_count += 1
                    #print "found off by 25:  {}".format(interv)

            # check for rewritten timestamp because of silence/subregion comment
            if interval[0] in [intrv[0] for intrv in adjusted_timestamps]:
                adjusted_by_comment = True

            if not (off_by_one or
                    off_by_15 or
                    off_by_25 or
                    adjusted_by_comment):
                problems.append(interval)

    if len(problems) > 0:
        # print "\nThere were some discrepancies between the original cex file"
        # print "and the annotated version. The intervals in the annotated"
        # print "version might have been altered."
        #
        # print "\n# off by ones: " + str(off_by_one_count)
        # print "\n# off by 25: " + str(off_by_25_count)
        # print "# otherwise inconsistent intervals: " + str(len(problems))
        # print "\nproblem intervals: " + str(problems)

        with open("error_files/"+ id +"_errors.txt", "w") as error_file:
            for problem_interval in problems:
                error_file.write(str(problem_interval) + "\n")

        return False
    return True

def print_usage():
    print "USAGE: \n"
    print "python newclan.py [original_cex] [annotated_cex] [its_skeleton] [output_dir]\n"


# original_cex = ""
# annotated_cex = ""
# cha_skeleton = ""
# output_path = ""
# error_path = ""

if __name__ == "__main__":

    if len(sys.argv) < 5:
        print_usage()
        sys.exit(0)

    # original_cex  = sys.argv[1] # original cex
    # annotated_cex = sys.argv[2] # annotated cex
    # cha_skeleton  = sys.argv[3] # its skeleton cha
    # output_path   = sys.argv[4]  # output path



    clan_file = ClanFile(sys.argv[1], # original cex
                         sys.argv[2], # annotated cex
                         sys.argv[3], # its skeleton cha
                         sys.argv[4]) # output path
