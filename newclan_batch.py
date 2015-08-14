import os
import csv
import re
#
#   Subject_Files directory structure:
#
#
#
#                                   Subject_Files
#             /              /           |              \           \
# 1_02-30-2001   2_07-33-2001     3_07-35-2001     4_07-32-2001    5_07-44-2001
#                              /    /   |  \  \ \
#                            3_6  3_8  3_11 .........
#                                     /   \
#                                   /     \___________________
#                                 /                          \
#                           Home_Visit                   In-Lab_Visit
#                         /  \       \                   |          \
#                       /    \       \                  |           \
#              Analysis     Coding   Processing       Eyetracking   Stimuli
#               /   \             \            \
#             /     \              \            \
# Audio_Analysis    Video_Analysis  \            \
#                                    \            \
#                                    \             \___________
#                                    \                         \
#                                    \                       __\_____________
#                                    \                      /                \
#                                    \              Video_Files              Audio_Files (original .cex is here)
#                                    \                                          \
#                                    \                                     _____\________________________________________
#                                    \                                    /     \                        \               \
#                                    \                                 /       \                        \                \
#                                    \                               /         \                        \                 \
#                                    \                           3_11.cex   3_11_silences_added.cex   3_11_lena5min.csv    3_11.its
#                                    \
#                                    \
#                                    \
#                                    \
#                       _____________\_________________________________
#                      /          /                \                 \
#                    /          /                  \                 \
#          Audio_Annotation  Audio_Transcription   Video_Annotation   Video_Transcription
#
#                ^
#               |
#           (annotated
#            .cex is
#              here)

problem_files = []
all_files = []

if __name__ == "__main__":

    for root, dirs, files in os.walk("/Volumes/seedlings/Subject_Files"):
        print "root:    " + str(root)
        print "dirs:    " + str(dirs)
        print "files:   " + str(files)
        print

        if os.path.split(root)[1] == "Audio_Files":
            for file in files:
                if ".cex" in file:
                    all_files.append(file)
                    print "all_files so far: " + str(all_files) + "\n\n"
