import tkinter as tk
from tkinter import ttk
import customtkinter as ck
import cv2
from heatmap import heatmap_animation, save_overall_heatmap
from SetupBirdConfig import load_config
import numpy as np

ps = 10
def open_heatmap():
    config = load_config('config.json')
    for i in range(config['num_cameras']):
        try:
            heatmap_img = cv2.imread(f'heatmap{i}.png')
            cv2.imshow(f'Heatmap {i}', heatmap_img)
        except:
            print(f'heatmap{i}.png not found\nCheck if it has been drawn and exists in current directory.')

def win_loop():
    print('Initializing window')
    window = ck.CTk()
    window.geometry('520x600')
    window.title('SetupConfig')
    window.resizable(False,False)

    start, stop = tk.IntVar(), tk.IntVar()

    ck.CTkLabel(window, text='BigQ Table Analysis', font=('Times', 20)).grid(row=0, columnspan=2, padx=ps, pady=ps)
    
    ck.CTkLabel(window, text='Heatmap', font=('Times', 20)).grid(sticky='w',row=1, columnspan=2, padx=ps, pady=ps)
    ck.CTkLabel(window, text='Start').grid(sticky='w',row=2,column=1, padx=ps/2)
    ck.CTkLabel(window, text='Stop').grid(sticky='w',row=2,column=3, padx=ps/2)
    ck.CTkEntry(window, textvariable=start, width=100).grid(row=2, column=2, padx=ps)
    ck.CTkEntry(window, textvariable=stop, width=100).grid(row=2, column=4, padx=ps)
    ck.CTkButton(window,text = 'Show Animation', width=120, command = lambda: (heatmap_animation(start.get(), stop.get())), height=40, fg_color=('lightgray'), text_color='black').grid(sticky='w', row=2, pady=ps, padx=(ps,0))
    ck.CTkButton(window,text = 'Draw Heatmap(s)', width=120, command = save_overall_heatmap, height=40).grid(sticky='w', row=3, pady=ps, padx=ps)
    ck.CTkButton(window,text = 'Show', command = open_heatmap, height=40, width=50).grid(row=3, column=1)
    ttk.Separator(window,orient='horizontal').grid(row=4, columnspan = 5,sticky='ew', pady=ps)

    window.mainloop()

if __name__ == "__main__":
   win_loop()