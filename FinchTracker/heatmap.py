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
PROJECT_ID = config['bigquery_project_id']
DATASET_ID = config['bigquery_dataset_id']
TABLE_ID = config['table_name']

client = bigquery.Client(project=PROJECT_ID)

def get_data():
    query = f"""
        SELECT data, timestamp, corner_points, distance
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
    plotted_points = []

    for i in range(frame):
        row = data.iloc[i]
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
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')

    return plotted_points




def main():
    result = get_data().to_dataframe()  # Convert RowIterator to DataFrame
    data = []

    for _, row in result.iterrows():
        corner_point_list = [
            [int(coord) for coord in pair.replace('(', '').replace(')', '').split(",")]
            for pair in row.corner_points.split(") (")
        ]
        data.append([row.data, row.timestamp, corner_point_list, row.distance])

    columns = ['data', 'timestamp', 'corner_points', 'distance']
    df = pd.DataFrame(data, columns=columns)

    # Convert timestamp to datetime with the specified format
    timestamp_format = "%Y-%m-%d %H:%M:%S:%f"
    df['timestamp'] = pd.to_datetime(df['timestamp'], format=timestamp_format)

    fig, ax = plt.subplots()
    ani = FuncAnimation(fig, update_heatmap, fargs=(df, ax), frames=len(df), repeat=False)
    plt.show()

if __name__ == "__main__":
    main()
