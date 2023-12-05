import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = 'finch-project-399922'
DATASET_ID = 'finch_beta_table'
TABLE_ID = 'newest_coords_table'
SAFE_DISTANCE = 6  
INACTIVITY_THRESHOLD = 0.5  # Distance threshold to consider a bird inactive
VERY_ACTIVE_DISTANCE = 10  # Threshold for a bird to be considered very active

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

def calculate_duration(start, end):
    return (end - start).total_seconds() / 60  

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

        # Check for inactivity
        if summary[id]['last_position']:
            last_position, last_time = summary[id]['last_position']
            distance = compute_distance(corner_points, last_position)
            summary[id]['total_distance'] += distance

            if distance < INACTIVITY_THRESHOLD:
                inactivity_duration = calculate_duration(last_time, timestamp)
                summary[id]['inactivity_periods'].append(inactivity_duration)

        summary[id]['last_position'] = [corner_points, timestamp]

        # Check for close contacts
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
    # Format timestamps for filename using query start and end times
    start_str = query_start_time.strftime("%Y%m%d_%H%M%S")
    end_str = query_end_time.strftime("%Y%m%d_%H%M%S")
    filename = f'bird_data_summary_{start_str}_to_{end_str}.xlsx'

    with pd.ExcelWriter(filename) as writer:
        for id, info in summary.items():
            df = pd.DataFrame({
                'Timestamp': [pos[1] for pos in info['positions']],
                'Distance Travelled': [compute_distance(*pos[0]) for pos in info['positions']],
                'Inactivity Periods': info['inactivity_periods'],
                'Close Contacts': [f"{contact[0]} at {contact[1]} for {contact[2]} minutes" for contact in info['close_contacts']]
            })
            df.to_excel(writer, sheet_name=f"Bird_{id}")


def main(interval_minutes=60):
    current_time = datetime.utcnow()
    start_time = current_time - timedelta(minutes=interval_minutes)

    # Use the actual start and end times from the query
    query_start_time = start_time.isoformat()
    query_end_time = current_time.isoformat()

    data = get_data_for_interval(query_start_time, query_end_time)
    summary = generate_summary(data)
    export_to_spreadsheet(summary, query_start_time, query_end_time)

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