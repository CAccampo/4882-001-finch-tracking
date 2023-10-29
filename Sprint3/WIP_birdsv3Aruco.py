import cv2
import queue
import threading
import numpy as np
import time
from datetime import datetime
from google.cloud import bigquery

CALIBRATION_IMAGE_PATH = ["Sprint3\calib_img.png"]
UPLOAD_INTERVAL = 10
NUM_CAMERAS = 1

#setup dictionary and params for aruco detection
ARU_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
ARU_PARAMS = cv2.aruco.DetectorParameters()

class CameraProcessor:
    def __init__(self, camera_id, frame_queue, project_id, dataset_id):
        self.camera_id = camera_id
        self.frame_queue = frame_queue
        self.project_id = project_id
        self.dataset_id = dataset_id

        self.distance_dict = {}
        self.terminal_lock = threading.Lock()
        self.chessboard_size = (7, 6)
        self.image_paths = CALIBRATION_IMAGE_PATH
        self.fx, self.fy, self.cx, self.cy, self.dist_coeffs = self.calibrate_camera()
        self.batched_data = []
        self.data_lock = threading.Lock()
        self.client, self.table = self.initialize_bigquery(self.project_id, self.dataset_id)
        self.camera_matrix = np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]], dtype=np.float32)
        self.obj_real_size = 20
        self.aruco_detector = cv2.aruco.ArucoDetector(ARU_DICT, ARU_PARAMS)

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

        for image_path in self.image_paths:
            image = cv2.imread(image_path)
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
        table_name = 'new_coords_table'
        client = bigquery.Client(project=project_id)
        try:
            table = client.get_table(f"{project_id}.{dataset_id}.{table_name}")
            print(f"Using existing table: {table_name}")
        except Exception as e:
            table = client.create_table(
                bigquery.Table(f"{project_id}.{dataset_id}.{table_name}"),
                schema=[bigquery.SchemaField("camera_id", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("data", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("corner_points", "STRING", mode="REQUIRED"),
                        bigquery.SchemaField("distance", "FLOAT", mode="REQUIRED")
                        ],
                exists_ok=True
            )
            print(f"Created table: {table_name}")
        return client, table

    def detect_qr_codes(self, frame):
        return self.aruco_detector.detectMarkers(frame)

    def calculate_distance(self, obj_real_size, undistorted_coords):
        obj_pixel_size = self.obj_pixel_size(undistorted_coords)
        distance = (obj_real_size * self.fx) / obj_pixel_size
        print('aaaaaaaaa')
        print(obj_pixel_size, obj_real_size, self.fx, distance)
        return distance

    def obj_pixel_size(self, undistorted_coords):
        rect = cv2.minAreaRect(undistorted_coords)
        width = rect[1][0]
        height = rect[1][1]
        print('cccccc')
        print(rect, width, height)
        obj_pixel_size = max(width, height)
        return obj_pixel_size

    def init_heatmap(self):
        #determine w/h of camera image with test frame
        frame = self.frame_queue.get()

        #create blank white image of same size
        heatmap_img = np.ones(frame.shape, dtype = np.uint8)
        return 255*heatmap_img
    
    def draw_heatmap(self, center_point, data, heatmap_img):
        #opencv doesnt like variable colors so here we are
        #NEED TO MAKE DOT COLORS MORE DISTINCT
        dot_colors = (51,51,51)
        dot_colors = tuple(int(data*inc) for inc in dot_colors)
        print(dot_colors)

        return cv2.circle(heatmap_img, tuple(center_point.round().astype(int)), radius=0, color=dot_colors, thickness=-5)

    def process_frames(self):
        heatmap_img = self.init_heatmap()
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
                    data = data[0]

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")

                    corner_points = ' '.join([f'({x}, {y})' for x, y in points])
                    
                    heatmap_img = self.draw_heatmap(points.mean(0), data, heatmap_img)
                    cv2.imwrite('heatmap.png', heatmap_img) 
                    
                    if data in self.distance_dict and corner_points == self.distance_dict[data][0]:
                        distance = self.distance_dict[data][1]
                    else:
                        undistorted_coordinates = cv2.undistortPoints(np.array([points], dtype='float32'),
                                                                    self.camera_matrix, self.dist_coeffs)
                        print('bbbbbbbbbbbbb')
                        print(undistorted_coordinates, points)
                        distance = self.calculate_distance(self.obj_real_size, undistorted_coordinates)
                        self.distance_dict[data] = [corner_points, distance]

                    with self.data_lock:
                        self.batched_data.append({
                            "camera_id": str(self.camera_id),
                            "timestamp": timestamp,
                            "data": data,
                            "corner_points": corner_points,
                            "distance": distance
                        })
                        print(f"| {self.camera_id:10} | {timestamp:30} | {data:9}  | {corner_points:30} | {distance:.2f} mm")
                        

            print('|', ' ' * 87, '|')
            print('-' * 89)

            self.frame_queue.task_done()

    def stop_processing(self):
        self.frame_queue.put(None)
        self.processing_thread.join()
        self.upload_thread.join()

    def upload_data(self):
        while True:
            time.sleep(UPLOAD_INTERVAL)
            with self.data_lock:
                if not self.batched_data:
                    continue
                data_to_insert = self.batched_data.copy()
                self.batched_data.clear()

            errors = self.client.insert_rows_json(self.table, data_to_insert)
            if errors:
                print(f"Encountered errors while inserting rows: {errors}")
            else:
                print(f"Data uploaded to {self.table.table_id} at {datetime.utcnow().isoformat()}")

if __name__ == "__main__":
    frame_queues = [queue.Queue() for _ in range(NUM_CAMERAS)]
    camera_processors = [CameraProcessor(i, frame_queues[i], 'finch-project-399922', 'finch_beta_table') for i in range(NUM_CAMERAS)]

    caps = [cv2.VideoCapture(i) for i in range(NUM_CAMERAS)]

    try:
        while True:
            for i in range(NUM_CAMERAS):
                ret, frame = caps[i].read()
                if ret:
                    frame_queues[i].put(frame)

                if frame_queues[i].qsize() > 1:
                    frame_queues[i].get()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass

    for processor in camera_processors:
        processor.stop_processing()

    for cap in caps:
        cap.release()
