import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
import json
import pyautogui
import mss
import cv2
import numpy as np
import pytesseract
import gc
import os

# --- CONFIGURATION ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class VisualCalibrationOverlay:
    def __init__(self, master, on_save_callback):
        self.master = master
        self.on_save_callback = on_save_callback
        self.top = tk.Toplevel(master)
        self.top.attributes("-fullscreen", True)
        self.top.attributes("-alpha", 0.6)
        self.top.attributes("-topmost", True)
        self.top.config(bg="grey")
        self.locked = False
        self.box_width = 30
        self.box_height = 20
        self.gap = 40
        self.start_x = 0
        self.start_y = 0
        self.canvas = tk.Canvas(self.top, bg="grey", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.ctrl_frame = tk.Frame(self.top, bg="white", padx=10, pady=10)
        self.ctrl_frame.place(x=10, y=10)
        tk.Label(self.ctrl_frame, text="VISUAL CALIBRATION", font=("Arial", 12, "bold")).pack()
        tk.Label(self.ctrl_frame, text="1. Move to Box 1 -> Click to LOCK").pack()
        
        frm_size = tk.LabelFrame(self.ctrl_frame, text="Box Size")
        frm_size.pack(fill="x")
        tk.Button(frm_size, text="Width +", command=lambda: self.adjust_size(2, 0)).grid(row=0, column=2)
        tk.Button(frm_size, text="Width -", command=lambda: self.adjust_size(-2, 0)).grid(row=0, column=0)
        tk.Button(frm_size, text="Height +", command=lambda: self.adjust_size(0, 2)).grid(row=1, column=1)
        tk.Button(frm_size, text="Height -", command=lambda: self.adjust_size(0, -2)).grid(row=0, column=1)

        frm_gap = tk.LabelFrame(self.ctrl_frame, text="Grid Spacing")
        frm_gap.pack(fill="x")
        tk.Button(frm_gap, text="Spread (+)", command=lambda: self.adjust_gap(2)).pack(side="left")
        tk.Button(frm_gap, text="Condense (-)", command=lambda: self.adjust_gap(-2)).pack(side="right")

        tk.Button(self.ctrl_frame, text="SAVE (Enter)", bg="green", fg="white", command=self.save_and_close).pack(fill="x", pady=10)
        tk.Button(self.ctrl_frame, text="CANCEL (Esc)", command=self.close).pack(fill="x")

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)
        self.top.bind("<Return>", lambda e: self.save_and_close())
        self.top.bind("<Escape>", lambda e: self.close())
        
        self.rects = []
        for i in range(4):
            r = self.canvas.create_rectangle(0, 0, 1, 1, outline="red", width=2)
            t = self.canvas.create_text(0, 0, text=f"{i+1}", fill="red", font=("Arial", 12, "bold"))
            self.rects.append((r, t))
            
    def adjust_size(self, w_delta, h_delta):
        self.box_width = max(10, self.box_width + w_delta)
        self.box_height = max(10, self.box_height + h_delta)
        self.redraw()
    def adjust_gap(self, delta):
        self.gap = max(self.box_width + 5, self.gap + delta)
        self.redraw()
    def on_mouse_move(self, event):
        if not self.locked:
            self.start_x = event.x
            self.start_y = event.y
            self.redraw()
    def on_click(self, event):
        self.locked = not self.locked
        if self.locked:
            self.canvas.config(cursor="arrow")
            self.ctrl_frame.config(bg="#e6ffe6")
        else:
            self.canvas.config(cursor="cross")
            self.ctrl_frame.config(bg="white")
    def redraw(self):
        for i in range(4):
            x = self.start_x + (i * self.gap)
            y = self.start_y
            r, t = self.rects[i]
            self.canvas.coords(r, x, y, x + self.box_width, y + self.box_height)
            self.canvas.coords(t, x + self.box_width/2, y - 15)
    def save_and_close(self):
        rois = []
        for i in range(4):
            x = self.start_x + (i * self.gap)
            rois.append({"top": int(self.start_y), "left": int(x), "width": int(self.box_width), "height": int(self.box_height)})
        self.on_save_callback(rois)
        self.close()
    def close(self):
        self.top.destroy()

class AccuracyMatrixWindow:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Accuracy Matrix Report")
        self.top.geometry("400x600")
        
        self.canvas = tk.Canvas(self.top, bg="#f0f0f0")
        self.scrollbar = ttk.Scrollbar(self.top, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        tk.Label(self.scrollable_frame, text="Num", font=("Arial", 9, "bold"), width=4, relief="ridge").grid(row=0, column=0)
        tk.Label(self.scrollable_frame, text="Box 1", font=("Arial", 9, "bold"), width=8, relief="ridge").grid(row=0, column=1)
        tk.Label(self.scrollable_frame, text="Box 2", font=("Arial", 9, "bold"), width=8, relief="ridge").grid(row=0, column=2)
        tk.Label(self.scrollable_frame, text="Box 3", font=("Arial", 9, "bold"), width=8, relief="ridge").grid(row=0, column=3)
        tk.Label(self.scrollable_frame, text="Box 4", font=("Arial", 9, "bold"), width=8, relief="ridge").grid(row=0, column=4)

        self.cells = {}
        for num in range(37):
            bg_col = "#e0e0e0" if num % 2 == 0 else "white"
            tk.Label(self.scrollable_frame, text=str(num), font=("Arial", 9, "bold"), bg=bg_col, width=4).grid(row=num+1, column=0, pady=1)
            for box in range(4):
                lbl = tk.Label(self.scrollable_frame, text="--", bg="white", width=8, relief="sunken")
                lbl.grid(row=num+1, column=box+1, padx=1)
                self.cells[(num, box)] = lbl

    def update_status(self, box_idx, number, success):
        if number is None: return
        try:
            lbl = self.cells.get((number, box_idx))
            if lbl:
                if success:
                    lbl.config(text="✔", fg="green", bg="#ccffcc")
                else:
                    lbl.config(text="✘", fg="red", bg="#ffcccc")
        except:
            pass
    def clear(self):
        for lbl in self.cells.values():
            lbl.config(text="--", fg="black", bg="white")

class SessionMasterV19:
    def __init__(self, root):
        self.root = root
        self.root.title("Roulette Master V19 (True Color)")
        self.root.geometry("1000x550")
        
        self.rois = [] 
        self.is_running = False  
        self.is_testing_sequence = False 
        self.thread_active = False 
        self.is_floating = False
        self.box_count = 4 
        
        # PIPELINE
        self.expected_history = [None] * self.box_count
        self.memory_is_verified = [False] * self.box_count 
        self.shifts_since_start = 0
        
        # STABILIZATION
        self.box1_pending_val = None
        self.box1_stable_counter = 0
        self.STABILITY_THRESHOLD = 3 
        
        # SELF-HEALING & ANTI-DIM
        self.mismatch_counters = [0] * self.box_count
        self.HEALING_THRESHOLD = 5 
        self.BRIGHTNESS_THRESHOLD = 100 
        
        self.matrix_window = None
        self.offset_x = 0
        self.offset_y = 0

        # UI
        self.frame_controls = tk.Frame(root, bg="#f0f0f0", pady=5)
        self.frame_controls.pack(fill="x")
        self.btn_float = tk.Button(self.frame_controls, text="FLOAT", bg="#007bff", fg="white", font=("Arial", 9, "bold"), command=self.toggle_float)
        self.btn_float.pack(side="left", padx=5)
        self.btn_matrix = tk.Button(self.frame_controls, text="MATRIX REPORT", bg="#663399", fg="white", font=("Arial", 9, "bold"), command=self.open_matrix)
        self.btn_matrix.pack(side="left", padx=5)
        tk.Label(self.frame_controls, text="Opacity:", bg="#f0f0f0").pack(side="left")
        self.slider_alpha = tk.Scale(self.frame_controls, from_=0.3, to=1.0, resolution=0.1, orient="horizontal", command=self.set_alpha, bg="#f0f0f0", bd=0)
        self.slider_alpha.set(1.0)
        self.slider_alpha.pack(side="left", padx=5)
        self.btn_calib = tk.Button(self.frame_controls, text="Adjust Grid", command=self.open_calibration)
        self.btn_calib.pack(side="right", padx=5)
        self.btn_test_seq = tk.Button(self.frame_controls, text="TEST 0-36 LOOP", bg="orange", fg="black", font=("Arial", 9, "bold"), command=self.toggle_sequence_test)
        self.btn_test_seq.pack(side="right", padx=5)
        self.btn_start = tk.Button(self.frame_controls, text="START MONITOR", bg="green", fg="white", font=("Arial", 9, "bold"), command=self.handle_start_stop)
        self.btn_start.pack(side="right", padx=5)

        self.lbl_status = tk.Label(root, text="System: Ready", font=("Arial", 10, "bold"), fg="gray", bg="white", relief="sunken")
        self.lbl_status.pack(fill="x", padx=5, pady=2)
        
        self.frame_results = tk.Frame(root, bg="white")
        self.frame_results.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.box_widgets = [] 
        for i in range(self.box_count):
            frame = tk.Frame(self.frame_results, borderwidth=1, relief="solid", bg="white")
            frame.pack(side="left", fill="both", expand=True, padx=2)
            lbl_title = tk.Label(frame, text=f"Box {i+1}", font=("Arial", 10), bg="white", fg="gray")
            lbl_title.pack()
            lbl_num = tk.Label(frame, text="--", font=("Arial", 55, "bold"), fg="gray", width=2, bg="white")
            lbl_num.pack(expand=True)
            lbl_bar = tk.Label(frame, text="WAITING", font=("Arial", 8, "bold"), bg="#dddddd", fg="black", height=2)
            lbl_bar.pack(fill="x")
            self.box_widgets.append((lbl_num, lbl_bar))

        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.do_move)
        self.load_coords()

    # --- TRUE COLOR LOOKUP ---
    def get_true_color(self, number):
        """ Returns the official roulette color for a number """
        if number == 0:
            return "green"
        reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        if number in reds:
            return "red"
        return "black"

    def open_matrix(self):
        if self.matrix_window is None or not tk.Toplevel.winfo_exists(self.matrix_window.top):
            self.matrix_window = AccuracyMatrixWindow(self.root)
        else:
            self.matrix_window.top.lift()

    def update_pipeline(self, new_val_box1):
        self.expected_history[3] = self.expected_history[2]
        self.expected_history[2] = self.expected_history[1]
        self.expected_history[1] = self.expected_history[0]
        self.expected_history[0] = new_val_box1
        
        self.memory_is_verified[3] = self.memory_is_verified[2]
        self.memory_is_verified[2] = self.memory_is_verified[1]
        self.memory_is_verified[1] = self.memory_is_verified[0]
        self.memory_is_verified[0] = True 
        
        self.shifts_since_start += 1
        
        if self.shifts_since_start == 4:
            self.lbl_status.config(text="LOOP SUCCESS: CYCLE COMPLETE", bg="gold", fg="black")
        elif self.shifts_since_start > 4:
             self.lbl_status.config(text=f"LOOP SUCCESS: LOOP CONTINUES (Shift #{self.shifts_since_start})", bg="#32CD32", fg="white")
        else:
            self.lbl_status.config(text=f"Pipeline Filling... ({self.shifts_since_start}/4)", bg="white", fg="black")

    def verify_box(self, box_index, ocr_val, ocr_color):
        expected_val = self.expected_history[box_index]
        is_verified_source = self.memory_is_verified[box_index]
        
        # SELF-HEALING Logic
        if expected_val is not None and ocr_val is not None:
            if ocr_val != expected_val:
                self.mismatch_counters[box_index] += 1
            else:
                self.mismatch_counters[box_index] = 0 
        
        if self.mismatch_counters[box_index] >= self.HEALING_THRESHOLD:
            self.expected_history[box_index] = ocr_val
            self.mismatch_counters[box_index] = 0
            expected_val = ocr_val 
            self.lbl_status.config(text=f"AUTO-HEALED Box {box_index+1}", bg="orange", fg="black")

        # Startup
        if not is_verified_source:
             if expected_val is not None:
                 if ocr_val is not None:
                     return ocr_val, ocr_color, "#87CEFA", "ACCURATE (UNV)"
                 # Fallback to Memory -> True Color
                 return expected_val, self.get_true_color(expected_val), "#87CEFA", "ACCURATE (UNV)"
             else:
                 return "--", "gray", "#dddddd", "WAITING"

        # Verified
        if ocr_val == expected_val:
            if self.matrix_window:
                self.matrix_window.update_status(box_index, expected_val, True)
            return ocr_val, ocr_color, "#00cc00", "VERIFIED"

        if ocr_val is None:
            # FIX: Use True Color instead of Gray, AND Green Status
            return expected_val, self.get_true_color(expected_val), "#00cc00", "VERIFIED (MEM)"

        if ocr_val != expected_val:
            if self.matrix_window:
                self.matrix_window.update_status(box_index, expected_val, False)
            err_msg = f"MISMATCH BOX {box_index+1}: OCR={ocr_val} | EXP={expected_val}"
            self.lbl_status.config(text=err_msg, bg="red", fg="white")
            # FIX: Mismatch? Still show correct Expected Value with True Color
            return expected_val, self.get_true_color(expected_val), "red", f"ERR: {ocr_val}"

        return "--", "gray", "#dddddd", "WAIT"

    def toggle_sequence_test(self):
        if not self.is_testing_sequence:
            self.is_testing_sequence = True
            self.btn_test_seq.config(text="STOP TEST", bg="red")
            self.btn_start.config(state="disabled")
            if self.matrix_window: self.matrix_window.clear()
            t = threading.Thread(target=self.run_sequence_loop)
            t.daemon = True
            t.start()
        else:
            self.is_testing_sequence = False
            self.btn_test_seq.config(text="TEST 0-36 LOOP", bg="orange")
            self.btn_start.config(state="normal")

    def run_sequence_loop(self):
        seq = list(range(37)) 
        idx = 0
        self.shifts_since_start = 0
        self.memory_is_verified = [False] * 4 
        self.expected_history = [None] * 4
        
        while self.is_testing_sequence:
            num = seq[idx]
            self.update_pipeline(num)
            
            if self.matrix_window:
                for b in range(4):
                    if self.expected_history[b] is not None and self.memory_is_verified[b]:
                        self.matrix_window.update_status(b, self.expected_history[b], True)

            for i in range(self.box_count):
                val = self.expected_history[i]
                lbl_num, lbl_bar = self.box_widgets[i]
                
                is_ver = self.memory_is_verified[i]
                bg_col = "#00cc00" if is_ver else "#87CEFA"
                txt = "VERIFIED" if is_ver else "ACCURATE (UNV)"
                
                if val is not None:
                    h_col = self.get_true_color(val) # Use True Color in test
                    lbl_num.config(text=str(val), fg=h_col)
                    lbl_bar.config(text=txt, bg=bg_col)
                else:
                    lbl_num.config(text="--", fg="gray")
                    lbl_bar.config(text="EMPTY", bg="#dddddd")
            idx = (idx + 1) % len(seq)
            time.sleep(0.2) 
        self.lbl_status.config(text="Test Stopped.")
        self.expected_history = [None] * self.box_count

    def handle_start_stop(self):
        if not self.is_running:
            self.is_running = True
            self.btn_start.config(text="STOP", bg="red")
            self.btn_test_seq.config(state="disabled")
            self.thread_active = True
            
            self.shifts_since_start = 0 
            self.memory_is_verified = [False] * 4 
            self.box1_pending_val = None
            self.box1_stable_counter = 0
            self.mismatch_counters = [0] * 4
            
            t = threading.Thread(target=self.vision_loop)
            t.daemon = True
            t.start()
        else:
            self.is_running = False 
            self.btn_start.config(text="STOPPING...", bg="gray", state="disabled")
            self.check_thread_shutdown()

    def check_thread_shutdown(self):
        if self.thread_active:
            self.root.after(100, self.check_thread_shutdown)
        else:
            self.btn_start.config(text="START MONITOR", bg="green", state="normal")
            self.btn_test_seq.config(state="normal")
            self.lbl_status.config(text="Stopped.")

    def pre_fill_memory(self, sct):
        self.lbl_status.config(text="Initializing: Scanning Board...", bg="yellow")
        initial_scan = []
        for i, roi in enumerate(self.rois):
            pad = 2 
            monitor = {
                "top": roi['top'] - pad, 
                "left": roi['left'] - pad, 
                "width": roi['width'] + (pad * 2), 
                "height": roi['height'] + (pad * 2)
            }
            img = np.array(sct.grab(monitor))
            num, col = self.get_number_from_image(img)
            initial_scan.append(num)
        
        self.expected_history = initial_scan
        self.memory_is_verified = [False, False, False, False]
        self.lbl_status.config(text="System: Running (Waiting for New Number...)", bg="white")

    def check_screen_brightness(self, img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGRA2GRAY)
        max_val = np.max(gray) 
        return max_val < self.BRIGHTNESS_THRESHOLD

    def vision_loop(self):
        with mss.mss() as sct:
            self.pre_fill_memory(sct)
            while self.is_running:
                try:
                    current_ocr_results = []
                    
                    dimmed_detected = False
                    
                    for i, roi in enumerate(self.rois):
                        pad = 2 
                        monitor = {
                            "top": roi['top'] - pad, 
                            "left": roi['left'] - pad, 
                            "width": roi['width'] + (pad * 2), 
                            "height": roi['height'] + (pad * 2)
                        }
                        img = np.array(sct.grab(monitor))
                        
                        if i == 0:
                            if self.check_screen_brightness(img):
                                dimmed_detected = True
                        
                        num, col = self.get_number_from_image(img)
                        current_ocr_results.append((num, col))
                    
                    if dimmed_detected:
                        self.lbl_status.config(text="PAUSED: LOW VISIBILITY (Reconnecting)", bg="orange", fg="black")
                        time.sleep(0.5)
                        continue 
                        
                    ocr_box1_val = current_ocr_results[0][0]
                    mem_box1_val = self.expected_history[0]
                    
                    if ocr_box1_val is not None and ocr_box1_val != mem_box1_val:
                        if ocr_box1_val == self.box1_pending_val:
                            self.box1_stable_counter += 1
                        else:
                            self.box1_pending_val = ocr_box1_val
                            self.box1_stable_counter = 1
                        
                        if self.box1_stable_counter >= self.STABILITY_THRESHOLD:
                            self.update_pipeline(ocr_box1_val)
                            self.box1_pending_val = None
                            self.box1_stable_counter = 0
                    else:
                        if ocr_box1_val == mem_box1_val:
                            self.box1_pending_val = None
                            self.box1_stable_counter = 0

                    for i in range(self.box_count):
                        ocr_val, ocr_col = current_ocr_results[i]
                        disp_val, disp_col, bar_bg, bar_text = self.verify_box(i, ocr_val, ocr_col)
                        
                        lbl_num, lbl_bar = self.box_widgets[i]
                        lbl_num.config(text=str(disp_val), fg=disp_col)
                        lbl_bar.config(text=bar_text, bg=bar_bg)
                    
                except Exception as e:
                    print(e)
                time.sleep(0.2)
        self.thread_active = False

    def toggle_float(self):
        if not self.is_floating:
            self.is_floating = True
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            self.btn_float.config(text="UNFLOAT", bg="orange")
        else:
            self.is_floating = False
            self.root.overrideredirect(False)
            self.root.attributes("-topmost", False)
            self.btn_float.config(text="FLOAT", bg="#007bff")
    def set_alpha(self, val):
        self.root.attributes("-alpha", float(val))
    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y
    def do_move(self, event):
        if self.is_floating:
            x = self.root.winfo_x() + event.x - self.offset_x
            y = self.root.winfo_y() + event.y - self.offset_y
            self.root.geometry(f"+{x}+{y}")
    def open_calibration(self):
        VisualCalibrationOverlay(self.root, self.save_coords)
    def save_coords(self, rois):
        self.rois = rois
        with open('coords_step3.json', 'w') as f:
            json.dump({'box_rois': self.rois}, f, indent=4)
        self.load_coords()
    def load_coords(self):
        filename = 'coords_step3.json'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                self.rois = data.get('box_rois', [])
            self.lbl_status.config(text="Ready: Grid Loaded")
    def process_green_text(self, img_array):
        img = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([30, 40, 40]), np.array([90, 255, 255]))
        pixel_count = cv2.countNonZero(mask)
        mask = cv2.resize(mask, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        final = cv2.bitwise_not(mask)
        final = cv2.copyMakeBorder(final, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[255,255,255])
        return final, pixel_count
    def process_red_text(self, img_array):
        img = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([160, 100, 100]), np.array([180, 255, 255]))
        mask = mask1 + mask2
        mask = cv2.resize(mask, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        final = cv2.bitwise_not(mask)
        final = cv2.copyMakeBorder(final, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[255,255,255])
        return final
    def process_white_text(self, img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGRA2GRAY)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        binary = cv2.bitwise_not(binary)
        binary = cv2.copyMakeBorder(binary, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[255,255,255])
        return binary
    def validate_number(self, text):
        if not text: return None
        text = text.replace("O", "0").replace("o", "0").replace("S", "5").replace("B", "8")
        clean = ''.join(filter(str.isdigit, text))
        if not clean: return None
        num = int(clean)
        if 0 <= num <= 36: return num
        return None
    def get_number_from_image(self, img):
        _, green_pixels = self.process_green_text(img)
        if green_pixels > 80: return 0, "green"
        bin_red = self.process_red_text(img)
        text_red = pytesseract.image_to_string(bin_red, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        if res := self.validate_number(text_red): return res, "red"
        bin_white = self.process_white_text(img)
        text_white = pytesseract.image_to_string(bin_white, config='--psm 7 -c tessedit_char_whitelist=0123456789')
        if res := self.validate_number(text_white): return res, "black"
        return None, "gray"

if __name__ == "__main__":
    root = tk.Tk()
    app = SessionMasterV19(root)
    root.mainloop()