import tkinter as tk
from tkinter import ttk
import customtkinter as ck
import json

config_list = []
config_path = 'config.json'
ck.set_appearance_mode('dark')

window = ck.CTk()
window.geometry('540x600')
window.title('SetupFinchConfig')
window.resizable(False,False)

def update_config(config, config_entry):
    for i, key in enumerate(config.keys()):
        curr_config_entry = config_entry[i].get()
        if curr_config_entry.isdigit():
            curr_config_entry = int(curr_config_entry)
        else:
            try:
                curr_config_entry = float(curr_config_entry)
            except ValueError:
                pass
        config[key]=curr_config_entry
    
    save_config(config)

def win_loop():
    ps = 10
    config = load_config()
    config_entry = []
    for i in range(len(config)):
        config_entry.append(tk.StringVar())

    ck.CTkLabel(window, text='Finch Tracker Configuration', font=('Times', 20)).grid(row=0, columnspan=4, padx=ps, pady=ps)
    
    for i, item in enumerate(config.items()):
        key, val = item
        ck.CTkLabel(window, text=key).grid(sticky='w',row=i+1, padx=(ps))
        curr_entry = ck.CTkEntry(window, textvariable=config_entry[i])
        curr_entry.grid(row=i+1, column=1, padx=(ps), pady=1)
        curr_entry.insert(0, val)
    ttk.Separator(window,orient='horizontal').grid(row=len(config)+1, columnspan = 4,sticky='ew', pady=ps)
    ck.CTkButton(window,text = 'Update', command = lambda: update_config(config, config_entry)).grid(row=len(config)+2, columnspan =2, pady=10)

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