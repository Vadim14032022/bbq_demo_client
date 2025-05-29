import os
import yaml
import threading
import sys

import paramiko
import numpy as np
import time
from scp import SCPClient

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from sensor_msgs.msg import Image
from std_srvs.srv import Trigger
from cv_bridge import CvBridge
import cv2


with open("secrets.yaml") as stream:
    secrets = yaml.safe_load(stream)

HOST = secrets["HOST"]
PORT = secrets["PORT"]
USERNAME = secrets["USERNAME"]
PRIVATE_KEY_PATH = secrets["PRIVATE_KEY_PATH"]

REMOTE_PATH = "/home/jovyan/Tatiana_Z/bbq_demo/user_query/"
INTERVAL = 1

IMAGE_PATH = "input_data/rgb.png"
DEPTH_PATH = "input_data/depth.png"
TRANSLATION_PATH = "input_data/translation.txt"
ORIENTAION_PATH = "input_data/orientation.txt"
POSE_PATH = "input_data/pose.txt"

REMOTE_RELEVANT_OBJECTS_3D = "/home/jovyan/Tatiana_Z/bbq_demo/outputs/3d_relevant_objects.png"
REMOTE_RELEVANT_OBJECTS_2D = "/home/jovyan/Tatiana_Z/bbq_demo/outputs/overlayed_masks_sam_and_graph_relevant_objects.png"
REMOTE_RELEVANT_OBJECTS_TEXT = "/home/jovyan/Tatiana_Z/bbq_demo/outputs/relevant_objects.txt"

REMOTE_FINAL_ANSWER_3D = "/home/jovyan/Tatiana_Z/bbq_demo/outputs/3d_final_answer.png"
REMOTE_FINAL_ANSWER_2D = "/home/jovyan/Tatiana_Z/bbq_demo/outputs/overlayed_masks_sam_and_graph_final_answer.png"
REMOTE_FINAL_ANSWER_TEXT = "/home/jovyan/Tatiana_Z/bbq_demo/outputs/final_answer.txt"

LOCAL_RELEVANT_OBJECTS_3D = "3d_relevant_objects.png"
LOCAL_RELEVANT_OBJECTS_2D = "overlayed_masks_sam_and_graph_relevant_objects.txt"
LOCAL_RELEVANT_OBJECTS_TEXT = "relevant_objects.png"

LOCAL_FINAL_ANSWER_3D = "3d_final_answer.png"
LOCAL_FINAL_ANSWER_2D = "overlayed_masks_sam_and_graph_final_answer.png"
LOCAL_FINAL_ANSWER_TEXT = "final_answer.txt"


class RGBDImageSaver(Node):

    def __init__(self):
        super().__init__('rgbd_image_saver_service')
        self.bridge = CvBridge()

        # Subscriptions to RGB and Depth topics
        self.rgb_msg = None
        self.depth_msg = None

        self.rgb_sub = self.create_subscription(
            Image,
            # '/aima/hal/rgbd_camera/hand_left/color',  # Change if your RGB topic is different
            '/aima/hal/rgbd_camera/head_front/color',
            self.rgb_callback,
            10)

        self.depth_sub = self.create_subscription(
            Image,
            '/aima/hal/rgbd_camera/head_front/depth',
            self.depth_callback,
            10)

        # Service to trigger saving
        self.srv = self.create_service(Trigger, 'save_rgbd_images', self.save_callback)

        # Saving setup
        self.save_dir = 'input_data'
        os.makedirs(self.save_dir, exist_ok=True)
        self.image_counter = 0

    def rgb_callback(self, msg):
        self.rgb_msg = msg

    def depth_callback(self, msg):
        self.depth_msg = msg

    def save_images(self, user_trigger_time=None, timeout_sec=2.0):
        if self.rgb_msg is None or self.depth_msg is None:
            self.get_logger().warning("RGB or Depth image not received yet.")
            return False, "No images received yet"

        if user_trigger_time is not None:
            self.get_logger().info("Waiting for new RGB and Depth images...")
            start_time = time.time()

            # Spin until both new images arrive after user_trigger_time
            while True:
                rgb_time = Time.from_msg(self.rgb_msg.header.stamp)
                depth_time = Time.from_msg(self.depth_msg.header.stamp)

                print(rgb_time-user_trigger_time, depth_time-user_trigger_time)

                if rgb_time > user_trigger_time and depth_time > user_trigger_time:
                    break

                if time.time() - start_time > timeout_sec:
                    return False, "Timeout waiting for new RGB and Depth images after user trigger."

                rclpy.spin_once(self, timeout_sec=0.1)

        try:
            rgb_image = self.bridge.imgmsg_to_cv2(self.rgb_msg, desired_encoding='bgr8')
            depth_image = self.bridge.imgmsg_to_cv2(self.depth_msg, desired_encoding='passthrough')

            rgb_filename = os.path.join(self.save_dir, f'rgb.png')
            depth_filename = os.path.join(self.save_dir, f'depth.png')

            if depth_image.dtype == np.float32:
                depth_normalized = cv2.normalize(depth_image, None, 0, 65535, cv2.NORM_MINMAX)
                depth_to_save = depth_normalized.astype(np.uint16)
            else:
                depth_to_save = depth_image

            cv2.imwrite(rgb_filename, rgb_image)
            cv2.imwrite(depth_filename, depth_to_save)

            self.image_counter += 1
            msg = f"Saved RGB to {rgb_filename}, Depth to {depth_filename}"
            self.get_logger().info(msg)
            return True, msg

        except Exception as e:
            err = f"Error saving images: {e}"
            self.get_logger().error(err)
            return False, err

    # Used by the service
    def save_callback(self, request, response):
        success, msg = self.save_images()
        response.success = success
        response.message = msg
        return response


def quaternion_to_rotation_matrix(quaternion):
    Ox, Oy, Oz, Ow = quaternion[0], quaternion[1], quaternion[2], quaternion[3]
    # Compute squared terms
    xx, yy, zz = Ox * Ox, Oy * Oy, Oz * Oz
    xy, xz, yz = Ox * Oy, Ox * Oz, Oy * Oz
    wx, wy, wz = Ow * Ox, Ow * Oy, Ow * Oz

    # Rotation matrix
    R = np.array([
        [1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy)],
        [2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx)],
        [2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy)]
    ])
    return R

def get_image():
    """
    Get image from camera and return path to image
    """
    # placeholder function, replace by Zed software
    # image = camera_callback()
    # img = Image.fromarray(image)
    # img.save(os.path.join("input_data", f"rgb.png"))
    return IMAGE_PATH

def get_depth():
    # placeholder function, replace by Zed software
    """
    Get depth from camera and return path to depth
    """
    # depth = camera_callback()
    # img = Image.fromarray((depth*1000).astype(np.uint16), 'I;16')
    # img.save(os.path.join("input_data", f"depth.png"))
    return DEPTH_PATH

def get_pose():
    # placeholder function, replace by Zed software
    """
    Get translation and rotation from camera and return path to computed 4x4 pose
    """
    T = gripper_callback_translation()
    O = gripper_callback_orientation()
    T = np.expand_dims(T, axis=1)
    R = quaternion_to_rotation_matrix(O)
    Rt = np.hstack((R,T))
    pose = np.vstack((Rt, np.array([0.0, 0.0, 0.0, 1.0])))
    np.savetxt(POSE_PATH, pose)
    return POSE_PATH

def send_data(text, ssh, image_path=None, depth_path=None, pose_path=None):
    """Отправляет текст и изображение на сервер."""

    # Отправка изображения (если указано)
    if image_path and os.path.exists(image_path):
        sftp = ssh.open_sftp()
        sftp.put(image_path, f"{REMOTE_PATH}/image.png")
        sftp.close()

    # Отправка изображения (если указано)
    if depth_path and os.path.exists(depth_path):
        sftp = ssh.open_sftp()
        sftp.put(depth_path, f"{REMOTE_PATH}/depth.png")
        sftp.close()

    # Отправка изображения (если указано)
    # if pose_path and os.path.exists(pose_path):
    #     sftp = ssh.open_sftp()
    #     sftp.put(pose_path, f"{REMOTE_PATH}/pose.txt")
    #     sftp.close()

    # Отправка текста
    stdin, stdout, stderr = ssh.exec_command(f'echo "{text}" > {REMOTE_PATH}/text.txt')
    print(stdout.read().decode(), stderr.read().decode())

    with open('user_query.txt', 'w') as f:
        f.write(f'{text}')

def get_remote_file_timestamp(ssh_client, remote_path):
    stdin, stdout, stderr = ssh_client.exec_command(f'stat -c %Y "{remote_path}"')
    output = stdout.read().strip()
    return int(output) if output else None

def main(args=None):
    rclpy.init(args=args)
    node = RGBDImageSaver()

    # Start spinning in a separate thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()


    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, PORT, USERNAME, key_filename=PRIVATE_KEY_PATH)

    print(ssh)
    last_timestamp_final_answer = get_remote_file_timestamp(ssh, REMOTE_FINAL_ANSWER_2D)

    while True:
        user_input = input("Введите текст: ")
        #user_input = "Test sed"
        if user_input.lower() == "exit":
            break

        user_trigger_time = node.get_clock().now()
        node.save_images(user_trigger_time=user_trigger_time)
        image_path = get_image()
        depth_path = get_depth()
        # pose_path = get_pose()
        send_data(user_input, ssh, image_path, depth_path, None)

        while True:
            time.sleep(INTERVAL)
            new_timestamp = get_remote_file_timestamp(ssh, REMOTE_FINAL_ANSWER_2D)
            if new_timestamp and new_timestamp != last_timestamp_final_answer:
                print(f"Change detected! Downloading {REMOTE_FINAL_ANSWER_2D}...")
                with SCPClient(ssh.get_transport()) as scp:
                    scp.get(REMOTE_RELEVANT_OBJECTS_3D, LOCAL_RELEVANT_OBJECTS_3D)
                    scp.get(REMOTE_RELEVANT_OBJECTS_2D, LOCAL_RELEVANT_OBJECTS_2D)
                    scp.get(REMOTE_RELEVANT_OBJECTS_TEXT, LOCAL_RELEVANT_OBJECTS_TEXT)

                    scp.get(REMOTE_FINAL_ANSWER_3D, LOCAL_FINAL_ANSWER_3D)
                    scp.get(REMOTE_FINAL_ANSWER_2D, LOCAL_FINAL_ANSWER_2D)
                    scp.get(REMOTE_FINAL_ANSWER_TEXT, LOCAL_FINAL_ANSWER_TEXT)
                print(f"File copied to {REMOTE_FINAL_ANSWER_2D}")
                last_timestamp_final_answer = new_timestamp
                break

    # Shutdown
    node.destroy_node()
    rclpy.shutdown()
    spin_thread.join()

if __name__ == '__main__':
    main()