import numpy as np
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import json
import os
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

with open('Sprint4/config.json', 'r') as config_file:
    config = json.load(config_file)
    
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config['CREDENTIALS']
PROJECT_ID = config['bigquery_project_id']
DATASET_ID = config['bigquery_dataset_id']
TABLE_ID = config['table_name']
SAFE_DISTANCE = config['SAFE_DISTANCE']
INACTIVITY_THRESHOLD = config['INACTIVITY_THRESHOLD']
VERY_ACTIVE_DISTANCE = config['VERY_ACTIVE_DISTANCE']

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
    points = [
        [int(coord) for coord in pair.replace('(', '').replace(')', '').split(",")]
        for pair in corner_points.split(") (")
    ]
    x_center = sum(point[0] for point in points) / len(points)
    y_center = sum(point[1] for point in points) / len(points)
    return x_center, y_center

def compute_distance(corner_points1, corner_points2):
    x1, y1 = get_center_from_corner_points(corner_points1)
    x2, y2 = get_center_from_corner_points(corner_points2)
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def parse_custom_timestamp(timestamp_str):
    if ':' in timestamp_str[-8:]:
        timestamp_str = timestamp_str.rsplit(':', 1)[0] + '.' + timestamp_str.rsplit(':', 1)[1]
    return parse(timestamp_str)

def calculate_duration(start, end):
    start_dt = parse_custom_timestamp(start)
    end_dt = parse_custom_timestamp(end)
    return (end_dt - start_dt).total_seconds() / 60

def generate_summary(data):
    summary = {}
    for row in data:
        id = row.data
        corner_points = row.corner_points
        timestamp = row.timestamp
        if id not in summary:
            summary[id] = {
                'positions': [],
                'close_contacts': [],
                'inactivity_periods': [],
                'total_distance': 0,
                'last_position': None
            }
        summary[id]['positions'].append([corner_points, timestamp])
        if summary[id]['last_position']:
            last_position, last_time = summary[id]['last_position']
            # Ensure both times are strings
            last_time_str = last_time.isoformat() if not isinstance(last_time, str) else last_time
            timestamp_str = timestamp if not isinstance(timestamp, str) else timestamp

            distance = compute_distance(corner_points, last_position)
            summary[id]['total_distance'] += distance

            if distance < INACTIVITY_THRESHOLD:
                inactivity_duration = calculate_duration(last_time_str, timestamp_str)
                summary[id]['inactivity_periods'].append(inactivity_duration)

        summary[id]['last_position'] = [corner_points, timestamp]
        for other_id, info in summary.items():
            if other_id != id:
                for other_position in info['positions']:
                    if other_position[1] == timestamp:
                        distance = compute_distance(corner_points, other_position[0])
                        if distance < SAFE_DISTANCE:
                            duration = calculate_duration(last_time, timestamp)
                            summary[id]['close_contacts'].append([other_id, timestamp, duration])
                            break
    
    return summary
def export_to_spreadsheet(summary, query_start_time, query_end_time):
    start_str = query_start_time.strftime("%Y%m%d_%H%M%S")
    end_str = query_end_time.strftime("%Y%m%d_%H%M%S")
    filename = f'bird_data_summary_{start_str}_to_{end_str}.xlsx'

    with pd.ExcelWriter(filename) as writer:
        for id, info in summary.items():
            timestamps = []
            distances = []
            inactivity_periods = []
            close_contacts = []

            for pos in info['positions']:
                timestamps.append(pos[1])
                if len(pos[0]) == 2:
                    distances.append(compute_distance(pos[0][0], pos[0][1]))
                else:
                    distances.append(0)
                inactivity_periods.append(None)
                close_contacts.append(None)
            for i, period in enumerate(info['inactivity_periods']):
                inactivity_periods[i] = period

            for i, contact in enumerate(info['close_contacts']):
                close_contacts[i] = f"{contact[0]} at {contact[1]} for {contact[2]} minutes"

            df = pd.DataFrame({
                'Timestamp': timestamps,
                'Distance Travelled': distances,
                'Inactivity Periods': inactivity_periods,
                'Close Contacts': close_contacts
            })
            df.to_excel(writer, sheet_name=f"Bird_{id}")

def main():
    current_time = datetime.utcnow()
    start_time = current_time - relativedelta(months=1)
    query_start_time = start_time.isoformat()
    query_end_time = current_time.isoformat()

    data = get_data_for_interval(query_start_time, query_end_time)
    summary = generate_summary(data)
    export_to_spreadsheet(summary, start_time, current_time)

    for id, info in summary.items():
        print(f"Summary for ID {id} from {start_time} to {current_time}:")
        print(f"Positions: {info['positions']}")
        print(f"Total Distance Travelled: {info['total_distance']}")
        if info['total_distance'] > VERY_ACTIVE_DISTANCE:
            print(f"Bird ID {id} is very active.")
        if info['close_contacts']:
            print(f"Close contacts: {', '.join([str(contact) for contact in info['close_contacts']])}")
        if info['inactivity_periods']:
            print(f"Inactivity Periods: {info['inactivity_periods']}")
        print('-'*40)

if __name__ == "__main__":
    main()
