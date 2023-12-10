import tkinter as tk
from tkinter import ttk
import customtkinter as ck
from customtkinter import CTkToplevel
import json

config_list = []
config_path = 'config.json'
bird_config_path = 'bird_config.json'
ck.set_appearance_mode('dark')
ps = 10
id_labels = []


def load_config(config_p):
    with open(config_p, 'r') as config_file:
        return json.load(config_file)
def save_config(config, config_p):
    with open(config_p, 'w') as config_file:
        json.dump(config, config_file, indent=4)

def save_and_display(config, config_p, window):
    save_config(config, config_p)
    display_ids(window)

def display_ids(window):
    loc_bird_config = load_config(bird_config_path)
    for id_label in id_labels:
        try:
            id_label.grid_remove()
        except tk.TclError:
            pass
    for i, item in enumerate(loc_bird_config.items()):
        key, val = item
        id_labels.append(ck.CTkLabel(window, text=f'{key}\t\t{val}'))
        id_labels[-1].grid(sticky='w',row=i+3, column=2, padx=(ps,0))
        if i > 5:
            id_labels.append(ck.CTkLabel(window, text=f'...\t\t...'))
            id_labels[-1].grid(sticky='w',row=i+4, column=2, padx=(ps,0))
            break


def add_birds():
    bird_config = load_config(bird_config_path)
    config = load_config(config_path)
    num_config_birds = config['num_birds']

    i = len(bird_config)
    while num_config_birds > len(bird_config):
        i = i+1
        bird_config[i] = i
    while num_config_birds < len(bird_config):
        bird_config.popitem()
    save_config(bird_config, bird_config_path)


def update_config(config, config_entry, config_p):
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
    if config_p == bird_config_path:
        add_birds()
    save_config(config, config_p)

def bird_win_loop(window):
    bird_config = load_config(bird_config_path)
    birdwin = CTkToplevel(window)
    birdwin.attributes('-topmost',True)
    win_size = '260x'+str(len(bird_config)*30+150)
    birdwin.geometry(win_size)
    birdwin.title('SetupBirdConfig')
    
    config = load_config(bird_config_path)

    config_entry = []
    for i in range(len(config)):
        config_entry.append(tk.StringVar())

    #Left Side Finch Config
    ck.CTkLabel(birdwin, text='Configure Bird IDs', font=('Times', 20)).grid(row=0, columnspan=2, padx=ps, pady=ps)
    ck.CTkLabel(birdwin, text='AruCo Code').grid(row=1, column=0, padx=ps)
    ck.CTkLabel(birdwin, text='Bird ID').grid(row=1, column=1)

    for i, item in enumerate(config.items()):
        key, val = item
        ck.CTkLabel(birdwin, text=key).grid(sticky='w',row=i+2, padx=(ps))
        curr_entry = ck.CTkEntry(birdwin, textvariable=config_entry[i])
        curr_entry.grid(row=i+2, column=1, padx=(ps), pady=1)
        curr_entry.insert(0, val)
    ttk.Separator(birdwin,orient='horizontal').grid(row=len(config)+2, columnspan = 2,sticky='ew', pady=ps)
    ck.CTkButton(birdwin,text = 'Update', command = lambda: [update_config(config, config_entry, bird_config_path), save_and_display(config, bird_config_path, window)]).grid(row=len(config)+3, columnspan =2, pady=10)

    birdwin.mainloop()
