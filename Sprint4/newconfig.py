import json

def load_config(file_path):
    with open(file_path, 'r') as config_file:
        return json.load(config_file)

def save_config(file_path, config):
    with open(file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
        print("Configuration saved successfully.")

def display_config(config):
    print("\nCurrent Configuration:")
    for key, value in config.items():
        print(f"{key}: {value}")

def is_valid_input(value, data_type):
    try:
        if data_type == list:
            json.loads(value)
        elif data_type == int:
            int(value)
        return True
    except ValueError:
        return False

def edit_config(config):
    print("\nEnter new values for the configuration variables (leave blank to keep current value):")
    for key in config.keys():
        while True:
            new_value = input(f"{key} [{config[key]}]: ")
            if not new_value:
                break
            if is_valid_input(new_value, type(config[key])):
                if isinstance(config[key], int):
                    config[key] = int(new_value)
                elif isinstance(config[key], list):
                    config[key] = json.loads(new_value)
                else:
                    config[key] = new_value
                break
            else:
                print("Invalid input. Please enter a valid value.")
    return config

def main():
    config_path = 'config.json'
    config = load_config(config_path)
    display_config(config)
    config = edit_config(config)
    save_config(config_path, config)

if __name__ == "__main__":
    main()
