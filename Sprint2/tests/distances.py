
import numpy as np
import cv2
import matplotlib.pyplot as plt

def perspective_projection(u, v, focal_length, principle_point):
    x = (u - principle_point[0]) / focal_length
    y = (v - principle_point[1]) / focal_length
    return x, y

def inverse_perspective_projection(x, y, focal_length, principle_point, depth):
    X = x * depth
    Y = y * depth
    Z = depth
    return X, Y, Z

def adjust_depth(estimated_depth, object_size_pixels, known_size_mm):
    object_size_mm = (object_size_pixels / image_width) * sensor_width_mm
    adjusted = estimated_depth * (known_size_mm / object_size_mm)
    return adjusted

def calculate_center_point(corners_3d):
    center = np.mean(corners_3d, axis=0)
    return center

def calculate_distance(camera_position, object_position):
    distance = (np.linalg.norm(np.array(camera_position) - np.array(object_position))) / 10
    return distance

def visualize_shapes(json_data):
    plt.figure()
    ax = plt.gca()

    for shape_name, corners in json_data.items():
        for x, y in corners:
            plt.plot(x, y, 'ro')
        corners.append(corners[0])
        x_values, y_values = zip(*corners)
        plt.plot(x_values, y_values, 'b-')

    plt.gca().invert_yaxis()
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Shapes Plotted with Corners')
    plt.grid(True)
    plt.show()



camera_params = {
    'focal_length': 1000,
    'principle_point': (320, 240),
    'baseline': 0.1,  #baseline for stereo vision (adjust as needed)
    'camera_position': (0, 0, 0)
}

#example of bouding box data output
json_data = {
    "large_quadrilateral": [
        (100, 100),
        (180, 150),
        (200, 220),
        (120, 170)
    ],
    "medium_quadrilateral": [
        (250, 100),
        (320, 150),
        (350, 220),
        (280, 170)
    ],
    "small_quadrilateral": [
        (400, 100),
        (460, 150),
        (480, 220),
        (420, 170)
    ],
    "tiny_quadrilateral": [
        (550, 100),
        (570, 120),
        (580, 140),
        (560, 160)
    ],
    "smallest_quadrilateral": [
        (700, 100),
        (710, 105),
        (715, 110),
        (705, 115)
    ]
}

image_path = 'img_1.png'

image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
stereo = cv2.StereoBM_create(numDisparities=64, blockSize=15)
disparities = stereo.compute(image, image)

#convert disparity to depth
depth_scaling_factor = 1.0  #adjust based on your depth map units
depth_map = camera_params['baseline'] * camera_params['focal_length'] / (disparities + 1e-6)
depth_map_scaled = depth_map * depth_scaling_factor

known_square_size_mm = 10.0  #replace with the actual size of the qr codes in millimeters

distances = {}

image_width = image.shape[1]
sensor_width_mm = 36.0  #replace with camera's sensor width in millimeters

for square_name, corners_2d in json_data.items():
    corners_normalized = [perspective_projection(u, v, camera_params['focal_length'], camera_params['principle_point']) for u, v in corners_2d]
    
    #depth for the square: average depth values from the depth map
    depths = [depth_map_scaled[int(v), int(u)] for u, v in corners_normalized]
    estimated_depth = np.mean(depths)
    adjusted_depth = adjust_depth(estimated_depth, max(corners_2d)[0] - min(corners_2d)[0], known_square_size_mm)
    
    corners_3d = [inverse_perspective_projection(x, y, camera_params['focal_length'], camera_params['principle_point'], adjusted_depth) for x, y in corners_normalized]
    center_point = calculate_center_point(corners_3d)
    
    distance = calculate_distance(camera_params['camera_position'], center_point)
    distances[square_name] = distance

print(distances)

visualize_shapes(json_data)