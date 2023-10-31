import cv2
from pyzbar.pyzbar import decode
from datetime import datetime
import pyzbar
import queue
import threading
import numpy as np
import torch
from transformers import AutoModelForDepth, AutoFeature
from PIL import Image

class CameraProcessor:
    def __init__(self, camera_id, frame_queue):
        self.camera_id = camera_id
        self.frame_queue = frame_queue
        self.distance_dict = {}
        self.terminal_lock = terminal_lock

        #camera calibration parameters
        self.chessboard_size = (7, 6) #chessboard size here is literally the amount of squares width x the amount of squares height ex: "tuple(5, 7)"
        self.image_paths = ["CALBRATION_IMAGE_PATH"] #replace with actual paths
        self.fx, self.fy, self.cx, self.cy, self.dist_coeffs = self.calibrate_camera()

        #load MIDAS model
        self.midas_model = AutoModelForDepth.from_pretrained("intel-isl/MiDaS")
        print(f'Model Loaded for Camera {self.camera_id}')

        self.processing_thread = threading.Thread(target=self.process_frames)
        self.processing_thread.start()

    '''
    This part of the code is simply for detecting the distances within the frames
    The "calibrate_camera" function just calibrates some camera settings to check for distortion
    To do the calibration I am using a distortion test using a chessboard which is computer vision industry standard calibration testing
    The "calculate distance" function calculates the distance from the camera to the qr code given the distortion as input
    The "calculate_depth" function uses the midas model to do distoration pixel depth calculation (this is a pretrained huggingface model)
    '''
    def calibrate_camera(self):
        obj_points = []  #3D points in the real world
        img_points = []  #2D points in the image plane
        objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)

        for image_path in self.image_paths:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            #find chessboard corners
            ret, corners = cv2.findChessboardCorners(gray, self.chessboard_size, None)

            if ret:
                obj_points.append(objp)
                img_points.append(corners)

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray.shape[::-1], None, None)

        fx = mtx[0, 0]
        fy = mtx[1, 1]
        cx = mtx[0, 2]
        cy = mtx[1, 2]

        return fx, fy, cx, cy, dist

    def calculate_cam_distance(self, undistorted_coordinates, depth):
        x, y = undistorted_coordinates[0][0], undistorted_coordinates[0][1]
        x_3d = (x - self.cx) * depth / self.fx
        y_3d = (y - self.cy) * depth / self.fy
        z_3d = depth
        return np.sqrt(x_3d**2 + y_3d**2 + z_3d**2)

    def calculate_depth(self, frame):
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        image = image.resize((384, 384))
        feature = AutoFeature.from_dict(self.midas_model.preprocess(image))

        #ensure you have the correct camera_matrix and dist_coeffs
        camera_matrix = np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]], dtype=np.float32)

        #calculate undistorted coordinates and depth
        obj = decode(frame, symbols=[pyzbar.pyzbar.ZBarSymbol.QRCODE])[0]
        undistorted_coordinates = cv2.undistortPoints(np.array([obj.rect.center], dtype='float32'), camera_matrix, self.dist_coeffs)

        depth = self.calculate_depth(frame)
        distance = self.calculate_cam_distance(undistorted_coordinates, depth)
        return obj, distance


    '''
    This is the actual function thread that will detect the QR codes and output the lines into the terminal
    It works using pyzbar and then logs them using a timestep and camera id
    It works by taking frames from the queue
    '''
    def process_frames(self):
        while True:
            frame = self.frame_queue.get()
            if frame is None:
                break

            decoded_objects = decode(frame, symbols=[pyzbar.pyzbar.ZBarSymbol.QRCODE])

            #lines 99  -> 138 are just for outputing the lines nicely in the terminal as rows
            print('-' * 89)
            print('|', ' ' * 87, '|')

            for obj in decoded_objects:
                data = obj.data.decode('utf-8')
                qr_code_type = obj.type
                points = obj.polygon
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")

                corner_points = ' '.join([f'({x}, {y})' for x, y in points])


                '''
                this conditional below is used to not have to reclaulate the distance to a qr code if the position within the frame has not changed
                the items stored in the dictionary and key:data and value:list where the list is ["corner_points", distance]
                '''
                if data in self.distance_dict.keys():
                    if corner_points == self.distance_dict[data][0]:
                        distance = self.distance_dict[data][1]
                    else:
                        #undistort pixel coordinates of the QR center
                        undistorted_coordinates = cv2.undistortPoints(
                            np.array([obj.rect.center], dtype='float32'), np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]], dtype=np.float32), self.dist_coeffs)

                        depth = self.calculate_depth(frame)
                        distance = self.calculate_cam_distance(undistorted_coordinates, depth)
                        self.distance_dict[data] = [corner_points, distance]
                else:
                    undistorted_coordinates = cv2.undistortPoints(
                        np.array([obj.rect.center], dtype='float32'), np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]], dtype=np.float32), self.dist_coeffs)

                    depth = self.calculate_depth(frame)
                    distance = self.calculate_cam_distance(undistorted_coordinates, depth)
                    self.distance_dict[data] = [corner_points, distance]

                
                print(f"| {self.camera_id:10} | {timestamp:30} | {data:9}  | {corner_points:30} | {distance:.2f} mm")

            print('|', ' ' * 87, '|')
            print('-' * 89)

            self.frame_queue.task_done()

    def stop_processing(self):
        self.frame_queue.put(None)
        self.processing_thread.join()

if __name__ == "__main":
    num_cameras = 4
    frame_queues = [queue.Queue() for _ in range(num_cameras)]
    terminal_lock = threading.Lock()
    camera_processors = [CameraProcessor(i, frame_queues[i], terminal_lock) for i in range(num_cameras)]

    caps = [cv2.VideoCapture(i) for i in range(num_cameras)]

    try:
        while True:
            for i in range(num_cameras):
                ret, frame = caps[i].read()
                if ret:
                    frame_queues[i].put(frame)

                if frame_queues[i].qsize() > 1:
                    frame_queues[i].get()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass  # Exit gracefully on Ctrl+C

    for processor in camera_processors:
        processor.stop_processing()

    for cap in caps:
        cap.release()
