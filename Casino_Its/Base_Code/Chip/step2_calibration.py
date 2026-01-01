import tkinter as tk
from tkinter import messagebox
import threading
import time
import json
import pyautogui
import keyboard
import serial
import random
import winsound

# --- CONFIGURATION ---
ARDUINO_PORT = 'COM7'  # <--- CHECK PORT
BAUD_RATE = 9600

# Safety: Fail-safe corner (Upper left)
pyautogui.FAILSAFE = True 

def human_move(x, y):
    """
    Moves the mouse to x,y in a way that looks human
    """
    duration = random.uniform(0.3, 0.7)
    pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeOutQuad)

class HandsToolV4:
    def __init__(self, root):
        self.root = root
        self.root.title("Step 2: Chip Calibrator (Auto-Hide)")
        self.root.geometry("550x400")
        
        # Keep window on top so you can find it easily
        self.root.attributes('-topmost', True) 
        
        self.coords = {
            'chip_001': None,
            'chip_01': None
        }
        self.arduino = None
        
        # --- UI HEADER ---
        tk.Label(root, text="Step 2: Chip Selector", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(root, text="Window hides automatically during MAP and TEST", fg="blue").pack()
        
        self.lbl_hw = tk.Label(root, text="Arduino: Connecting...", fg="orange", font=("Arial", 10))
        self.lbl_hw.pack(pady=5)
        
        # --- CONTROL GRID ---
        self.frame_controls = tk.Frame(root, padx=20, pady=20)
        self.frame_controls.pack(fill="both", expand=True)
        
        tk.Label(self.frame_controls, text="TARGET", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Label(self.frame_controls, text="STATUS", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=10, pady=10)
        tk.Label(self.frame_controls, text="ACTIONS", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=10, pady=10)

        # 1. 0.01 Chip
        tk.Label(self.frame_controls, text="0.01 Chip").grid(row=1, column=0, sticky="w")
        self.lbl_001_stat = tk.Label(self.frame_controls, text="Not Set", fg="red")
        self.lbl_001_stat.grid(row=1, column=1)
        f_001 = tk.Frame(self.frame_controls)
        f_001.grid(row=1, column=2)
        tk.Button(f_001, text="MAP", bg="#e6f2ff", width=8, command=lambda: self.start_map("chip_001")).pack(side="left", padx=2)
        self.btn_test_001 = tk.Button(f_001, text="TEST", bg="blue", fg="white", width=8, state="disabled", command=lambda: self.start_test("chip_001"))
        self.btn_test_001.pack(side="left", padx=2)

        # 2. 0.1 Chip
        tk.Label(self.frame_controls, text="0.10 Chip").grid(row=2, column=0, sticky="w")
        self.lbl_01_stat = tk.Label(self.frame_controls, text="Not Set", fg="red")
        self.lbl_01_stat.grid(row=2, column=1)
        f_01 = tk.Frame(self.frame_controls)
        f_01.grid(row=2, column=2)
        tk.Button(f_01, text="MAP", bg="#ffffcc", width=8, command=lambda: self.start_map("chip_01")).pack(side="left", padx=2)
        self.btn_test_01 = tk.Button(f_01, text="TEST", bg="gold", width=8, state="disabled", command=lambda: self.start_test("chip_01"))
        self.btn_test_01.pack(side="left", padx=2)
        
        # Log
        self.lbl_log = tk.Label(root, text="Log: Ready", fg="gray", font=("Courier", 10))
        self.lbl_log.pack(side="bottom", pady=15)

        self.connect_arduino()
        self.load_existing_coords()

    def log(self, text):
        self.lbl_log.config(text=f"Log: {text}")

    def connect_arduino(self):
        try:
            self.arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=0.1)
            time.sleep(2)
            self.lbl_hw.config(text=f"Arduino: Connected ({ARDUINO_PORT})", fg="green")
        except Exception as e:
            self.lbl_hw.config(text="Arduino: NOT FOUND", fg="red")

    def load_existing_coords(self):
        try:
            with open('coords_step2.json', 'r') as f:
                data = json.load(f)
                if 'chip_001' in data: self.coords['chip_001'] = data['chip_001']
                if 'chip_01' in data: self.coords['chip_01'] = data['chip_01']
            
            if self.coords.get('chip_001'): 
                self.lbl_001_stat.config(text="OK", fg="green")
                self.btn_test_001.config(state="normal")
            if self.coords.get('chip_01'): 
                self.lbl_01_stat.config(text="OK", fg="green")
                self.btn_test_01.config(state="normal")
            self.log("Loaded existing map.")
        except:
            self.log("No existing map found.")

    # --- MAPPING ---
    def start_map(self, key):
        t = threading.Thread(target=self.run_map_sequence, args=(key,))
        t.daemon = True
        t.start()

    def run_map_sequence(self, key):
        # HIDE
        self.root.withdraw()
        time.sleep(0.5) 
        
        winsound.Beep(600, 200) # Ready beep
        
        # Wait for user input
        while not keyboard.is_pressed('enter'): 
            time.sleep(0.05)
        while keyboard.is_pressed('enter'): 
            time.sleep(0.05)
        
        # Capture
        x, y = pyautogui.position()
        self.coords[key] = {'x': x, 'y': y}
        
        with open('coords_step2.json', 'w') as f:
            json.dump(self.coords, f, indent=4)
        
        winsound.Beep(1000, 200) # Success beep
        
        # SHOW
        self.root.deiconify()
        self.root.after(0, lambda: self.update_ui_after_map(key))

    def update_ui_after_map(self, key):
        self.log(f"Saved {key}")
        if key == 'chip_001':
            self.lbl_001_stat.config(text="OK", fg="green")
            self.btn_test_001.config(state="normal")
        elif key == 'chip_01':
            self.lbl_01_stat.config(text="OK", fg="green")
            self.btn_test_01.config(state="normal")

    # --- TESTING (HYBRID) ---
    def start_test(self, key):
        t = threading.Thread(target=self.run_test_sequence, args=(key,))
        t.daemon = True
        t.start()

    def run_test_sequence(self, key):
        if not self.arduino:
            self.log("Error: Arduino not connected")
            return
            
        target = self.coords[key]
        if not target: return
        
        # --- FIX: HIDE WINDOW BEFORE MOVING ---
        self.root.withdraw()
        time.sleep(0.5) # Brief pause so visual disturbance is gone
        
        # Move
        human_move(target['x'], target['y'])
        
        # Click
        self.arduino.write(b"CLICK\n")
        
        # --- RESTORE WINDOW ---
        time.sleep(0.2) # Wait a tiny bit after click
        self.root.deiconify()
        
        self.log(f"Done: {key}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HandsToolV4(root)
    root.mainloop()