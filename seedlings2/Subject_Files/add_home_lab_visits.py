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
            print "current root: {}\n\n".format(root)
            for directory in dirs:
                os.mkdir(os.path.join(root,directory,"Home_Visit"))
                os.mkdir(os.path.join(root,directory,"In-Lab_Visit"))
                os.mkdir(os.path.join(root,directory,"Home_Visit/Analysis"))
                os.mkdir(os.path.join(root,directory,"Home_Visit/Coding"))
                os.mkdir(os.path.join(root,directory,"Home_Visit/Processing"))
                os.mkdir(os.path.join(root,directory,"In-Lab_Visit/Eyetracking"))
                os.mkdir(os.path.join(root,directory,"In-Lab_Visit/Stimuli"))
                os.mkdir(os.path.join(root,directory,"Home_Visit/Analysis/Audio_Analysis"))
                os.mkdir(os.path.join(root,directory,"Home_Visit/Analysis/Video_Analysis"))







                #
                # audio_analysis_leaf_path = os.path.join(root, directory, "Home_Visit/Analysis/Audio_Analysis")
                # video_analysis_leaf_path = os.path.join(root, directory, "Home_Visit/Analysis/Video_Analysis")
                # audio_annot_leaf_path = os.path.join(root, directory, "Home_Visit/Coding/Audio_Annotation")
                # audio_trans_leaf_path = os.path.join(root, directory, "Home_Visit/Coding/Audio_Transcription")
                # video_annot_leaf_path = os.path.join(root, directory, "Home_Visit/Coding/Video_Annotation")
                # video_trans_leaf_path = os.path.join(root, directory, "Home_Visit/Coding/Video_Transcription")
                # try:
                #     os.makedirs(audio_analysis_leaf_path)
                #     os.makedirs(video_analysis_leaf_path)
                #     os.makedirs(audio_annot_leaf_path)
                #     os.makedirs(audio_trans_leaf_path)
                #     os.makedirs(video_annot_leaf_path)
                #     os.makedirs(video_trans_leaf_path)
                # except OSError, e:
                #     if e.errno != 17:
                #         raise
                #     pass

