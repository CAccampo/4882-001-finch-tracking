import json

def load_config(file_path):
    
    with open(file_path, 'r') as config_file:
        return json.load(config_file)

def save_config(file_path, config):
    with open(file_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
        print("Configuration saved successfully.")

def display_config(config):
    """ Display the current configuration settings. """
    print("\nCurrent Configuration:")
    for key, value in config.items():
        print(f"{key}: {value}")

def edit_config(config):
    print("\nEnter new values for the configuration variables (leave blank to keep current value):")
    for key in config.keys():
        new_value = input(f"{key} [{config[key]}]: ")
        if new_value:
            # Convert to appropriate type (int, list, etc.)
            if isinstance(config[key], int):
                config[key] = int(new_value)
            elif isinstance(config[key], list):
                config[key] = json.loads(new_value)
            else:
                config[key] = new_value
    return config

def main():
    config_path = 'config.json'
    config = load_config(config_path)

    display_config(config)
    config = edit_config(config)
    save_config(config_path, config)

if __name__ == "__main__":
    main()
