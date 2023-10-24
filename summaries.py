import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = 'finch-project-399922'
DATASET_ID = 'finch_beta_table'
TABLE_ID = 'new_coords_table'
SAFE_DISTANCE = 6  

client = bigquery.Client(project=PROJECT_ID)

def get_data_for_interval(start_time, end_time):
    query = f"""
        SELECT data, timestamp, corner_points, distance
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
        ORDER BY timestamp
    """
    return client.query(query).result()

def get_center_from_corner_points(corner_points):
    points = [tuple(map(float, point.strip('()').split(','))) for point in corner_points.split()]
    x_center = sum(point[0] for point in points) / len(points)
    y_center = sum(point[1] for point in points) / len(points)
    return x_center, y_center

def compute_distance(corner_points1, corner_points2):
    x1, y1 = get_center_from_corner_points(corner_points1)
    x2, y2 = get_center_from_corner_points(corner_points2)
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def generate_summary(data):
    summary = {}
    for row in data:
        id = row.data
        corner_points = row.corner_points
        timestamp = row.timestamp

        if id not in summary:
            summary[id] = {
                'positions': [],
                'close_contacts': []
            }
        summary[id]['positions'].append([corner_points, timestamp])

        for other_id, info in summary.items():
            if other_id != id:
                for other_position in info['positions']:
                    if other_position[1] == timestamp:
                        if compute_distance(corner_points, other_position[0]) < SAFE_DISTANCE:
                            summary[id]['close_contacts'].append([other_id, timestamp])
                            break
    
    return summary

def main(interval_minutes=60):
    current_time = datetime.utcnow()
    start_time = current_time - timedelta(minutes=interval_minutes)

    data = get_data_for_interval(start_time.isoformat(), current_time.isoformat())
    summary = generate_summary(data)

    for id, info in summary.items():
        print(f"Summary for ID {id} from {start_time} to {current_time}:")
        print(f"Positions: {info['positions']}")
        if info['close_contacts']:
            print(f"Close contacts: {', '.join(info['close_contacts'])}")
        print('-'*40)

if __name__ == "__main__":
    main()
