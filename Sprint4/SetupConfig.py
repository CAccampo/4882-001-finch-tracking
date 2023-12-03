import tkinter as tk
from tkinter.filedialog import asksaveasfile
import json

def create_window():
    window = tk.Tk()
    window.geometry('640x480')
    window.title('SetupFinchConfig')
    return window

def add_widgets(window):
    head = tk.Label(window, text='Finch Configuration', font=('Times', 20))
    #widgets
    ##CHECK/ADD THE UNITS ON SOME OF THESE >:( )
    calib_path_label = tk.Label(window, text='Calibration:\nImage Path')
    calib_path_entry = tk.Entry(window)
    cb_size_label = tk.Label(window, text='Calibration:\nChessboard Size')
    cb_size_entry = tk.Entry(window)
    upload_int_label = tk.Label(window, text='Upload Interval')
    upload_int_entry = tk.Entry(window)
    num_cams_label = tk.Label(window, text='Number of Cameras')
    num_cams_entry = tk.Entry(window)
    code_size_label = tk.Label(window, text='Barcode Size')
    code_size_entry = tk.Entry(window)


    sub_btn=tk.Button(window,text = 'Submit', command = '')

    #default values
    calib_path_entry.insert(0, 'calib_img.png')
    cb_size_entry.insert(0, [7, 6])
    upload_int_entry.insert(0, 10)
    num_cams_entry.insert(0, 1)
    code_size_entry.insert(0, 20)

    #placing widgets in window
    head.grid(row=0, column=1, columnspan=3)
    calib_path_label.grid(row=1,column=0)
    calib_path_entry.grid(row=1,column=1)
    cb_size_label.grid(row=1,column=2)
    cb_size_entry.grid(row=1,column=3)
    upload_int_label.grid(row=2,column=0)
    upload_int_entry.grid(row=2,column=1)
    num_cams_label.grid(row=3,column=0)
    num_cams_entry.grid(row=3,column=1)
    code_size_label.grid(row=4,column=0)
    code_size_entry.grid(row=4,column=1)

    sub_btn.grid(row=10,column=1)

    window.mainloop()

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
    window = create_window()
    add_widgets(window)
    config_path = 'config.json'
    config = load_config(config_path)

    display_config(config)
    config = edit_config(config)
    save_config(config_path, config)

if __name__ == "__main__":
    main()