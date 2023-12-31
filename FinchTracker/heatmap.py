import os
from google.cloud import bigquery
import pandas as pd
from pandas.api.types import CategoricalDtype
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
from SetupBirdConfig import load_config

config = load_config('config.json')
bird_config = load_config('bird_config.json')
PROJECT_ID = config['bigquery_project_id']
DATASET_ID = config['bigquery_dataset_id']
TABLE_ID = config['table_name']

client = bigquery.Client(project=PROJECT_ID)

def get_data():
    query = f"""
        SELECT data, timestamp, corner_points, distance, camera_id
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        ORDER BY timestamp
    """
    return client.query(query).result()

def calculate_center_point(corner_points):
    x_values = [point[0] for point in corner_points]
    y_values = [point[1] for point in corner_points]

    center_point = [
        sum(x_values) / len(x_values),
        sum(y_values) / len(y_values)
    ]

    return center_point

def update_heatmap(frame, data, ax, start, stop):
    frame = start+frame
    if frame < len(data) and frame <= stop:
        plotted_points = []

        row = data.iloc[frame]
        corner_points = np.array(row['corner_points'])
        center_point = calculate_center_point(corner_points)

        # Calculate alpha based on the time difference with increased scaling
        first_timestamp = data['timestamp'].min()
        time_difference = row['timestamp'] - first_timestamp
        alpha_scaling_factor = 8.0  # Adjust the scaling factor for a more pronounced fading effect
        alpha = 1.0 - (alpha_scaling_factor * time_difference / pd.Timedelta.max)

        # Plot the point with fading effect
        plotted_point = ax.plot(center_point[0], center_point[1], 'ro', alpha=alpha)[0]
        plotted_points.append(plotted_point)

        ax.set_title(f'Accumulated Frames up to {frame}')

        return plotted_points
def heatmap_animation(start, stop):
    data = format_data()
    columns = ['data', 'timestamp', 'corner_points', 'distance', 'camera_id']
    df = pd.DataFrame(data, columns=columns)

    # Convert timestamp to datetime with the specified format
    timestamp_format = "%Y-%m-%d %H:%M:%S:%f"
    df['timestamp'] = pd.to_datetime(df['timestamp'], format=timestamp_format)

    if stop == 0:
        stop = len(df)

    fig, ax = plt.subplots()
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ani = FuncAnimation(fig, update_heatmap, fargs=(df, ax, start, stop), frames=len(df), repeat=False)
    plt.show()

def init_heatmap(cam_num, dot_colors):
    #create blank white image from frame
    caps = [i for i in range(config['num_cameras'])]
    caps[cam_num] = cv2.VideoCapture(cam_num)
    _, frame = caps[cam_num].read()
    heatmap_img = np.ones(frame.shape, dtype = np.uint8)

    for i, (key, value) in enumerate(dot_colors.items()):
        heatmap_img = cv2.putText(heatmap_img, str(key), org=(50*i, 50), fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=1, color=value)

    return 255*heatmap_img
    
def draw_heatmap(center_point, data, heatmap_img, camera, dot_colors, bird_id):
    dot_color=tuple((0,0,0))
    if bird_id in dot_colors:
        dot_color=dot_colors[bird_id]
    return cv2.circle(heatmap_img, tuple(center_point.round().astype(int)), radius=0, color=dot_color, thickness=-5)


def save_overall_heatmap():
    data = format_data()
    #deciding colors
    dot_colors = {}
    for _, value in bird_config.items():
        dot_colors[value] = np.random.randint(0,255,size=3,)
        dot_colors[value] = tuple(int(dot_colors[value][i]) for i in range(len(dot_colors[value])))

    for i in range(config['num_cameras']):
        heatmap_img = init_heatmap(i, dot_colors)
        for row in data:
            if int(row[4])==i:
                heatmap_img = draw_heatmap(np.int32(row[2]).mean(0), data, heatmap_img, i, dot_colors, int(row[0]))
        cv2.imwrite(f'heatmap{i}.png', heatmap_img)
        print(f'Finished drawing heatmap{i}.png')

def format_data():
    result = get_data().to_dataframe()  # Convert RowIterator to DataFrame
    data = []

    for _, row in result.iterrows():
        corner_point_list = [
            [int(coord) for coord in pair.replace('(', '').replace(')', '').split(",")]
            for pair in row.corner_points.split(") (")
        ]
        data.append([row.data, row.timestamp, corner_point_list, row.distance, row.camera_id])
    return data
