import tkinter as tk
from tkinter import ttk
import customtkinter as ck
import json
from SetupBirdConfig import bird_win_loop, update_config, save_config, load_config

config_list = []
config_path = 'config.json'
ck.set_appearance_mode('dark')

window = ck.CTk()
window.geometry('520x600')
window.title('SetupConfig')
window.resizable(False,False)

def win_loop():
    ps = 10
    config = load_config()
    config_entry = []
    for i in range(len(config)):
        config_entry.append(tk.StringVar())

    #Left Side Finch Config
    ck.CTkLabel(window, text='Finch Tracker Configuration', font=('Times', 20)).grid(row=0, columnspan=2, padx=ps, pady=ps)
    
    for i, item in enumerate(config.items()):
        key, val = item
        ck.CTkLabel(window, text=key).grid(sticky='w',row=i+1, padx=(ps))
        curr_entry = ck.CTkEntry(window, textvariable=config_entry[i])
        curr_entry.grid(row=i+1, column=1, padx=(ps), pady=1)
        curr_entry.insert(0, val)
    ttk.Separator(window,orient='horizontal').grid(row=len(config)+1, columnspan = 2,sticky='ew', pady=ps)
    ck.CTkButton(window,text = 'Update', command = lambda: update_config(config, config_entry)).grid(row=len(config)+2, columnspan =2, pady=10)

    #Right Side ArUco Config
    ck.CTkLabel(window, text='ArUco Barcode', font=('Times', 20)).grid(row=0, column = 2, columnspan=2)
    ck.CTkLabel(window, text='Dictionary Type: DICT_4X4_250').grid(row=1, column = 2, columnspan=2)
    ck.CTkButton(window,text = 'Set Bird IDs', command = bird_win_loop).grid(row=2, column=2, columnspan =2, pady=10)

    window.mainloop()

if __name__ == "__main__":
   win_loop()