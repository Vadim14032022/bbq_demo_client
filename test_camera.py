import pyzed.sl as sl
import math
import numpy as np
import torch
import time

class TimestampHandler:
    def __init__(self):
        self.t_imu = sl.Timestamp()
        self.t_baro = sl.Timestamp()
        self.t_mag = sl.Timestamp()

    def is_new(self, sensor):
        if isinstance(sensor, sl.IMUData):
            new_ = (sensor.timestamp.get_microseconds() > self.t_imu.get_microseconds())
            if new_:
                self.t_imu = sensor.timestamp
            return new_
        elif isinstance(sensor, sl.MagnetometerData):
            new_ = (sensor.timestamp.get_microseconds() > self.t_mag.get_microseconds())
            if new_:
                self.t_mag = sensor.timestamp
            return new_
        elif isinstance(sensor, sl.BarometerData):
            new_ = (sensor.timestamp.get_microseconds() > self.t_baro.get_microseconds())
            if new_:
                self.t_baro = sensor.timestamp
            return new_

# Initialize ZED camera
zed = sl.Camera()
info = zed.get_camera_information()

# Create InitParameters object and set configuration parameters
init_params = sl.InitParameters()
init_params.sdk_verbose = 1  # Enable verbose logging
init_params.depth_mode = sl.DEPTH_MODE.ULTRA  # Use ULTRA depth mode
init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP  # Use a right-handed Y-up coordinate system
init_params.coordinate_units = sl.UNIT.METER  # Set units in meters
status = zed.open(init_params)

if status != sl.ERROR_CODE.SUCCESS:  # Ensure the camera has opened successfully
    print("Camera Open : " + repr(status) + ". Exit program.")
    exit()

# Enable positional tracking with default parameters
py_transform = sl.Transform()  # First create a Transform object for TrackingParameters object
tracking_parameters = sl.PositionalTrackingParameters(_init_pos=py_transform)
err = zed.enable_positional_tracking(tracking_parameters)
if err != sl.ERROR_CODE.SUCCESS:
    print("Enable positional tracking : " + repr(err) + ". Exit program.")
    zed.close()
    exit()

can_compute_imu = zed.get_camera_information().camera_model != sl.MODEL.ZED

# Create and set RuntimeParameters after opening the camera
zed_sensors = sl.SensorsData()
runtime_parameters = sl.RuntimeParameters()
ts_handler = TimestampHandler()
i = 0

# Data containers
data_dict = {
    'images': [],
    'depths': [],
    'point_clouds': [],
    'translations': [],
    'orientations': [],
    'imu_orientations': [],
    'imu_accelerations': [],
    'imu_angular_velocities': []
}

image = sl.Mat()
depth = sl.Mat()
point_cloud = sl.Mat()
zed_pose = sl.Pose()

while i < 50:
    # A new image is available if grab() returns SUCCESS
    if zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
        if zed.get_sensors_data(zed_sensors, sl.TIME_REFERENCE.CURRENT) == sl.ERROR_CODE.SUCCESS:
            # Check if the data has been updated since the last time
            if ts_handler.is_new(zed_sensors.get_imu_data()):
                # Retrieve left image
                zed.retrieve_image(image, sl.VIEW.LEFT)
                # Retrieve depth map. Depth is aligned on the left image
                zed.retrieve_measure(depth, sl.MEASURE.DEPTH)
                # Retrieve colored point cloud. Point cloud is aligned on the left image.
                zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA)
                zed.get_position(zed_pose, sl.REFERENCE_FRAME.WORLD)

                # Convert data to numpy arrays for saving
                image_np = image.get_data()  # Get image as NumPy array
                depth_np = depth.get_data()  # Get depth as NumPy array
                point_cloud_np = point_cloud.get_data()  # Get point cloud as NumPy array

                # Get translation and orientation
                py_translation = sl.Translation()
                translation = zed_pose.get_translation(py_translation).get()
                py_orientation = sl.Orientation()
                orientation = zed_pose.get_orientation(py_orientation).get()

                # Get IMU data
                zed_imu = zed_sensors.get_imu_data()
                acceleration = [0, 0, 0]
                zed_imu.get_linear_acceleration(acceleration)
                angular_velocity = [0, 0, 0]
                zed_imu.get_angular_velocity(angular_velocity)
                imu_orientation = zed_imu.get_pose(sl.Transform()).get_orientation().get()

                # Append data to the dictionary
                data_dict['images'].append(image_np.copy())  # Use .copy() to avoid overwriting
                data_dict['depths'].append(depth_np.copy())
                data_dict['point_clouds'].append(point_cloud_np.copy())
                data_dict['translations'].append(translation)
                data_dict['orientations'].append(orientation)
                data_dict['imu_orientations'].append(imu_orientation)
                data_dict['imu_accelerations'].append(acceleration)
                data_dict['imu_angular_velocities'].append(angular_velocity)

                i += 1

                print(f'Image: {i}')
                time.sleep(0.5)

# Save the collected data to a PyTorch .pt file
torch.save(data_dict, 'zed_data.pt')

# Close the camera
zed.close()