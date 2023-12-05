import os
from google.cloud import bigquery
import pandas as pd
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'finch-project-399922-0196b8dd1667.json'

PROJECT_ID = 'finch-project-399922'
DATASET_ID = 'finch_beta_table'
TABLE_ID = 'new_coords_table'

client = bigquery.Client(project=PROJECT_ID)

def get_data():
    query = f"""
        SELECT data, corner_points, distance
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

def update_heatmap(frame, data, ax):
    ax.clear()

    for i in range(frame):
        row = data.iloc[i]
        corner_points = np.array(row['corner_points'])
        center_point = calculate_center_point(corner_points)
        ax.plot(center_point[0], center_point[1], 'ro')  # 'ro' means red color, circular marker

    ax.set_title(f'Accumulated Frames up to {frame}')
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')

if __name__ == "__main__":
    result = get_data()
    data = []

    for row in result:
        corner_point_list = [
            [int(coord) for coord in pair.replace('(', '').replace(')', '').split(",")]
            for pair in row.corner_points.split(") (")
        ]
        data.append([row.data, corner_point_list, row.distance])

    columns = ['data', 'corner_points', 'distance']
    df = pd.DataFrame(data, columns=columns)

    fig, ax = plt.subplots()
    ani = FuncAnimation(fig, update_heatmap, fargs=(df, ax), frames=len(df), repeat=False)
    plt.show()
