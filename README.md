# 4882-001-finch-tracking

## Sprint 1

- In Sprint one, the focus was on researching how to handle QR codes and working with our client to order the necessary Raspberry Pi hardware (the Pi itself, cameras, cables, etc.).
- We started writing code to test popular libraries for QR detection: OpenCV's `QRCodeDetector.DetectMulti()` and Pyzbar's `decode()`.
- The team began setting up a Google Cloud BigQuery table to store the raw outputs from the QR code detection.

### Goals For Sprint 2

- Load the code on the Raspberry Pi.
- Establish a remote connection to the RPi.
- Establish a connection between the RPi and the cameras.
- Scan and recognize a QR code with a camera. 📷🔍

## Sprint 2

### Additional Goals for Sprint 2

- Calculate distances between QR codes.
- Establish a connection to the BigQuery.
- Successfully upload scanned QR codes to BigQuery.

- In Sprint two, the focus was on scanning a QR code and logging it into BigQuery. We wanted to add the rows in the format:

```python
f"| {self.camera_id:10} | {timestamp:30} | {data:9} | {corner_points:30} | {distance:.2f} mm |"
```
where:
- `camera_id`: the ID of the camera that caught the scan.
- `timestamp`: the exact time down to milliseconds.
- `data`: the actual value read from the scanned QR code.
- `corner points`: the x and y coordinates of the corners of the detected QR code within the frame.
- `distance`: the calculated distance between the QR code and the camera.

### Sprint 2 Achievements 🏆

- Tested detection on both live video feed and individual images.
- Booted the operating system on the RPi.
- Created a virtual connection to the RPi.
- Tested RPi cameras.
- Implemented visualization that displays bounding boxes around QR codes for verification.
- Successfully detected multiple QR codes in one image.
- Brainstormed how the data can be summarized.

### Goals for Sprint 3

- Get the RPi itself to stream data to BigQuery.
- Work to consolidate code into a working deployable file.
- Explore remote location access to RPi.
- Integrate a distance algorithm to generate bird proximity summaries.

## Sprint 3

- In Sprint three, the focus is to get a product deployed on the RPi that could read QR codes at a rate of 60fps. The code was having difficulty reading that fast from a live video feed. The solution to this problem was to create a queue for each camera. The queue's responsibility is to do the actual processing of the individual frames. This allows the processing to be done in semi-real time without having to store all of the images. Another problem we were dealing with was library installation compatibility with the RPi. The solution to this problem was to package all the components into a Docker image that could be deployed onto the RPi. This solution will also assist us in making our project as reproducible and easily deployable for our client.

## Project Structure

```plaintext
main
4882-001-finch-tracking/
|-- Sprint1/               # Contains documentation from Sprint 1
|-- Sprint2/               # Contains documentation from Sprint 2
|-- Sprint3/               # Aruco code detection tests
|-- img_read_test          # Images for detection tests
|-- unused_assimilations   # Unused component files
|-- README.md              # Project overview and documentation
|-- requirements.txt       # List of project dependencies
|-- birdsv3.py             # Handles detection, processing, and uploading data
|-- calibration.jpg        # Image for camera calibration in birdsv3.py
|-- summaries.py           # Computes distances between QR codes filterable by time
```




