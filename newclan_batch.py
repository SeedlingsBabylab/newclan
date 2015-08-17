import os
import csv
import re
import subprocess as sp

problem_files = []
all_files = []

consensus_files = []
silences_files = []
# each command requires 4 arguments:
#
#   [[silences_added.cex],   [annotated_cex],   [cha_skeleton],   [output_path]]
#
# commands is a dictionary with file_id's for keys
# (e.g. '01_06') and command arguments for values
commands = {}

def build_command_set():
    for i in range(50):
        if i < 10:
            commands["0{}_06".format(i)] = [None] * 4
            commands["0{}_07".format(i)] = [None] * 4
            commands["0{}_08".format(i)] = [None] * 4
            commands["0{}_09".format(i)] = [None] * 4
            commands["0{}_10".format(i)] = [None] * 4
            commands["0{}_11".format(i)] = [None] * 4
            commands["0{}_12".format(i)] = [None] * 4
            commands["0{}_13".format(i)] = [None] * 4
            commands["0{}_14".format(i)] = [None] * 4
            commands["0{}_15".format(i)] = [None] * 4
            commands["0{}_16".format(i)] = [None] * 4
            commands["0{}_17".format(i)] = [None] * 4
            commands["0{}_18".format(i)] = [None] * 4

        commands["{}_06".format(i)] = [None] * 4
        commands["{}_07".format(i)] = [None] * 4
        commands["{}_08".format(i)] = [None] * 4
        commands["{}_09".format(i)] = [None] * 4
        commands["{}_10".format(i)] = [None] * 4
        commands["{}_11".format(i)] = [None] * 4
        commands["{}_12".format(i)] = [None] * 4
        commands["{}_13".format(i)] = [None] * 4
        commands["{}_14".format(i)] = [None] * 4
        commands["{}_15".format(i)] = [None] * 4
        commands["{}_16".format(i)] = [None] * 4
        commands["{}_17".format(i)] = [None] * 4
        commands["{}_18".format(i)] = [None] * 4

def set_outputs():
    for key, value in commands.iteritems():
        if value[1] == None:
            continue
        silences_split = os.path.split(value[1])
        merge_path = os.path.join(silences_split[0], silences_split[1][0:5] + "_merged.cha")
        value[3] = merge_path

def run_batch_newclan(commands):
    base = ["python", "newclan.py"]
    with open("not_processed.txt", "w") as errors:
        for key, value in commands.iteritems():
            if None in value:
                errors.write(key+"\n")
                continue
            else:
                command = base + value
                print "command: {}".format(command)

if __name__ == "__main__":

    # fill the command dictionary with all the subject_visit keys
    # and reserve a 4 item list as its value (for the 4 arguments
    # required by newclan.py)

    build_command_set()

    for root, dirs, files in os.walk("/Volumes/seedlings/Subject_Files"):


        # print "root:    " + str(root)
        # print "dirs:    " + str(dirs)
        # print "files:   " + str(files)
        # print


        if os.path.split(root)[1] == "Audio_Annotation":
            for file in files:
                if "consensus_final" in file and not file.startswith("."):
                    commands[file[0:5]][1] = os.path.join(root, file)
                    #consensus_files.append(file)
                    #print "consensus_files so far: {}".format(consensus_files)
        if os.path.split(root)[1] == "Audio_Files":
            for file in files:
                if "silences_added" in file and not file.startswith("."):
                    commands[file[0:5]][0] = os.path.join(root, file)
                    #silences_files.append(file)
                if ".lena.cha" in file and not file.startswith("."):
                    commands[file[0:5]][2] = os.path.join(root, file)
                # if ".cex" in file:
                #     all_files.append(file)
                #     print "all_files so far: " + str(all_files) + "\n\n"

    print "done with directory scan....\n"
    set_outputs()
    print "done setting outputs....\n\n"

    print "running batch newclan.py on available files....\n\n"

    run_batch_newclan(commands)

