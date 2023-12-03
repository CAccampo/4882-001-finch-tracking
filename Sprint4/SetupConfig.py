import tkinter as tk
from tkinter.filedialog import asksaveasfile
import json

config_list = []
config_path = 'config.json'

window = tk.Tk()
window.geometry('490x480')
window.title('SetupFinchConfig')
calib_path, cb_size, dict_type = tk.StringVar(), tk.StringVar(), tk.StringVar()
#Intvar appending 0s for some reason
up_int, num_cams, code_size = tk.StringVar(),tk.StringVar(),tk.StringVar()

def update_config():
    config = load_config()

    #update keys
    config['calibration_image_paths'] = calib_path.get()
    config['upload_interval'] = int(up_int.get())
    config['num_cameras'] = int(num_cams.get())
    # config['bigquery_project_id']
    # config['bigquery_dataset_id']
    # config['table_name']
    config['aruco_dictionary'] = dict_type.get()
    config['obj_real_size'] = int(code_size.get())
    config['chessboard_size'] = [eval(i) for i in cb_size.get().split(' ')]
    
    save_config(config)

def add_widgets():
    head = tk.Label(window, text='Finch Configuration', font=('Times', 25))

    #widgets
    ##CHECK/ADD THE UNITS ON SOME OF THESE >:( )
    calib_path_label = tk.Label(window, text='Calibration:\nImage Path')
    calib_path_entry = tk.Entry(window, textvariable=calib_path)
    cb_size_label = tk.Label(window, text='\nChessboard Size')
    cb_size_entry = tk.Entry(window, textvariable=cb_size)
    upload_int_label = tk.Label(window, text='Upload Interval')
    upload_int_entry = tk.Entry(window, textvariable=up_int)
    num_cams_label = tk.Label(window, text='Number of Cameras')
    num_cams_entry = tk.Entry(window, textvariable=num_cams)
    code_size_label = tk.Label(window, text='Barcode Size')
    code_size_entry = tk.Entry(window, textvariable=code_size)
    dict_type_label = tk.Label(window, text='ArUco Dictionary Type')
    dict_type_entry = tk.Entry(window, textvariable=dict_type)


    sub_btn=tk.Button(window,text = 'Submit', command = update_config)

    config = load_config()

    #default values
    calib_path_entry.insert(0, config['calibration_image_paths'])
    cb_size_entry.insert(0, config['chessboard_size'])
    upload_int_entry.insert(0, config['upload_interval'] )
    num_cams_entry.insert(0, config['num_cameras'] )
    code_size_entry.insert(0, config['obj_real_size'])
    dict_type_entry.insert(0, config['aruco_dictionary'])

    #placing widgets in window
    head.grid(row=0, column=0, columnspan=4)
    
    calib_path_label.grid(row=1,column=0)
    calib_path_entry.grid(row=1,column=1)
    cb_size_label.grid(row=1,column=2)
    cb_size_entry.grid(row=1,column=3,pady=20)
    upload_int_label.grid(row=2,column=0)
    upload_int_entry.grid(row=2,column=1)
    num_cams_label.grid(row=3,column=0)
    num_cams_entry.grid(row=3,column=1)
    code_size_label.grid(row=2,column=2)
    code_size_entry.grid(row=2,column=3)
    dict_type_label.grid(row=3, column = 2)
    dict_type_entry.grid(row=3, column = 3)

    sub_btn.grid(row=10,column=0, pady=20)

    window.mainloop()

def load_config():
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def save_config(config):
    with open(config_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
        print("Configuration saved successfully.")

def display_config(config):
    """ Display the current configuration settings. """
    print("\nCurrent Configuration:")
    for key, value in config.items():
        print(f"{key}: {value}")


def main():
    add_widgets()

if __name__ == "__main__":
    main()