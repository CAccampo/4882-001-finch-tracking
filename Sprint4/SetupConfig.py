import tkinter as tk
from tkinter import ttk
import json

config_list = []
config_path = 'config.json'

window = tk.Tk()
window.geometry('490x400')
window.title('SetupFinchConfig')
calib_path, cb_size, dict_type, proj_id, data_id, table_name = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
#Intvar appending 0s for some reason
up_int, num_cams, code_size = tk.StringVar(),tk.StringVar(),tk.StringVar()

def update_config():
    config = load_config()

    #update keys
    config['calibration_image_paths'] = calib_path.get()
    config['upload_interval'] = int(up_int.get())
    config['num_cameras'] = int(num_cams.get())
    config['bigquery_project_id'] = proj_id.get()
    config['bigquery_dataset_id'] = data_id.get()
    config['table_name'] = table_name.get()
    config['aruco_dictionary'] = dict_type.get()
    config['obj_real_size'] = int(code_size.get())
    config['chessboard_size'] = [eval(i) for i in cb_size.get().split(' ')]
    
    save_config(config)

def win_loop():
    ps = 10

    tk.Label(window, text='Finch Tracker Configuration', font=('Times', 20)).grid(row=0, columnspan=4)

    ##CHECK/ADD THE UNITS ON SOME OF THESE >:( )
    #Entries with labels
    tk.Label(text='Calibration:').grid(sticky = 'w', row=1,pady=(ps,0))
    tk.Label(window, text='Image Path').grid(row=2)
    calib_path_entry = tk.Entry(window, textvariable=calib_path)
    tk.Label(window, text='Chessboard Size').grid(row=2, column=2)
    cb_size_entry = tk.Entry(window, textvariable=cb_size)
    
    tk.Label(text='Camera Capture:').grid(sticky = 'w', row=3, column=0,pady=(ps,0))
    tk.Label(window, text='Upload Interval').grid(row=4)
    upload_int_entry = tk.Entry(window, textvariable=up_int)
    tk.Label(window, text='Number of Cameras').grid(row=4, column=2)
    num_cams_entry = tk.Entry(window, textvariable=num_cams)
    
    tk.Label(text='Aruco Barcode:').grid(sticky = 'w', row=5, column=0,pady=(ps,0))
    tk.Label(window, text='Barcode Size').grid(row=6)
    code_size_entry = tk.Entry(window, textvariable=code_size)
    tk.Label(window, text='Dictionary Type').grid(row=6, column=2)
    dict_type_entry = tk.Entry(window, textvariable=dict_type)
    
    tk.Label(text='Bigquery:').grid(sticky = 'w', row=7, column=0,pady=(ps,0))
    tk.Label(window, text='Project ID').grid(row=8, column=0)
    proj_id_entry = tk.Entry(window, textvariable=proj_id)
    tk.Label(window, text='Dataset ID').grid(row=8, column=2)
    data_id_entry = tk.Entry(window, textvariable=data_id)
    tk.Label(window, text='Table Name').grid(row=9)
    table_entry = tk.Entry(window, textvariable=table_name)

    #placing entry widgets in grid
    calib_path_entry.grid(row=2,column=1,padx=(ps*2,0))
    cb_size_entry.grid(row=2,column=3)
    upload_int_entry.grid(row=4,column=1)
    num_cams_entry.grid(row=4,column=3)
    code_size_entry.grid(row=6,column=1)
    dict_type_entry.grid(row=6, column = 3)
    proj_id_entry.grid(row=8, column = 1)
    data_id_entry.grid(row=8, column = 3)
    table_entry.grid(row=9, column = 1)

    sep = ttk.Separator(window,orient='horizontal').grid(row=10, columnspan = 4,sticky='ew', pady=ps)
    tk.Button(window,text = 'Update', command = update_config).grid(row=11,column=2, columnspan =2, pady=10)

    #default values for entries
    config = load_config()

    calib_path_entry.insert(0, config['calibration_image_paths'])
    cb_size_entry.insert(0, config['chessboard_size'])
    upload_int_entry.insert(0, config['upload_interval'] )
    num_cams_entry.insert(0, config['num_cameras'] )
    code_size_entry.insert(0, config['obj_real_size'])
    dict_type_entry.insert(0, config['aruco_dictionary'])
    proj_id_entry.insert(0, config['bigquery_project_id'] )
    data_id_entry.insert(0, config['bigquery_dataset_id'] )
    table_entry.insert(0, config['table_name'])

    window.mainloop()

def load_config():
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def save_config(config):
    with open(config_path, 'w') as config_file:
        json.dump(config, config_file, indent=4)
        print("Configuration saved successfully.")

if __name__ == "__main__":
   win_loop()