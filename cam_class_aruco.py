import cv2
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
from pyzbar import pyzbar
from google.cloud import bigquery
import random
from datetime import datetime, timedelta
import threading

class Camera:
    def __init__(self, camera_id):
        #cam identification params
        self.camera_id = camera_id
        self.client = client
        self.terminal_lock = threading.Lock()

        #BigQuery init values
        #(**NOTE** These values need to be changed for new BQ table See datatypes line 92)
        self.project_id = 'finch-project-399922'
        self.dataset_id = 'finch_beta_table'
        self.table_id = 'finch_positional_table'
        self.client, self.table = self.initialize_bigquery(self.project_id, self.dataset_id)

        #camera setup
        self.camera = camera_setup()



    def initialize_bigquery(self, project_id, dataset_id, table_id):
        client = bigquery.Client(project=project_id) #setup the BQ

        #these setup the actual table
        dataset_ref = client.dataset(dataset_id, project=project_id)
        table_ref = dataset_ref.table(table_id)
        table = client.get_table(table_ref)

        return client, table


    def insert_data_into_bigquery(self, row):
        errors = self.client.insert_rows_json(table, row)
        if errors:
            print("Errors occurred while inserting rows: {}".format(errors))
        else:
            print("Successfully inserted rows.")


    def camera_setup(self):
        camera = PiCamera() #initialize the picamera
        camera.resolution = (640, 480)
        camera.framerate = 32
        rawCapture = PiRGBArray(camera, size=(640, 480))
        time.sleep(0.1)

        return camera


    def read_frames(self):
        for frame in self.camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            image = frame.array #convert the image to an array
            image = self.read_barcodes(image) #read all barcodes in that frame
            cv2.imshow("Barcode/QR Code Reader", image)
            rawCapture.truncate(0)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cv2.destroyAllWindows()


    def read_barcodes(self, frame):
        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)  #this is changeable for the size of the Arucos (currently 6x6)
        parameters = cv2.aruco.DetectorParameters_create()
        corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters) #returns 
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  #gets current timestamp down to milliseconds up to 3 digits

        if ids is not None:
            print(ids)
            for i in range(len(ids)):
                marker_corners = corners[i][0]  #extracting the corner coordinates from the first element of corners

                #write bounding boxes
                cv2.polylines(frame, [marker_corners], True, (0, 255, 0), 2)

                #display row that will be uploaded
                print(f"| ArUco Marker ID: {ids[i][0]} | Timestamp: {timestamp} | Camera ID: {camera_id} | Corners: {marker_corners} |")

                '''
                Data types for BQ schema:
                id: int
                timestamp: datetime
                camera_id: int
                marker_corners: array
                '''

                row_to_insert = [ids[i][0], timestamp, camera_id, marker_corners]
                self.insert_data_into_bigquery(row_to_insert)

        return frame


if __name__ == '__main__':
    cam_1 = Camera(1)
    cam_1.read_frames()
