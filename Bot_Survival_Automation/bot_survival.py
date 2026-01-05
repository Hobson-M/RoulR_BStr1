import tkinter as tk
from tkinter import messagebox
import threading
import time
import pyautogui
import mss
import cv2
import numpy as np
import pytesseract
import os
import json
import sys

# --- CONFIGURATION ---
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

class BoxSelector:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.title("Draw Box")
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
        self.start_x = None; self.start_y = None; self.rect = None; self.selection = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.wait_window()
    def on_press(self, event): self.start_x = event.x; self.start_y = event.y; self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
    def on_drag(self, event): self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    def on_release(self, event):
        x1, y1, x2, y2 = min(self.start_x, event.x), min(self.start_y, event.y), max(self.start_x, event.x), max(self.start_y, event.y)
        if x2 - x1 > 5 and y2 - y1 > 5: self.selection = {'top': y1, 'left': x1, 'width': x2-x1, 'height': y2-y1}
        self.root.destroy()

class FieldTestRecorderV20:
    def __init__(self, root):
        self.root = root
        self.root.title("Step 3.2: Survival V20 (INFINITY SCROLL)")
        self.root.geometry("900x900") # Increased height for new stage
        self.root.attributes('-topmost', True)
        
        self.config = {
            'central_roi': None,
            'stage1_data': None, 
            'stage2_data': None,
            'stage3_img': None,
            'stage4_roi': None,
            'stage4_data': None,
            'stage5_img': None,
            'stage6_img': None,
            'stage7_data': None # ADDED FOR STAGE 7
        }
        
        tk.Label(root, text="Step 3.2: Survival V20 (Infinity Scroll)", font=("Arial", 16, "bold"), fg="purple").pack(pady=10)
        
        self.frame_steps = tk.Frame(root, padx=10, pady=10)
        self.frame_steps.pack(fill="both", expand=True)
        self.labels = {}

        self.lbl_log = tk.Label(root, text="Log: Initializing...", fg="blue", font=("Courier", 10), wraplength=850, justify="left")
        self.lbl_log.pack(side="bottom", pady=10)

        if not os.path.exists(TESSERACT_PATH):
            self.log(f"CRITICAL: Tesseract not found at {TESSERACT_PATH}", color="red")
        else:
            self.log("Tesseract found. Ready.", color="green")

        # --- SECTIONS ---
        # 1. KEEP ALIVE
        frame_roi = tk.Frame(self.frame_steps, relief="groove", borderwidth=1)
        frame_roi.pack(fill="x", pady=5)
        tk.Button(frame_roi, text="SET CENTRAL ROI", bg="#ffe0b2", width=15, command=self.set_central_roi).pack(side="left", padx=5)
        self.lbl_roi_stat = tk.Label(frame_roi, text="[ROI PENDING]", fg="red", font=("Arial", 9)); self.lbl_roi_stat.pack(side="left")

        self.create_text_action_stage(1, "Inactivity Pause", "Inactivity", "stage1_data")
        self.create_hybrid_stage_shared(2, "Session Crash", "Session", "btn_crash_ok.png", "stage2_data")
        
        # 2. RECOVERY (ALL DYNAMIC NOW)
        self.create_image_stage(3, "Find Provider (Dynamic)", "pragmatic_logo.png", "stage3_img")
        
        f_top = tk.Frame(self.frame_steps); f_top.pack(fill="x", pady=10)
        tk.Button(f_top, text="SET LOBBY ROI", bg="#ffe0b2", width=15, command=self.set_lobby_roi).pack(side="left", padx=5)
        self.lbl_lobby_roi = tk.Label(f_top, text="[ROI PENDING]", fg="red", font=("Arial", 9)); self.lbl_lobby_roi.pack(side="left")

        self.create_lobby_text_click_stage(4, "Select Table (Dynamic)", "Stake Roulette", "target_table_name.png", "stage4_data")
        self.create_image_stage(5, "Full Screen (Dynamic)", "btn_fullscreen.png", "stage5_img")
        
        # --- STAGE 6: ISOLATED OK ---
        self.create_static_image_only_stage(6, "Isolated OK Button", "btn_crash_ok.png", "stage6_img")

        # --- NEW STAGE 7: DEAD-END SESSION (F5 REFRESH) ---
        # Trigger: Text found BUT Button MISSING -> Press F5
        self.create_refresh_stage(7, "Dead-end Session (F5)", "Session", "btn_crash_ok.png", "stage7_data")
        
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists('survival_config.json'):
                with open('survival_config.json', 'r') as f:
                    data = json.load(f)
                    for k, v in data.items(): self.config[k] = v
                if self.config.get('central_roi'): self.lbl_roi_stat.config(text="[ROI SET]", fg="green")
                if self.config.get('stage4_roi'): 
                    if hasattr(self, 'lbl_lobby_roi'): self.lbl_lobby_roi.config(text="[ROI SET]", fg="green")
                self.log("Config loaded successfully.", color="purple")
        except Exception as e: self.log(f"Config Load Error: {e}", color="red")

    # --- UI HELPERS ---
    def create_text_action_stage(self, num, label, def_trigger, key):
        f = tk.Frame(self.frame_steps); f.pack(fill="x", pady=2)
        tk.Label(f, text=f"Stage {num}: {label}", width=20, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
        e = tk.Entry(f, width=10); e.insert(0, def_trigger); e.pack(side="left")
        lbl = tk.Label(f, text="[PENDING]", fg="gray", width=10); lbl.pack(side="right")
        self.labels[num] = lbl
        tk.Button(f, text="TEST", bg="#e1f5fe", command=lambda: self.test_stage_1(e.get(), lbl)).pack(side="right")

    def create_hybrid_stage_shared(self, num, label, def_trigger, filename, key):
        f = tk.Frame(self.frame_steps); f.pack(fill="x", pady=2)
        tk.Label(f, text=f"Stage {num}: {label}", width=20, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
        e = tk.Entry(f, width=10); e.insert(0, def_trigger); e.pack(side="left")
        tk.Button(f, text="SNIP", bg="#fff9c4", command=lambda: self.snip(filename)).pack(side="left", padx=2)
        lbl = tk.Label(f, text="[PENDING]", fg="gray", width=10); lbl.pack(side="right")
        self.labels[num] = lbl
        tk.Button(f, text="TEST", bg="#e1f5fe", command=lambda: self.test_stage_2(e.get(), filename, lbl)).pack(side="right")

    def create_image_stage(self, num, label, filename, key):
        f = tk.Frame(self.frame_steps); f.pack(fill="x", pady=2)
        tk.Label(f, text=f"Stage {num}: {label}", width=20, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
        tk.Button(f, text="SNIP", bg="#fff9c4", command=lambda: self.snip(filename)).pack(side="left", padx=2)
        lbl = tk.Label(f, text="[PENDING]", fg="gray", width=10); lbl.pack(side="right")
        self.labels[num] = lbl
        tk.Button(f, text="TEST", bg="#c8e6c9", command=lambda: self.test_image(num, filename, lbl, key)).pack(side="right")

    def create_lobby_text_click_stage(self, num, label, def_trigger, filename, key):
        f = tk.Frame(self.frame_steps); f.pack(fill="x", pady=2)
        tk.Label(f, text=f"Stage {num}: {label}", width=20, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
        e = tk.Entry(f, width=12); e.insert(0, def_trigger); e.pack(side="left")
        tk.Button(f, text="SNIP", bg="#fff9c4", command=lambda: self.snip(filename)).pack(side="left", padx=2)
        lbl = tk.Label(f, text="[PENDING]", fg="gray", width=10); lbl.pack(side="right")
        self.labels[num] = lbl
        tk.Button(f, text="TEST", bg="#e1f5fe", command=lambda: self.test_stage_4(e.get(), filename, lbl)).pack(side="right")

    def create_static_image_only_stage(self, num, label, filename, key):
        f = tk.Frame(self.frame_steps); f.pack(fill="x", pady=2)
        tk.Label(f, text=f"Stage {num}: {label}", width=20, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
        tk.Button(f, text="SNIP", bg="#fff9c4", command=lambda: self.snip(filename)).pack(side="left", padx=2)
        lbl = tk.Label(f, text="[PENDING]", fg="gray", width=10); lbl.pack(side="right")
        self.labels[num] = lbl
        tk.Button(f, text="TEST", bg="#e1f5fe", command=lambda: self.test_stage_6(filename, lbl, key)).pack(side="right")

    # --- NEW HELPER FOR STAGE 7 (TEXT + NO BUTTON -> REFRESH) ---
    def create_refresh_stage(self, num, label, def_trigger, btn_filename, key):
        f = tk.Frame(self.frame_steps); f.pack(fill="x", pady=2)
        tk.Label(f, text=f"Stage {num}: {label}", width=20, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
        e = tk.Entry(f, width=10); e.insert(0, def_trigger); e.pack(side="left")
        lbl = tk.Label(f, text="[PENDING]", fg="gray", width=10); lbl.pack(side="right")
        self.labels[num] = lbl
        tk.Button(f, text="TEST", bg="#ffccbc", command=lambda: self.test_stage_7(e.get(), btn_filename, lbl, key)).pack(side="right")

    # --- ACTIONS ---
    def set_central_roi(self): self._set_roi('central_roi', self.lbl_roi_stat)
    def set_lobby_roi(self): self._set_roi('stage4_roi', self.lbl_lobby_roi)

    def _set_roi(self, key, label_widget):
        self.root.withdraw(); time.sleep(0.3)
        selector = BoxSelector(self.root); self.root.deiconify()
        if selector.selection:
            self.config[key] = selector.selection
            label_widget.config(text="[ROI SET]", fg="green")
            self.save_config()

    def save_config(self):
        with open('survival_config.json', 'w') as f: json.dump(self.config, f, indent=4)
    
    def log(self, text, color="blue"): 
        print(f"LOG: {text}")
        self.lbl_log.config(text=f"Log: {text}", fg=color)

    def snip(self, filename):
        self.root.withdraw(); time.sleep(0.5)
        selector = BoxSelector(self.root); self.root.deiconify()
        if selector.selection:
            with mss.mss() as sct:
                img = np.array(sct.grab(selector.selection))
                cv2.imwrite(filename, cv2.cvtColor(img, cv2.COLOR_BGRA2BGR))
            self.log(f"Snipped {filename}.", color="green")

    def perform_action(self, x, y, label, key, value):
        self.log(f"Action: Click at {x},{y}", color="orange")
        pyautogui.click(x, y)
        self.root.after(0, lambda: self.mark_pass(label, key, value))

    def mark_pass(self, label, key, value):
        label.config(text="[PASSED]", fg="green")
        self.config[key] = value
        self.save_config()
        self.log(f"Stage {key} Saved.", color="green")

    # --- WORKERS ---
    def test_stage_1(self, trigger, label):
        roi = self.config.get('central_roi')
        if not roi: self.log("Error: Central ROI not set!", "red"); return
        self.log(f"Stage 1: Waiting 5s...", "red")
        threading.Thread(target=self._worker_stage_1, args=(trigger, label, roi), daemon=True).start()

    def _worker_stage_1(self, trigger, label, roi):
        try:
            time.sleep(5)
            if self._check_text_in_roi(roi, trigger):
                cx, cy = roi['left'] + roi['width']//2, roi['top'] + roi['height']//2
                self.root.after(0, lambda: self.perform_action(cx, cy, label, "stage1_data", {'trigger':trigger}))
            else: self.root.after(0, lambda: self.log(f"Stage 1 Fail: Text '{trigger}' not found", "red"))
        except Exception as e: self.root.after(0, lambda: self.log(f"CRASH S1: {e}", "red"))

    def test_stage_2(self, trigger, btn_file, label):
        roi = self.config.get('central_roi')
        if not roi: self.log("Error: Central ROI not set!", "red"); return
        self.log(f"Stage 2: Waiting 5s...", "red")
        threading.Thread(target=self._worker_stage_2, args=(trigger, btn_file, label, roi), daemon=True).start()

    def _worker_stage_2(self, trigger, btn_file, label, roi):
        try:
            time.sleep(5)
            if self._check_text_in_roi(roi, trigger):
                self._find_click_img_static(roi, btn_file, label, "stage2_data", trigger)
            else: self.root.after(0, lambda: self.log(f"Stage 2 Fail: Text '{trigger}' not found", "red"))
        except Exception as e: self.root.after(0, lambda: self.log(f"CRASH S2: {e}", "red"))

    def test_stage_6(self, filename, label, key):
        roi = self.config.get('central_roi')
        if not roi: self.log("Error: Central ROI not set! (Stage 6 uses Central)", "red"); return
        if not os.path.exists(filename): self.log(f"Error: {filename} missing", "red"); return
        self.log(f"Stage 6: Waiting 5s...", "red")
        threading.Thread(target=self._worker_stage_6, args=(filename, label, roi, key), daemon=True).start()

    def _worker_stage_6(self, filename, label, roi, key):
        try:
            time.sleep(5)
            self._find_click_img_static(roi, filename, label, key, "Isolated OK")
        except Exception as e: self.root.after(0, lambda: self.log(f"CRASH S6: {e}", "red"))

    # --- WORKER STAGE 7: REFRESH IF TEXT EXISTS & BTN MISSING ---
    def test_stage_7(self, trigger, btn_filename, label, key):
        roi = self.config.get('central_roi')
        if not roi: self.log("Error: Central ROI not set!", "red"); return
        self.log(f"Stage 7: Waiting 5s...", "red")
        threading.Thread(target=self._worker_stage_7, args=(trigger, btn_filename, label, roi, key), daemon=True).start()

    def _worker_stage_7(self, trigger, btn_filename, label, roi, key):
        try:
            time.sleep(5)
            # 1. Check if TEXT is present (Collision check with Stage 2)
            if self._check_text_in_roi(roi, trigger):
                self.root.after(0, lambda: self.log(f"S7: Trigger '{trigger}' found. Checking for button...", "blue"))
                
                # 2. Check if BUTTON is present (Logic: We want it to be MISSING)
                button_found = False
                if os.path.exists(btn_filename):
                    with mss.mss() as sct:
                        img = np.array(sct.grab(roi))
                        template = cv2.imread(btn_filename)
                        res = cv2.matchTemplate(cv2.cvtColor(img, cv2.COLOR_BGRA2BGR), template, cv2.TM_CCOEFF_NORMED)
                        _, mv, _, _ = cv2.minMaxLoc(res)
                        if mv > 0.8: button_found = True

                # 3. Decision
                if button_found:
                    self.root.after(0, lambda: self.log("S7 Abort: Button found. Letting Stage 2/6 handle it.", "orange"))
                else:
                    self.root.after(0, lambda: self.log("S7 Action: Button MISSING. Refreshing page...", "red"))
                    pyautogui.press('f5')
                    self.root.after(0, lambda: self.mark_pass(label, key, {'trigger':trigger, 'action':'F5'}))
            else:
                self.root.after(0, lambda: self.log(f"Stage 7 Fail: Text '{trigger}' not found", "red"))
        except Exception as e: self.root.after(0, lambda: self.log(f"CRASH S7: {e}", "red"))

    # --- DYNAMIC WORKERS (INFINITY SCROLL) ---
    def test_image(self, num, filename, label, key):
        if not os.path.exists(filename): self.log(f"Error: {filename} missing", "red"); return
        self.log(f"Stage {num}: Waiting 5s (Infinity Search)...", "red")
        threading.Thread(target=self._worker_image_dynamic, args=(filename, label, key), daemon=True).start()

    def _worker_image_dynamic(self, filename, label, key):
        def check_img():
            template = cv2.imread(filename)
            with mss.mss() as sct:
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                screen = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2BGR)
                res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= 0.8)
                points = list(zip(*loc[::-1]))
                if points:
                    points.sort(key=lambda k: (k[1], k[0]))
                    tx, ty = points[0]
                    h, w = template.shape[:2]
                    return (tx + w//2 + monitor['left'], ty + h//2 + monitor['top'])
            return None

        with mss.mss() as sct:
             mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
             scroll_x = mon['left'] + mon['width']//2
             scroll_y = mon['top'] + mon['height']//2

        result = self._scroll_and_find_infinity(check_img, scroll_x, scroll_y)
        
        if result:
            self.root.after(0, lambda: self.perform_action(result[0], result[1], label, key, filename))
        else:
            self.root.after(0, lambda: self.log(f"Image {filename} not found after infinity search.", "red"))

    def test_stage_4(self, trigger, filename, label):
        roi = self.config.get('stage4_roi')
        if not roi: self.log("Error: Lobby ROI not set!", "red"); return
        self.log(f"Stage 4: Waiting 5s (Infinity Search)...", "red")
        threading.Thread(target=self._worker_stage_4_dynamic, args=(trigger, label, roi), daemon=True).start()

    def _worker_stage_4_dynamic(self, trigger, label, roi):
        def check_text():
            coords = self._get_text_coords(roi, trigger)
            if coords:
                tx, ty, tw, th = coords
                return (tx + tw//2, ty - 30)
            return None
        
        cx = roi['left'] + roi['width'] // 2
        cy = roi['top'] + roi['height'] // 2
        
        result = self._scroll_and_find_infinity(check_text, cx, cy)
        
        if result:
            self.root.after(0, lambda: self.perform_action(result[0], result[1], label, "stage4_data", {'trigger':trigger}))
        else:
            self.root.after(0, lambda: self.log(f"Stage 4 Fail: '{trigger}' not found after infinity search.", "red"))

    # --- CORE LOGIC ---
    def _scroll_and_find_infinity(self, check_func, mouse_x, mouse_y):
        MAX_ATTEMPTS = 50 
        SCROLL_AMOUNT = -500 
        direction = 1 
        pyautogui.moveTo(mouse_x, mouse_y)
        for i in range(MAX_ATTEMPTS):
            res = check_func()
            if res: return res
            self.root.after(0, lambda idx=i: self.log(f"Searching... (Scan {idx+1}/{MAX_ATTEMPTS})", "blue"))
            if i > 0 and i % 10 == 0:
                direction *= -1
                SCROLL_AMOUNT = 500 if direction == -1 else -500
                self.root.after(0, lambda: self.log(f"Reversing Scroll Direction...", "orange"))
            pyautogui.moveTo(mouse_x, mouse_y)
            pyautogui.scroll(SCROLL_AMOUNT)
            time.sleep(1.2)
        return None

    def _check_text_in_roi(self, roi, trigger):
        with mss.mss() as sct:
            img = np.array(sct.grab(roi))
            gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY), None, fx=2, fy=2)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 40 and trigger.lower() in data['text'][i].lower(): return True
        return False

    def _get_text_coords(self, roi, trigger):
        with mss.mss() as sct:
            img = np.array(sct.grab(roi))
            gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY), None, fx=2, fy=2)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
            t_parts = trigger.lower().split()
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 40:
                    txt = data['text'][i].lower()
                    if any(p in txt for p in t_parts):
                        return (roi['left'] + data['left'][i]//2, roi['top'] + data['top'][i]//2, data['width'][i]//2, data['height'][i]//2)
        return None

    def _find_click_img_static(self, roi, filename, label, key, trigger):
        if not os.path.exists(filename): return
        with mss.mss() as sct:
            img = np.array(sct.grab(roi))
            template = cv2.imread(filename)
            res = cv2.matchTemplate(cv2.cvtColor(img, cv2.COLOR_BGRA2BGR), template, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv > 0.8:
                h, w = template.shape[:2]
                self.root.after(0, lambda: self.perform_action(roi['left']+ml[0]+w//2, roi['top']+ml[1]+h//2, label, key, trigger))
            else: self.root.after(0, lambda: self.log(f"Img match fail: {mv:.2f}", "red"))

if __name__ == "__main__":
    root = tk.Tk()
    app = FieldTestRecorderV20(root)
    root.mainloop()