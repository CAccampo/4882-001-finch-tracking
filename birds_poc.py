import cv2
from pyzbar.pyzbar import decode
from google.cloud import bigquery
from datetime import datetime
import threading
import time
client = bigquery.Client()
table_id = "finch_beta_table"
batched_data = []
data_lock = threading.Lock()
upload_interval = 5 * 60  

def insert_rows_to_bigquery():
    while True:
        time.sleep(upload_interval)
        with data_lock:
            if not batched_data:
                continue
            data_to_insert = batched_data.copy()
            batched_data.clear()
        rows_to_insert = [{"qr_data": data, "timestamp": timestamp} for data, timestamp in data_to_insert]
        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            print("Encountered errors while inserting rows: {}".format(errors))
def main():
    upload_thread = threading.Thread(target=insert_rows_to_bigquery, daemon=True)
    upload_thread.start()
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')
            print("QR Data: ", qr_data)
            with data_lock:
                batched_data.append((qr_data, datetime.utcnow()))

       
        cv2.imshow("QR Code Scanner", frame)

        # Breaks loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
