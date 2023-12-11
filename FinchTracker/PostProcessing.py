import tkinter as tk
from tkinter import ttk
import customtkinter as ck
import cv2
from heatmap import main as draw_heatmap
from SetupBirdConfig import load_config
import numpy as np
import imageio.v3 as iio

ps = 10
def open_heatmap():
    config = load_config('config.json')
    for i in range(config['num_cameras']):
        heatmap_img = iio.imread(f'heatmap{i}.png')
        cv2.imshow(f'Heatmap {i}', heatmap_img)

def win_loop():
    print('Initializing window')
    window = ck.CTk()
    window.geometry('520x600')
    window.title('SetupConfig')
    window.resizable(False,False)


    ck.CTkButton(window,text = 'Heatmap Animation', command = draw_heatmap, fg_color=('lightgray'),text_color=('black'), font=('Roboto',18), height=40).grid(row=2, column=2, pady=ps, padx=(ps,0))
    ck.CTkButton(window,text = 'Heatmap Overall', command = open_heatmap, fg_color=('lightgray'),text_color=('black'), font=('Roboto',18), height=40).grid(row=3, column=2, pady=ps, padx=(ps,0))

    window.mainloop()

if __name__ == "__main__":
   win_loop()