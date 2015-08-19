import os
import sys


if __name__ == "__main__":
    for root, dirs, files in os.walk("."):
        print root
        print dirs
        print files
        print
        if root == ".":
            continue
        else:
            for directory in dirs:
                print "rename_root: {}".format(root)
                os.rename(os.path.join(root, directory),
                          os.path.join(root, directory.replace("01_", root[0:5])))



