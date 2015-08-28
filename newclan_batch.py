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

files_processed_count = 0

total_files = 0

visit_log_path = "/Volumes/seedlings/Subject_Info_and_Paperwork/subject_visit_dates_forAndrei.csv"

visit_log = {}  # key   = subject
                # value = visit

not_processed = []

found_cha = []  # key   = subject
                # value = file

def build_command_set():
    for i in range(1,47):
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
        else:
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

def count_files():
    global total_files
    for key, value in commands:
        if key[0:2] == "05":
            continue
        if int(key[2:5]) > 12:
            continue
        else:
            total_files += 1

def set_outputs():
    for key, value in commands.iteritems():
        if value[1] == None:
            continue
        silences_split = os.path.split(value[1])
        merge_path = os.path.join(silences_split[0], silences_split[1][0:5] + "_newclan_merged.cha")
        value[3] = merge_path


def run_batch_newclan(commands):
    global files_processed_count
    base = ["python", "newclan.py"]
    with open("not_batch_processed.txt", "w") as errors:
        with open("batch_processed.txt", "w") as processed:
            for key, value in commands.iteritems():
                if None in value:
                    errors.write(key+"\n")
                    continue
                else:
                    command = base + value
                    abbrev_command = [os.path.split(element)[1] for element in command]
                    print "command: {}".format(abbrev_command)
                    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)
                    pipe.communicate()  # blocks until the subprocess in complete
                    processed.write(key+":\tcommand: {}\n".format(abbrev_command))
                    files_processed_count += 1

def export_command_set():
    with open("commands.txt", "w") as file:
        for key, values in commands.iteritems():
            abbrev_values = [os.path.split(value)[1] for value in values if value is not None]
            file.write("{}:  {}\n".format(key, abbrev_values))

def read_visit_log():
    with open(visit_log_path, "rU") as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            visit_log[int(row[0])] = row[1:]


def compare_visit_log_and_outputs():
    temp = []
    with open("not_batch_processed.txt") as file:
        for line in file:
            if int(line.strip()[0:2]) < 46:
                not_processed.append(line.strip())


    for visit in not_processed:
        if visit_log[int(visit[0:2])][visit_to_index(visit[3:])] is not '':
            temp.append(visit)

    for visit in temp:
        if visit not in found_cha:
            problem_files.append(visit)

    print problem_files

def visit_to_index(visit):
    if visit == '06':
        return 0
    elif visit == '07':
        return 1
    elif visit == '08':
        return 2
    elif visit == '09':
        return 3
    elif visit == '10':
        return 4
    elif visit == '11':
        return 5
    elif visit == '12':
        return 6
    elif visit == '13':
        return 7
    elif visit == '14':
        return 8
    elif visit == '15':
        return 9
    elif visit == '16':
        return 10
    elif visit == '17':
        return 11
    elif visit == '18':
        return 12

if __name__ == "__main__":

    # fill the command dictionary with all the subject_visit keys
    # and reserve a 4 item list as its value (for the 4 arguments
    # required by newclan.py)

    read_visit_log()

    print "Building command set...\n"
    build_command_set()


    print "Traversing Subject_Files for files...\n\n"

    for root, dirs, files in os.walk("/Volumes/seedlings/Subject_Files"):

        if os.path.split(root)[1] == "Audio_Annotation":
            for file in files:
                if ".cha" in file:
                    found_cha.append(file[0:5])

            cex_files = [file for file in files if ".cex" in file and not file.startswith(".")]
            #print cex_files
            for file in cex_files:
                # case where "final" is missing from filename and
                # it's the only .cex file in Audio_Annotations
                if (len(cex_files) == 1) and ".cex" in file:
                    commands[file[0:5]][1] = os.path.join(root, file)
                if "consensus_final" in file and not file.startswith(".") and ".cex" in file:
                    commands[file[0:5]][1] = os.path.join(root, file)
                    continue
                if "consensus" in file and not file.startswith(".") and ".cex" in file:
                    commands[file[0:5]][1] = os.path.join(root, file)
                    continue
                if "_final" in file and not file.startswith(".") and ".cex" in file:
                    commands[file[0:5]][1] = os.path.join(root, file)

        if os.path.split(root)[1] == "Audio_Files":
            for file in files:
                if "silences_added" in file and not file.startswith("."):
                    if commands[file[0:5]][0] is not None:
                        if "subregions" in commands[file[0:5]][0]:
                            continue
                        else:
                            commands[file[0:5]][0] = os.path.join(root, file)
                    else:
                        commands[file[0:5]][0] = os.path.join(root, file)
                if "subregions" in file and not file.startswith(".") and ".cex" in file:
                    commands[file[0:5]][0] = os.path.join(root, file)
                if ".lena.cha" in file and not file.startswith("."):
                    commands[file[0:5]][2] = os.path.join(root, file)



    print "done with directory scan....\n"
    set_outputs()
    export_command_set()
    print "done setting outputs....\n\n"

    print "running batch newclan.py on available files....\n\n"

    run_batch_newclan(commands)

    compare_visit_log_and_outputs()

    print "Total # of clan files converted: {}".format(files_processed_count)

