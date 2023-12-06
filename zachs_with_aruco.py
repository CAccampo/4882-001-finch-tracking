import cv2
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
from pyzbar import pyzbar
from google.cloud import bigquery
import random
from datetime import datetime, timedelta


def calculate_corners(x, y, w, h):
    half_w = w // 2 #takes half of the wdith
    half_h = h // 2 #takes half of the height

    # uses hw and 
    top_left = (x - half_w, y - half_h)
    top_right = (x + half_w, y - half_h)
    bottom_left = (x - half_w, y + half_h)
    bottom_right = (x + half_w, y + half_h)

    return (top_left, top_right, bottom_left, bottom_right)


test_data = generate_test_data(100)

def insert_data_into_bigquery(row, client):

    project_id = 'finch-project-399922'
    dataset_id = 'finch_beta_table'
    table_id = 'finch_positional_table'

    dataset_ref = client.dataset(dataset_id, project=project_id)
    table_ref = dataset_ref.table(table_id)
    table = client.get_table(table_ref)

    errors = client.insert_rows_json(table, row)
    print(1)
    if errors:
        print("Errors occurred while inserting rows: {}".format(errors))
    else:
        print("Successfully inserted rows.")


def read_barcodes(frame, client, camera_id):
    aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)  #this is changeable for the size of the Arucos (currently 6x6)
    parameters = cv2.aruco.DetectorParameters_create()
    corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  #gets current timestamp down to milliseconds up to 3 digits

    if ids is not None:
        print(ids)
        for i in range(len(ids)):
            marker_corners = corners[i][0]  #extracting the corner coordinates from the first element of corners

            #write bounding boxes
            cv2.polylines(frame, [marker_corners], True, (0, 255, 0), 2)

            #display row that will be uploaded
            print(f"| ArUco Marker ID: {ids[i][0]} | Timestamp: {timestamp} | Camera ID: {camera_id} | Corners: {marker_corners} |")

            row_to_insert = [ids[i][0], timestamp, camera_id, marker_corners]
            insert_data_into_bigquery(row_to_insert, client)

    return frame



def main():

    camera = PiCamera()
    camera_id = 1 #just setting this for testing for now
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))
    time.sleep(0.1)

    client = bigquery.Client()

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        image = read_barcodes(image, client, camera_id)
        cv2.imshow("Barcode/QR Code Reader", image)
        rawCapture.truncate(0)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()