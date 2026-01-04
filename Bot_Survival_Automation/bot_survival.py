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

class SurvivalControlCenterV33:
    def __init__(self, root):
        self.root = root
        self.root.title("Survival V33: Auto-Hide Fix")
        self.root.geometry("950x950") 
        self.root.attributes('-topmost', True)
        
        self.watching = False
        self.watch_thread = None

        self.config = {
            'anchor_roi': None,
            'anchor_data': None,
            'central_roi': None,
            'stage1_data': None, 
            'stage2_data': None,
            'stage3_img': None,
            'stage4_roi': None,
            'stage4_data': None,
            'stage5_img': None
        }
        
        # --- HEADER ---
        f_head = tk.Frame(root, pady=10, bg="#263238")
        f_head.pack(fill="x")
        tk.Label(f_head, text="SURVIVAL V33: CONSCIOUSNESS", font=("Arial", 14, "bold"), fg="white", bg="#263238").pack()
        
        # CONTROLS
        self.btn_start = tk.Button(f_head, text="START WATCHER", bg="#00e676", font=("Arial", 12, "bold"), width=20, command=self.start_watcher)
        self.btn_start.pack(side="left", padx=20, pady=5)
        self.btn_stop = tk.Button(f_head, text="STOP WATCHER", bg="#ff5252", font=("Arial", 12, "bold"), width=20, state="disabled", command=self.stop_watcher)
        self.btn_stop.pack(side="right", padx=20, pady=5)

        self.lbl_status = tk.Label(root, text="STATUS: IDLE", font=("Arial", 12, "bold"), fg="grey")
        self.lbl_status.pack(pady=5)
        
        self.frame_steps = tk.Frame(root, padx=10, pady=10)
        self.frame_steps.pack(fill="both", expand=True)
        self.labels = {}

        self.lbl_log = tk.Label(root, text="Log: System Ready.", fg="blue", font=("Courier", 10), wraplength=900, justify="left", bg="#eceff1", relief="sunken")
        self.lbl_log.pack(side="bottom", fill="x", pady=10)

        if not os.path.exists(TESSERACT_PATH):
            self.log(f"CRITICAL: Tesseract missing at {TESSERACT_PATH}", "red")

        # --- SECTION 0: CONSCIOUSNESS (ANCHOR) ---
        tk.Label(self.frame_steps, text="--- SECTION 0: GAME ANCHOR (Balance & Total Bet) ---", fg="purple", font=("Arial", 10, "bold")).pack(anchor="w", pady=5)
        
        f_anchor = tk.Frame(self.frame_steps); f_anchor.pack(fill="x")
        tk.Button(f_anchor, text="SET ANCHOR ROI", bg="#e1bee7", width=15, command=self.set_anchor_roi).pack(side="left")
        self.lbl_anchor_roi = tk.Label(f_anchor, text="[ROI PENDING]", fg="red"); self.lbl_anchor_roi.pack(side="left", padx=5)
        
        f_at = tk.Frame(self.frame_steps, pady=2); f_at.pack(fill="x")
        tk.Label(f_at, text="Anchor Text:", width=15, anchor="w").pack(side="left")
        self.entry_anchor = tk.Entry(f_at, width=20); self.entry_anchor.insert(0, "Balance Total Bet"); self.entry_anchor.pack(side="left", padx=2)
        tk.Button(f_at, text="TEST ANCHOR", bg="#e1bee7", width=15, font=("Arial", 9, "bold"), command=self.test_anchor).pack(side="left", padx=10)

        # --- SECTION 1: MONITOR ---
        tk.Label(self.frame_steps, text="--- PART 1: MONITOR (Shared ROI) ---", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w", pady=5)
        f_roi = tk.Frame(self.frame_steps); f_roi.pack(fill="x")
        tk.Button(f_roi, text="SET CENTRAL ROI", bg="#ffe0b2", width=15, command=self.set_central_roi).pack(side="left")
        self.lbl_roi_stat = tk.Label(f_roi, text="[ROI PENDING]", fg="red"); self.lbl_roi_stat.pack(side="left", padx=5)

        self.create_text_action_stage(1, "Inactivity Pause", "Inactivity", "stage1_data")
        self.create_hybrid_stage_shared(2, "Session Crash", "Session", "btn_crash_ok.png", "stage2_data")
        
        # --- SECTION 2: RECOVERY ---
        tk.Label(self.frame_steps, text="--- PART 2: RECOVERY (Priority Loop) ---", fg="blue", font=("Arial", 10, "bold")).pack(anchor="w", pady=(15,5))
        
        self.create_image_stage(3, "Priority 4: Provider", "pragmatic_logo.png", "stage3_img")
        
        f_lroi = tk.Frame(self.frame_steps); f_lroi.pack(fill="x", pady=5)
        tk.Button(f_lroi, text="SET LOBBY ROI", bg="#ffe0b2", width=15, command=self.set_lobby_roi).pack(side="left")
        self.lbl_lobby_roi = tk.Label(f_lroi, text="[ROI PENDING]", fg="red"); self.lbl_lobby_roi.pack(side="left", padx=5)

        self.create_lobby_text_click_stage(4, "Priority 3: Table", "Stake Roulette", "target_table_name.png", "stage4_data")
        self.create_image_stage(5, "Priority 2: Full Screen", "btn_fullscreen.png", "stage5_img")
        
        self.load_config()

    # --- STATE MACHINE ---
    def start_watcher(self):
        if not self.config.get('anchor_roi'):
            messagebox.showerror("Error", "Game Anchor ROI is missing! I cannot have consciousness without it.")
            return
        if not self.config.get('central_roi'):
            messagebox.showerror("Error", "Central ROI is missing!")
            return
        
        self.watching = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="STATUS: PART 1 (MONITORING)", fg="green")
        self.log("Watcher Started. Consciousness Active.", "green")
        
        self.watch_thread = threading.Thread(target=self._state_machine_loop, daemon=True)
        self.watch_thread.start()

    def stop_watcher(self):
        self.watching = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(text="STATUS: STOPPING...", fg="orange")
        self.log("Stop Requested...", "orange")

    def _state_machine_loop(self):
        current_state = "PART_1"
        anchor_text = self.entry_anchor.get()
        
        while self.watching:
            try:
                # ===========================
                # PART 1: CONSCIOUS MONITOR
                # ===========================
                if current_state == "PART_1":
                    self.root.after(0, lambda: self.lbl_status.config(text="STATUS: PART 1 (MONITORING)", fg="green"))
                    
                    # 1. Ambiguous OK Button Check
                    if self._check_crash_ok_button_any():
                        self.log("PART 1: Detected OK Button. Clicking...", "orange")
                        cx, cy = self._get_center(self.config['central_roi'])
                        self.perform_action(cx, cy)
                        
                        # CONSCIOUS CHECK
                        self.log("Verifying Consciousness (2s wait)...", "purple")
                        time.sleep(2.0)
                        
                        if self._is_in_game(anchor_text):
                            self.log("Consciousness: Anchor Found. Still in Game. Resuming.", "green")
                            continue
                        else:
                            self.log("Consciousness: Anchor GONE. Crashed. -> PART 2.", "red")
                            current_state = "PART_2"
                            continue

                    # 2. Inactivity Text
                    if self.run_stage_1_logic(is_test=False):
                        self.log("PART 1: Inactivity Text Found. Clicked.", "blue")
                        time.sleep(1.0)
                        continue

                    # 3. Session Text (Backup)
                    if self.run_stage_2_logic(is_test=False):
                        self.log("PART 1: Session Text Found. -> PART 2", "red")
                        current_state = "PART_2"
                        time.sleep(1.0)
                        continue
                    
                    time.sleep(0.5)

                # ===========================
                # PART 2: PRIORITY LOOP
                # ===========================
                elif current_state == "PART_2":
                    self.root.after(0, lambda: self.lbl_status.config(text="STATUS: PART 2 (PRIORITY LOOP)", fg="orange"))
                    
                    # P1: BACK IN GAME?
                    if self._is_in_game(anchor_text):
                        self.log("PART 2: Game Anchor Found! RECOVERY COMPLETE.", "green")
                        current_state = "PART_1"
                        time.sleep(2.0)
                        continue

                    # P2: FULL SCREEN
                    if self.run_stage_5_logic(is_test=False):
                        self.log("PART 2: Clicked Full Screen. Looping...", "blue")
                        time.sleep(2.0)
                        continue

                    # P3: TABLE
                    if self.run_stage_4_logic_priority(is_test=False):
                        self.log("PART 2: Clicked Table. Looping...", "blue")
                        time.sleep(2.0)
                        continue

                    # P4: PROVIDER
                    if self.run_stage_3_logic_priority(is_test=False):
                        self.log("PART 2: Clicked Provider. Looping...", "blue")
                        time.sleep(2.0)
                        continue

                    # P5: SCROLL
                    self.log("PART 2: Nothing found. Scrolling...", "grey")
                    self._perform_blind_scroll()
                    time.sleep(1.0)

            except Exception as e:
                self.log(f"CRITICAL ERROR: {e}", "red")
                time.sleep(5) 
        
        self.root.after(0, lambda: self.lbl_status.config(text="STATUS: IDLE", fg="grey"))
        self.log("Watcher Stopped.", "blue")

    # --- CORE HELPERS ---
    def _is_in_game(self, text_trigger):
        roi = self.config.get('anchor_roi')
        if not roi: return False
        return self._check_text_in_roi(roi, text_trigger)

    def _check_crash_ok_button_any(self):
        roi = self.config.get('central_roi')
        return self._find_click_img_static(roi, "btn_crash_ok.png", click=False) 

    def _perform_blind_scroll(self):
        roi = self.config.get('stage4_roi')
        if not roi: return
        cx, cy = self._get_center(roi)
        pyautogui.moveTo(cx, cy)
        pyautogui.scroll(-500)

    # --- PRIORITY LOGIC ---
    def run_stage_3_logic_priority(self, is_test=True):
        return self._find_and_click_screen("pragmatic_logo.png")

    def run_stage_4_logic_priority(self, is_test=True):
        roi = self.config.get('stage4_roi')
        trigger = self.entries[4].get()
        coords = self._get_text_coords(roi, trigger)
        if coords:
            self.perform_action(coords[0] + coords[2]//2, coords[1] - 30)
            return True
        return False

    def _find_and_click_screen(self, filename):
        if not os.path.exists(filename): return False
        template = cv2.imread(filename)
        with mss.mss() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            screen = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2BGR)
            res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv > 0.8:
                h, w = template.shape[:2]
                self.perform_action(ml[0]+w//2 + monitor['left'], ml[1]+h//2 + monitor['top'])
                return True
        return False

    # --- LEGACY LOGIC ---
    def run_stage_1_logic(self, is_test=True):
        roi = self.config.get('central_roi')
        trigger = self.entries[1].get() 
        if self._check_text_in_roi(roi, trigger):
            cx, cy = self._get_center(roi)
            self.perform_action(cx, cy)
            if is_test: self.mark_pass(1, "stage1_data", {'trigger': trigger})
            return True
        return False

    def run_stage_2_logic(self, is_test=True):
        roi = self.config.get('central_roi')
        trigger = self.entries[2].get()
        if self._check_text_in_roi(roi, trigger):
            if self._find_click_img_static(roi, "btn_crash_ok.png"):
                if is_test: self.mark_pass(2, "stage2_data", {'trigger': trigger})
                return True
        return False

    def run_stage_5_logic(self, is_test=True):
        return self._find_and_click_screen("btn_fullscreen.png")

    # --- TEXT UTILS ---
    def _check_text_in_roi(self, roi, trigger):
        if not roi: return False
        with mss.mss() as sct:
            img = np.array(sct.grab(roi))
            gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY), None, fx=2, fy=2)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
            keywords = trigger.lower().split()
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 50:
                    txt = data['text'][i].lower()
                    if any(k in txt for k in keywords):
                        return True
        return False

    def _get_text_coords(self, roi, trigger):
        if not roi: return None
        with mss.mss() as sct:
            img = np.array(sct.grab(roi))
            gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY), None, fx=2, fy=2)
            _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            data = pytesseract.image_to_data(binary, output_type=pytesseract.Output.DICT)
            keywords = trigger.lower().split()
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 50:
                    txt = data['text'][i].lower()
                    if any(k in txt for k in keywords):
                        return (roi['left'] + data['left'][i]//2, roi['top'] + data['top'][i]//2, data['width'][i]//2, data['height'][i]//2)
        return None

    def _find_click_img_static(self, roi, filename, click=True):
        if not os.path.exists(filename): return False
        with mss.mss() as sct:
            img = np.array(sct.grab(roi))
            template = cv2.imread(filename)
            res = cv2.matchTemplate(cv2.cvtColor(img, cv2.COLOR_BGRA2BGR), template, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv > 0.8:
                if click:
                    h, w = template.shape[:2]
                    self.perform_action(roi['left']+ml[0]+w//2, roi['top']+ml[1]+h//2)
                return True
        return False

    def _get_center(self, roi):
        return (roi['left'] + roi['width']//2, roi['top'] + roi['height']//2)

    def perform_action(self, x, y):
        self.log(f"CLICK: {x}, {y}", "orange")
        pyautogui.click(x, y)

    # --- UI HELPERS ---
    def create_text_action_stage(self, num, label, def_val, key): self._row(num, label, def_val, None)
    def create_hybrid_stage_shared(self, num, label, def_val, fname, key): self._row(num, label, def_val, fname)
    def create_image_stage(self, num, label, fname, key): self._row(num, label, None, fname)
    def create_lobby_text_click_stage(self, num, label, def_val, fname, key): self._row(num, label, def_val, fname)
    def _row(self, num, label, def_val, fname):
        f = tk.Frame(self.frame_steps, pady=2); f.pack(fill="x")
        tk.Label(f, text=f"S{num}: {label}", width=25, anchor="w", font=("Arial", 9, "bold")).pack(side="left")
        if not hasattr(self, 'entries'): self.entries = {}
        if def_val is not None:
            e = tk.Entry(f, width=12); e.insert(0, def_val); e.pack(side="left", padx=2)
            self.entries[num] = e
        if fname:
            tk.Button(f, text="SNIP", bg="#fff9c4", width=6, command=lambda: self.snip(fname)).pack(side="left", padx=2)
        lbl = tk.Label(f, text="[PENDING]", fg="gray", width=10); lbl.pack(side="right")
        self.labels[num] = lbl
        tk.Button(f, text="TEST", bg="#e1f5fe", width=6, command=lambda: self.test_stage(num)).pack(side="right")

    # --- ANCHOR TEST (AUTO HIDE) ---
    def test_anchor(self):
        # 1. Hide GUI
        self.root.withdraw()
        time.sleep(1.0) # Wait for fade
        
        # 2. Check
        text = self.entry_anchor.get()
        result = self._is_in_game(text)
        
        # 3. Show GUI
        self.root.deiconify()
        
        if result:
            messagebox.showinfo("Success", f"Anchor Found! I see '{text}'.")
            self.log("Anchor Found. Bot is Conscious.", "green")
        else:
            messagebox.showerror("Fail", f"Anchor NOT found. Check ROI or Text.")
            self.log("Anchor Fail.", "red")

    def test_stage(self, stage_num):
        self.log(f"Testing Stage {stage_num} logic...", "blue")
        if stage_num == 1: self.run_stage_1_logic()
        elif stage_num == 2: self.run_stage_2_logic()
        elif stage_num == 3: self.run_stage_3_logic_priority()
        elif stage_num == 4: self.run_stage_4_logic_priority()
        elif stage_num == 5: self.run_stage_5_logic()

    # --- CONFIG ---
    def load_config(self):
        if os.path.exists('survival_config.json'):
            try:
                with open('survival_config.json', 'r') as f:
                    data = json.load(f)
                    for k, v in data.items(): self.config[k] = v
                if self.config.get('anchor_roi'): self.lbl_anchor_roi.config(text="[ROI SET]", fg="green")
                if self.config.get('central_roi'): self.lbl_roi_stat.config(text="[ROI SET]", fg="green")
                if self.config.get('stage4_roi'): self.lbl_lobby_roi.config(text="[ROI SET]", fg="green")
                if self.config.get('anchor_data'): self.entry_anchor.delete(0,tk.END); self.entry_anchor.insert(0, self.config['anchor_data'])
                if self.config.get('stage1_data'): self.entries[1].delete(0,tk.END); self.entries[1].insert(0, self.config['stage1_data'].get('trigger', 'Inactivity'))
                if self.config.get('stage2_data'): self.entries[2].delete(0,tk.END); self.entries[2].insert(0, self.config['stage2_data'].get('trigger', 'Session'))
                if self.config.get('stage4_data'): self.entries[4].delete(0,tk.END); self.entries[4].insert(0, self.config['stage4_data'].get('trigger', 'Stake Roulette'))
                self.log("Config Loaded.", "green")
            except: pass
    def save_config(self):
        self.config['anchor_data'] = self.entry_anchor.get()
        with open('survival_config.json', 'w') as f: json.dump(self.config, f, indent=4)
    def mark_pass(self, num, key, val):
        self.labels[num].config(text="[PASSED]", fg="green"); self.config[key] = val; self.save_config()
    def snip(self, filename):
        self.root.withdraw(); time.sleep(0.5); selector = BoxSelector(self.root); self.root.deiconify()
        if selector.selection:
            with mss.mss() as sct:
                img = np.array(sct.grab(selector.selection)); cv2.imwrite(filename, cv2.cvtColor(img, cv2.COLOR_BGRA2BGR))
            self.log(f"Snipped {filename}", "green")
    def set_central_roi(self): self._set_roi('central_roi', self.lbl_roi_stat)
    def set_lobby_roi(self): self._set_roi('stage4_roi', self.lbl_lobby_roi)
    def set_anchor_roi(self): self._set_roi('anchor_roi', self.lbl_anchor_roi)
    def _set_roi(self, key, lbl):
        self.root.withdraw(); time.sleep(0.5); sel = BoxSelector(self.root); self.root.deiconify()
        if sel.selection:
            self.config[key] = sel.selection; lbl.config(text="[ROI SET]", fg="green"); self.save_config()
    def log(self, text, color="blue"):
        print(f"LOG: {text}"); self.lbl_log.config(text=f"Log: {text}", fg=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = SurvivalControlCenterV33(root)
    root.mainloop()