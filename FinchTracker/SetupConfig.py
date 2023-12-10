import tkinter as tk
from tkinter import ttk
import customtkinter as ck
import json
from SetupBirdConfig import bird_win_loop, load_config, update_config, add_birds, display_ids
from DetectAruco_PiSide import main as detect, get_aruco_detector
import cv2
import numpy as np

config_list = []
config_path = 'config.json'
bird_config_path = 'bird_config.json'
ck.set_appearance_mode('dark')
ps = 10

def win_loop():
    print('Initializing window')
    window = ck.CTk()
    window.geometry('520x600')
    window.title('SetupConfig')
    window.resizable(False,False)

    config = load_config(config_path)
    bird_config = load_config(bird_config_path)
    config_entry = []
    for i in range(len(config)):
        config_entry.append(tk.StringVar())

    #Left Side Finch Config
    ck.CTkLabel(window, text='Finch Tracker Configuration', font=('Times', 20)).grid(row=0, columnspan=2, padx=ps, pady=ps)
    
    for i, item in enumerate(config.items()):
        key, val = item
        ck.CTkLabel(window, text=key).grid(sticky='w',row=i+1, padx=(ps))
        curr_entry = ck.CTkEntry(window, textvariable=config_entry[i])
        curr_entry.grid(row=i+1, column=1, padx=(ps), pady=2)
        curr_entry.insert(0, val)

    ttk.Separator(window,orient='horizontal').grid(row=len(config)+1, columnspan = 2,sticky='ew', pady=ps)
    ck.CTkButton(window,text = 'Update', command = lambda: [update_config(config, config_entry, config_path), add_birds(bird_config), display_ids(window)]).grid(row=len(config)+2, columnspan =2, pady=10)

    #Right Side ArUco Config
    ck.CTkLabel(window, text='ArUco Barcode', font=('Times', 20)).grid(row=0, column=2, columnspan=2)
    ck.CTkLabel(window, text='Dictionary Type: DICT_4X4_250').grid(row=1, column=2, columnspan=2)
    ck.CTkLabel(window, text=f'ArUco Code\tBird ID').grid(sticky='w',row=2, column=2, padx=(ps,0))
    display_ids(window)
    ck.CTkButton(window, text = 'Set Bird IDs', command = lambda: bird_win_loop(window)).grid(row=11, column=2, columnspan =2)
    ck.CTkButton(window, text = '👁️Cam View(s)', command = lambda: draw_frames(config), height=40, font=('Roboto', 14)).grid(row=13, column=2, columnspan =2)


    ck.CTkButton(window,text = 'Start Recording', command = lambda: [window.destroy(), detect()], fg_color=('lightgray'),text_color=('black'), font=('Roboto',18), height=40).grid(row=len(config)+2, column=2, pady=ps, padx=(ps,0))

    window.mainloop()

def draw_frames(config):
    print('Loading camera previews...')
    config = load_config(config_path)
    aruco_detector = get_aruco_detector()
    vid_cap = []

    for i in range(config['num_cameras']):
        vid_cap.append(cv2.VideoCapture(i)) 
    for i in range(config['num_cameras']):
        while True:
            for i in range(config['num_cameras']):
                ret, frame = vid_cap[i].read() 
                if frame is None:
                    break
                cv2.putText(frame,'Press \'q\' to Exit Camera View', org=(20,20), fontFace=cv2.FONT_HERSHEY_COMPLEX, fontScale=0.7, color=(0,0,0))
                aru_points, aru_decoded, rejected_marker = aruco_detector.detectMarkers(frame)
                if aru_decoded is not None:
                    for code in aru_decoded:
                        frame = cv2.polylines(frame, np.int32(aru_points), True, (255, 0, 255), 4)
                cv2.imshow(f'Camera {i} View', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break
        cv2.destroyAllWindows() 

if __name__ == "__main__":
   win_loop()