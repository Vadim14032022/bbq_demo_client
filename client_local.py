import os
import shutil
import yaml
import threading
import sys

import numpy as np
import time


REMOTE_PATH = "/home/docker_user/BeyondBareQueries"
INTERVAL = 1

# not important ->
IMAGE_PATH = "input_data/rgb.png"
DEPTH_PATH = "input_data/depth.png"
TRANSLATION_PATH = "input_data/translation.txt"
ORIENTAION_PATH = "input_data/orientation.txt"
POSE_PATH = "input_data/pose.txt"
#<-

REMOTE_FILES = {
"RELEVANT_OBJECTS_3D": "/home/docker_user/BeyondBareQueries/outputs/3d_relevant_objects.gif",
"RELEVANT_OBJECTS_2D": "/home/docker_user/BeyondBareQueries/outputs/overlayed_masks_sam_and_graph_relevant_objects.png",
"RELEVANT_OBJECTS_TEXT": "/home/docker_user/BeyondBareQueries/outputs/relevant_objects.txt",
"RELEVANT_OBJECTS_TABLE": "/home/docker_user/BeyondBareQueries/outputs/table_relevant_objects.json",

"FINAL_ANSWER_3D": "/home/docker_user/BeyondBareQueries/outputs/3d_final_answer.gif",
"FINAL_ANSWER_2D": "/home/docker_user/BeyondBareQueries/outputs/overlayed_masks_sam_and_graph_final_answer.png",
"FINAL_ANSWER_TEXT": "/home/docker_user/BeyondBareQueries/outputs/final_answer.txt",
"FINAL_ANSWER_TABLE": "/home/docker_user/BeyondBareQueries/outputs/table_final_answer.json",
}

LOCAL_FILES = {
"RELEVANT_OBJECTS_3D": "outputs/3d_relevant_objects.gif",
"RELEVANT_OBJECTS_2D": "outputs/overlayed_masks_sam_and_graph_relevant_objects.png",
"RELEVANT_OBJECTS_TEXT": "outputs/relevant_objects.txt",
"RELEVANT_OBJECTS_TABLE": "outputs/table_relevant_objects.json",

"FINAL_ANSWER_3D": "outputs/3d_final_answer.gif",
"FINAL_ANSWER_2D": "outputs/overlayed_masks_sam_and_graph_final_answer.png",
"FINAL_ANSWER_TEXT": "outputs/final_answer.txt",
"FINAL_ANSWER_TABLE": "outputs/table_final_answer.json",
}

def send_data(text,  ssh=None, image_path=None, depth_path=None, pose_path=None):
    with open(os.path.join(REMOTE_PATH, "text.txt"), "w") as f:
        f.write(text)

    with open("user_query.txt", "w") as f:
        f.write(text)

def get_remote_file_timestamp(remote_path):
    if os.path.exists(remote_path):
        return int(os.path.getmtime(remote_path))
    return None

def main(args=None):
    last_mtimes = {key: get_remote_file_timestamp(path) for key, path in REMOTE_FILES.items()}
    while True:
        user_input = input("Your input here:")
        if user_input.lower() == "exit":
            break

        send_data(user_input)

        updated_files = set()
        while True:
            time.sleep(INTERVAL)
            for key, path in REMOTE_FILES.items():
                current_mtime = get_remote_file_timestamp(path)
                if current_mtime != last_mtimes[key]:
                    last_mtimes[key] = current_mtime
                    print(f"Change detected! Downloading {path}...")
                    shutil.copy(path, LOCAL_FILES[key])
                    updated_files.add(path)
                    print(f"File {len(updated_files)}/{len(REMOTE_FILES)} copied to {LOCAL_FILES[key]}")

            if len(updated_files) == len(REMOTE_FILES):
                break

if __name__ == '__main__':
    main()
