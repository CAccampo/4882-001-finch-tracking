import cv2
import queue
import threading
import numpy as np
import time
from datetime import datetime
from google.cloud import bigquery
from SetupConfig import win_loop
import json
import os
from SetupBirdConfig import load_config


# Load configuration from JSON file
config = load_config('config.json')

# quick fix to format chessboard type correctly from config)
config['chessboard_size'] = [eval(i) for i in config['chessboard_size'].split()]

def cvt_id(data):
    bird_config = load_config('bird_config.json')
    cvt_data = bird_config.get(str(data))
    if cvt_data is not None:
        print(f'Converted detected Code {data} to Bird ID {cvt_data}')
        return cvt_data
    else:
        print(f'Code {data} not found in Bird IDs')
        return data

class CameraProcessor:
    def __init__(self, camera_id, frame_queue):
        self.camera_id = camera_id
        self.frame_queue = frame_queue

        self.distance_dict = {}
        self.terminal_lock = threading.Lock()
        self.chessboard_size = tuple(config['chessboard_size'])
        self.image_paths = config['calibration_image_paths']
        self.fx, self.fy, self.cx, self.cy, self.dist_coeffs = self.calibrate_camera()
        self.batched_data = []
        self.data_lock = threading.Lock()
        self.client, self.table = self.initialize_bigquery(config['bigquery_project_id'], config['bigquery_dataset_id'])
        self.camera_matrix = np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]], dtype=np.float32)
        self.obj_real_size = config['obj_real_size']
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        self.upload_thread = threading.Thread(target=self.upload_data, daemon=True)
        self.upload_thread.start()
        print(f'Model Loaded for Camera {self.camera_id}')
        self.processing_thread = threading.Thread(target=self.process_frames)
        self.processing_thread.start()

    def calibrate_camera(self):
        obj_points = []  
        img_points = []  
        objp = np.zeros((self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboard_size[0], 0:self.chessboard_size[1]].T.reshape(-1, 2)

        image = cv2.imread(self.image_paths)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
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

    def initialize_bigquery(self, project_id, dataset_id):
        table_name = config['table_name']
        client = bigquery.Client(project=project_id)
        try:
            table = client.get_table(f"{project_id}.{dataset_id}.{table_name}")
            print(f"Using existing table: {table_name}")
        except Exception as e:
            table = bigquery.Table(f"{project_id}.{dataset_id}.{table_name}",
            schema=[bigquery.SchemaField("camera_id", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("data", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("corner_points", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("distance", "FLOAT", mode="REQUIRED")
                        ]
            )
            table = client.create_table(table)
            print(f"Created table: {table_name}")
        return client, table

    def detect_qr_codes(self, frame):
        return self.aruco_detector.detectMarkers(frame)

    def calculate_distance(self, obj_real_size, undistorted_coords):
        obj_pixel_size = self.obj_pixel_size(undistorted_coords)
        distance = (obj_real_size * self.fx) / obj_pixel_size
        return distance

    def obj_pixel_size(self, undistorted_coords):
        rect = cv2.minAreaRect(undistorted_coords)
        width = rect[1][0]
        height = rect[1][1]
        obj_pixel_size = max(width, height)
        return obj_pixel_size
    

    def process_frames(self):
        while True:
            frame = self.frame_queue.get()
            if frame is None:
                break

            aru_points, aru_decoded, rejected_marker = self.detect_qr_codes(frame)

            print('-' * 89)
            print('|', ' ' * 87, '|')
            
            if aru_decoded is not None:
                for index, data in enumerate(aru_decoded):
                    points = np.int32(aru_points)[index][0]
                    #.item() needed to convert numpy inc to int bc dump to json does not like numpy
                    data = data[0].item()
                    data = cvt_id(data)

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")

                    corner_points = ' '.join([f'({x}, {y})' for x, y in points])

                    if data in self.distance_dict and corner_points == self.distance_dict[data][0]:
                        distance = self.distance_dict[data][1]
                    else:
                        undistorted_coordinates = cv2.undistortPoints(np.array([points], dtype='float32'),
                                                                    self.camera_matrix, self.dist_coeffs)
                        distance = self.calculate_distance(self.obj_real_size, undistorted_coordinates)
                        self.distance_dict[data] = [corner_points, distance]

                    with self.data_lock:
                        try:
                            self.batched_data.append({
                                "camera_id": str(self.camera_id),
                                "timestamp": str(timestamp),
                                "data": str(data),
                                "corner_points": str(corner_points),
                                "distance": str(distance)
                            })
                        except Exception as E:
                            print(Exception)
                        print(f"| {self.camera_id} | {timestamp} | {data} | {corner_points} | {distance} mm")

            print('|', ' ' * 87, '|')
            print('-' * 89)

            self.frame_queue.task_done()

    def stop_processing(self):
        self.frame_queue.put(None)
        self.processing_thread.join()
        self.upload_thread.join()

    def upload_data(self):
        while True:
            time.sleep(5)
            with self.data_lock:
                if not self.batched_data:
                    break
                data_to_insert = self.batched_data.copy()
                self.batched_data.clear()
            errors = self.client.insert_rows_json(self.table, data_to_insert)
            if errors:
                print(f"Encountered errors while inserting rows: {errors}")
            else:
                print(f"Data uploaded to {self.table.table_id} at {datetime.utcnow().isoformat()}")

def main():
    win_loop()
    frame_queues = [queue.Queue() for _ in range(config['num_cameras'])]

    camera_processors = [CameraProcessor(i, frame_queues[i]) for i in range(config['num_cameras'])]

    caps = [cv2.VideoCapture(i) for i in range(config['num_cameras'])]

    try:
        while True:
            for i in range(config['num_cameras']):
                ret, frame = caps[i].read()
                if ret:
                    frame_queues[i].put(frame)

                if frame_queues[i].qsize() > 1:
                    frame_queues[i].get()

    except KeyboardInterrupt:
        print('Keyboard Interrupt; closing threads...')
        pass
    for processor in camera_processors:
        processor.stop_processing()

    for cap in caps:
        cap.release()
