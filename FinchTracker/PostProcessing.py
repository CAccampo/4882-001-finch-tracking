import tkinter as tk
from tkinter import ttk
import customtkinter as ck
from heatmap import main as draw_heatmap

ps = 10

def win_loop():
    print('Initializing window')
    window = ck.CTk()
    window.geometry('520x600')
    window.title('SetupConfig')
    window.resizable(False,False)


    ck.CTkButton(window,text = 'Heatmap Animation', command = draw_heatmap, fg_color=('lightgray'),text_color=('black'), font=('Roboto',18), height=40).grid(row=3, column=2, pady=ps, padx=(ps,0))

    window.mainloop()

if __name__ == "__main__":
   win_loop()