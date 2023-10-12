import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = 'finch-project-399922'
DATASET_ID = 'finch_beta_table'
TABLE_ID_FILE = 'table_id.txt'
SAFE_DISTANCE = 6  


client = bigquery.Client(project=PROJECT_ID)

def get_data_for_interval(start_time, end_time):
    table_id = ''
    with open(TABLE_ID_FILE, 'r') as file:
        table_id = file.read().strip()

    query = f"""
        SELECT qr_data, timestamp, Position
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}`
        WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
        ORDER BY timestamp
    """
    return client.query(query).result()

def compute_distance(pos1, pos2):
    """
    Here, we compute euclidean distance between two positions.
    """
    x1, y1 = map(float, pos1.split(','))
    x2, y2 = map(float, pos2.split(','))
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def generate_summary(data):
    """
    We then generate a summary of movements and close contacts for the data.
    """
    summary = {}
    for row in data:
        id = row.qr_data
        position = row.Position
        timestamp = row.timestamp

        if id not in summary:
            summary[id] = {
                'positions': [],
                'close_contacts': []
            }
        summary[id]['positions'].append(position)

        for other_id, info in summary.items():
            if other_id != id:
                if info['positions'] and compute_distance(position, info['positions'][-1]) < SAFE_DISTANCE:
                    summary[id]['close_contacts'].append(other_id)
    
    return summary

def main(interval_minutes=60):
    """
    Main function to fetch data and generate movement summaries.
    """
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
