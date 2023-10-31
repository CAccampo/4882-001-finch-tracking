def initialize_bigquery(project_id, dataset_id, table_id_file):

    import os
    from google.cloud import bigquery, client
    from datetime import datetime
    import threading

    # check if a table file exists, load it or make one
    if os.path.exists(table_id_file):
        with open(table_id_file, 'r') as file:
            table_id = file.read().strip()
    else:
        table_id = f'test1_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        with open(table_id_file, 'w') as file:
            file.write(table_id)

    # create or load the bigquery table
    client = bigquery.Client(project=project_id)
    table = client.create_table(
        bigquery.Table(f"{project_id}.{dataset_id}.{table_id}", 
                       
        # this schema will likely change at some point, it is easily editable here
        schema=[
            bigquery.SchemaField("qr_data", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Position", "STRING", mode="NULLABLE")
        ]), 

        exists_ok=True)

    return client, table

def upload_data(client, table):

    import time
    import threading
    from datetime import datetime

    upload_interval = 10
    data_lock = threading.Lock()
    global batched_data

    while True:

        # we are upload every {upload_interval} seconds
        time.sleep(upload_interval)
        
        # the "data_lock" and "batched_data" serves to prevent the threading from imploding
        with data_lock:
            if not batched_data:
                continue
            
            data_to_insert = batched_data.copy()
            batched_data.clear()

        # prepare the data
        rows_to_insert = [
            {"qr_data": data, "timestamp": timestamp.isoformat(), "Position": position} 
            for data, timestamp, position in data_to_insert
        ]

        # upload the data
        errors = client.insert_rows_json(table, rows_to_insert)
        
        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
        else:
            print(f"Data uploaded to {table.table_id} at {datetime.utcnow().isoformat()}")

def draw_lines(frame, retval, decoded_list, points_list):
    import cv2
    line_color = (0, 255, 0)

    if retval:
        for decoded_qr in decoded_list:
            frame = cv2.putText(frame, str(decoded_qr), (10, (decoded_list.index(decoded_qr)+1)*20), cv2.FONT_HERSHEY_PLAIN, 1, line_color, 2)
        for points in points_list:
            frame = cv2.polylines(frame, [points.astype(int)], True, line_color, 4)

    return frame

# batched data is defined here instead of inside the main function so
# that it can exist as a global variable used by main() and upload_data()
batched_data = []

def main():

    import json
    import threading
    import cv2
    from datetime import datetime

    # we start with some initializations
    my_client, my_table = initialize_bigquery('finch-project-399922', 'finch_beta_table', 'table_id.txt')    
    detector = cv2.QRCodeDetector()
    display_select = False
    data_lock = threading.Lock()
    global batched_data

    # then we open a thread for constant bigquery uploads
    upload_thread = threading.Thread(target=upload_data, args= (my_client,my_table), daemon=True)
    upload_thread.start()

    # turn on the webcam. ChatGPT was used in the troubleshooting of getting this process to work. 
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Could not open webcam")
        return

    # this while loop constantly reads data frame the webcam
    # specifically looking to read and process qr codes
    while True:

        ret, frame = cap.read()
        if not ret: # ret is a boolean telling us if we successfully read a frame
            break

        # then we read the data 
        ret, decoded_list, points, straight_qr = detector.detectAndDecodeMulti(frame)
        if ret:
            for qr_data in decoded_list:
                if qr_data: # if the qr code is readable
                    print("QR Data: ", qr_data)
                    with data_lock:
                        batched_data.append((qr_data, datetime.utcnow(), None))

        # adding options to webcam display frame
        frame = cv2.putText(frame, "a - display", (540,450), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
        frame = cv2.putText(frame, "q - quit", (540,470), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)

        # toggle qr code target lines on "a", needs to be before display or no lines will be drawn
        if cv2.waitKey(1) & 0xFF == ord('a'):
            display_select = not display_select
        if display_select:
            frame = draw_lines(frame, ret, decoded_list, points)

        # webcam display frame
        cv2.imshow("QR Code Scanner", frame)

        # break on "q"
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

main()