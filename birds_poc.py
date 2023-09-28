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
qcd = cv2.QRCodeDetector()
line_color = (0, 255, 0)

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

def draw_lines(frame, retval, decoded_list, points_list):
    if retval:
        for decoded_qr in decoded_list:
            frame = cv2.putText(frame, str(decoded_qr), (10,(decoded_list.index(decoded_qr)+1)*20), cv2.FONT_HERSHEY_PLAIN, 1, line_color, 2)
        for points in points_list:
            frame = cv2.polylines(frame, [points.astype(int)], True, line_color, 4)
    return frame
        

def main():
    upload_thread = threading.Thread(target=insert_rows_to_bigquery, daemon=True)
    upload_thread.start()
    cap = cv2.VideoCapture(0)
    display_select = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        retval, decoded_list, points, straight_qr = qcd.detectAndDecodeMulti(frame)
        if retval:
            for qr_data in decoded_list:
                if qr_data: #if able to decode
                    print("QR Data: ", qr_data)
                    with data_lock:
                        batched_data.append((qr_data, datetime.utcnow()))

        #keypress menu
        frame = cv2.putText(frame, "a - display", (540,450), cv2.FONT_HERSHEY_PLAIN, 1, line_color, 2)
        frame = cv2.putText(frame, "q - quit", (540,470), cv2.FONT_HERSHEY_PLAIN, 1, line_color, 2)

        #toggle display on 'a' press
        if cv2.waitKey(1) & 0xFF == ord('a'):
            display_select = not display_select
        if display_select:
            frame = draw_lines(frame, retval, decoded_list, points)
        
        cv2.imshow("QR Code Scanner", frame)

        # Breaks loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
