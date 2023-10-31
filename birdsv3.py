import cv2
import queue
import threading
import numpy as np
import time
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account

# CALIBRATION_IMAGE_PATH = ["/app/calib_img.png"]
CALIBRATION_IMAGE_PATH = ["Sprint3/calib_img.png"]
UPLOAD_INTERVAL = 10
NUM_CAMERAS = 1
# credentials = service_account.Credentials.from_service_account_file(
#         '/app/finch-project-399922-0196b8dd1667.json'
#     )

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
        self.qr_code_detector = cv2.QRCodeDetector()

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
        table_name = 'finch_v4_table'
        # client = bigquery.Client(project=project_id, credentials = credentials)
        client = bigquery.Client(project=project_id)
        try:
            table = client.get_table(f"{project_id}.{dataset_id}.{table_name}")
            print(f"Uqing existing table: {table_name}")
        except Exception as e:
            schema = [
            bigquery.SchemaField("camera_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("data", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("corner_points", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("distance", "FLOAT", mode="REQUIRED")
        ]
            table = bigquery.Table(f"{project_id}.{dataset_id}.{table_name}", schema=schema)
            table = client.create_table(table)
            print(f"Created table: {table_name}")
        return client, table

    def detect_qr_codes(self, frame):
        retval, decoded_info, points, _ = self.qr_code_detector.detectAndDecodeMulti(frame)
        decoded_objects = []
        if retval:
            for info, point in zip(decoded_info, points):
                decoded_objects.append((info, point))
        return decoded_objects

    def calculate_distance(self, obj_real_size, undistorted_coords):
        obj_pixel_size = self.obj_pixel_size(undistorted_coords)
        if obj_pixel_size == 0:
            distance = 3.5
        else: 
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

            decoded_objects = self.detect_qr_codes(frame)
            if not decoded_objects:
                continue  # Skip printing if no QR codes are detected

            print(f'Camera {self.camera_id}: Detected QR codes')

            for obj in decoded_objects:
                data, points = obj
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")
                corner_points = ' '.join([f'({x}, {y})' for x, y in points])

                if data in self.distance_dict and corner_points == self.distance_dict[data][0]:
                    distance = self.distance_dict[data][1]
                    # if distance > 1000:
                    #     distance = 0
                
                else:
                    undistorted_coordinates = cv2.undistortPoints(np.array([points[0]], dtype='float32'),
                                                                 self.camera_matrix, self.dist_coeffs)
                    distance = self.calculate_distance(self.obj_real_size, undistorted_coordinates)
                    if distance > 1000:
                        distance = 3.5
                    self.distance_dict[data] = [corner_points, distance]

                with self.data_lock:
                    self.batched_data.append({
                        "camera_id": str(self.camera_id),
                        "timestamp": timestamp,
                        "data": data,
                        "corner_points": corner_points,
                        "distance": distance
                    })

            self.frame_queue.task_done()

    def upload_data(self):
        while True:
            time.sleep(UPLOAD_INTERVAL)  # Sleep for UPLOAD_INTERVAL seconds before proceeding
            with self.data_lock:
                if not self.batched_data:
                    continue

                data_to_insert = self.batched_data.copy()
                self.batched_data.clear()

            try:
                errors = self.client.insert_rows_json(self.table, data_to_insert)
                if errors:
                    print(f"Encountered errors while inserting rows: {errors}")
                else:
                    print(f"Data successfully uploaded to {self.table.table_id} at {datetime.utcnow().isoformat()}")
            except Exception as e:
                print(f"Failed to upload data: {str(e)}")

if __name__ == "__main__":
    frame_queues = [queue.Queue(maxsize=1) for _ in range(NUM_CAMERAS)]  # Set maxsize to 1
    camera_processors = [CameraProcessor(i, frame_queues[i], 'finch-project-399922', 'finch_beta_table') for i in range(NUM_CAMERAS)]

    cap = cv2.VideoCapture(1)
    try:
        while True:
            for i in range(NUM_CAMERAS):
                ret, frame = cap.read()
                if ret:
                    if not frame_queues[i].empty():
                        try:
                            frame_queues[i].get_nowait()  # Remove old frame if exists
                        except queue.Empty:
                            pass
                    frame_queues[i].put(frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        for processor in camera_processors:
            processor.stop_processing()
        cap.release()
        cv2.destroyAllWindows()