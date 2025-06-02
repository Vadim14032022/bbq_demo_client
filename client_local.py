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

REMOTE_RELEVANT_OBJECTS_3D = "/home/docker_user/BeyondBareQueries/outputs/3d_relevant_objects.gif"
REMOTE_RELEVANT_OBJECTS_2D = "/home/docker_user/BeyondBareQueries/outputs/overlayed_masks_sam_and_graph_relevant_objects.png"
REMOTE_RELEVANT_OBJECTS_TEXT = "/home/docker_user/BeyondBareQueries/outputs/relevant_objects.txt"
REMOTE_RELEVANT_OBJECTS_TABLE = "/home/docker_user/BeyondBareQueries/outputs/table_relevant_objects.json"

REMOTE_FINAL_ANSWER_3D = "/home/docker_user/BeyondBareQueries/outputs/3d_final_answer.gif"
REMOTE_FINAL_ANSWER_2D = "/home/docker_user/BeyondBareQueries/outputs/overlayed_masks_sam_and_graph_final_answer.png"
REMOTE_FINAL_ANSWER_TEXT = "/home/docker_user/BeyondBareQueries/outputs/final_answer.txt"
REMOTE_FINAL_ANSWER_TABLE = "/home/docker_user/BeyondBareQueries/outputs/table_final_answer.json"

LOCAL_RELEVANT_OBJECTS_3D = "3d_relevant_objects.gif"
LOCAL_RELEVANT_OBJECTS_2D = "overlayed_masks_sam_and_graph_relevant_objects.png"
LOCAL_RELEVANT_OBJECTS_TEXT = "relevant_objects.txt"
LOCAL_RELEVANT_OBJECTS_TABLE = "table_relevant_objects.json"

LOCAL_FINAL_ANSWER_3D = "3d_final_answer.gif"
LOCAL_FINAL_ANSWER_2D = "overlayed_masks_sam_and_graph_final_answer.png"
LOCAL_FINAL_ANSWER_TEXT = "final_answer.txt"
LOCAL_FINAL_ANSWER_TABLE = "table_final_answer.json"

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
    last_timestamp_final_answer = get_remote_file_timestamp(REMOTE_FINAL_ANSWER_TEXT)
    while True:
        user_input = input("Your input here:")
        if user_input.lower() == "exit":
            break

        send_data(user_input)

        while True:
            time.sleep(INTERVAL)
            new_timestamp = get_remote_file_timestamp(REMOTE_FINAL_ANSWER_TEXT)
            if new_timestamp != last_timestamp_final_answer:
                print(f"Change detected! Downloading {REMOTE_FINAL_ANSWER_TEXT}...")
                shutil.copy(REMOTE_RELEVANT_OBJECTS_3D, LOCAL_RELEVANT_OBJECTS_3D)
                shutil.copy(REMOTE_RELEVANT_OBJECTS_2D, LOCAL_RELEVANT_OBJECTS_2D)
                shutil.copy(REMOTE_RELEVANT_OBJECTS_TEXT, LOCAL_RELEVANT_OBJECTS_TEXT)
                shutil.copy(REMOTE_RELEVANT_OBJECTS_TABLE, LOCAL_RELEVANT_OBJECTS_TABLE)

                shutil.copy(REMOTE_FINAL_ANSWER_3D, LOCAL_FINAL_ANSWER_3D)
                shutil.copy(REMOTE_FINAL_ANSWER_2D, LOCAL_FINAL_ANSWER_2D)
                shutil.copy(REMOTE_FINAL_ANSWER_TEXT, LOCAL_FINAL_ANSWER_TEXT)
                shutil.copy(REMOTE_FINAL_ANSWER_TABLE, LOCAL_FINAL_ANSWER_TABLE)
                print(f"File copied to {REMOTE_FINAL_ANSWER_TEXT}")
                last_timestamp_final_answer = new_timestamp
                break

if __name__ == '__main__':
    main()
