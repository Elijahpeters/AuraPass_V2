import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import time
import serial
import random
import sys
import numpy as np
from deepface import DeepFace # --- FACENET UPGRADE IMPORT ---

class AuraPassSystem:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1100x750") 
        self.window.configure(bg="#0f172a")

        # --- LOCAL STUDENT DATABASE ---
        self.student_db = {
            1: {
                "name": "PETERS ELIJAH TEMIDAYO",
                "matric": "EES/19/20/0293",
                "level": "500 Level",
                "faculty": "Eng. & Environmental Studies",
                "dept": "Elect/Elect Eng.",
                "course": "EEG501"
            },
            2: {
                "name": "Jane Doe",
                "matric": "EES/21/22/0480",
                "level": "300 Level",
                "faculty": "Eng. & Environmental Studies",
                "dept": "Computer Eng.",
                "course": "CPE301"
            }
        }

        # --- Hardware Connection (COM1) ---
        self.serial_connected = False
        try:
            self.arduino = serial.Serial('COM1', 9600, timeout=1)
            time.sleep(2) 
            self.serial_connected = True
            print("[SUCCESS] Hardware Cable Connected")
        except:
            print("[WARNING] Hardware not connected.")

        # --- SEAT ALLOCATION & CONSTRAINT TRACKING ---
        self.available_seats = list(range(1, 51))
        self.assigned_users = {} # Maps user_id to Seat Number
        self.seat_map = {}       # Maps Seat Number to Course Code (to prevent cheating)

        # --- AI Brain Setup (FACENET VIA DEEPFACE) ---
        self.db_path = "Database"
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            messagebox.showwarning("Database Missing", "Created 'Database' folder. Please add authorized images (e.g., '1.jpg') before scanning.")
            
        # We still use Haar Cascade just to draw the box and crop the face quickly
        self.cascadePath = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.faceCascade = cv2.CascadeClassifier(self.cascadePath)
        
        # States
        self.system_state = "IDLE" 
        self.state_timer = 0
        self.current_user_id = -1
        self.gate_open = False
        self.frozen_frame = None
        self.frozen_gray_face = None
        self.frozen_box = (0,0,0,0)
        
        # --- UI LAYOUT ---
        self.header = tk.Label(window, text="OOU BIOMETRIC EXAM ALLOCATION TERMINAL", 
                              font=("Consolas", 24, "bold"), fg="#38bdf8", bg="#0f172a", pady=15)
        self.header.pack()

        self.main_container = tk.Frame(window, bg="#0f172a")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20)

        self.left_frame = tk.Frame(self.main_container, bg="#0f172a")
        self.left_frame.pack(side=tk.LEFT, padx=10)
        self.video_label = tk.Label(self.left_frame, bg="#1e293b", bd=2, relief="solid")
        self.video_label.pack()

        self.right_frame = tk.Frame(self.main_container, bg="#1e293b", bd=2, relief="ridge", width=400, height=480)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        self.right_frame.pack_propagate(False)

        tk.Label(self.right_frame, text="STUDENT DATABASE RECORD", font=("Consolas", 16, "underline"), fg="#94a3b8", bg="#1e293b", pady=10).pack()
        
        self.lbl_name = self.create_db_label("NAME: --")
        self.lbl_matric = self.create_db_label("MATRIC: --")
        self.lbl_level = self.create_db_label("LEVEL: --")
        self.lbl_dept = self.create_db_label("DEPT: --")
        self.lbl_course = self.create_db_label("COURSE: --") 
        
        self.lbl_seat_display = tk.Label(self.right_frame, text="SEAT: --", font=("Consolas", 36, "bold"), fg="#38bdf8", bg="#1e293b", pady=20)
        self.lbl_seat_display.pack()

        self.status_frame = tk.Frame(window, bg="#0f172a", pady=15)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_indicator = tk.Label(self.status_frame, text="SYSTEM LOCKED", font=("Consolas", 28, "bold"), fg="#94a3b8", bg="#0f172a")
        self.status_indicator.pack()

        self.vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.current_imgtk = None 
        
        self.update_video()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def create_db_label(self, text):
        lbl = tk.Label(self.right_frame, text=text, font=("Consolas", 14), fg="#cbd5e1", bg="#1e293b", anchor="w", justify=tk.LEFT, padx=20, pady=5)
        lbl.pack(fill=tk.X)
        return lbl

    def reset_db_labels(self):
        self.lbl_name.config(text="NAME: --", fg="#cbd5e1")
        self.lbl_matric.config(text="MATRIC: --", fg="#cbd5e1")
        self.lbl_level.config(text="LEVEL: --", fg="#cbd5e1")
        self.lbl_dept.config(text="DEPT: --", fg="#cbd5e1")
        self.lbl_course.config(text="COURSE: --", fg="#cbd5e1")
        self.lbl_seat_display.config(text="SEAT: --", fg="#38bdf8")

    def lock_hardware_gate(self):
        if self.gate_open and self.serial_connected:
            self.arduino.write(b'C\n')
            self.gate_open = False

    def draw_techy_scan_effects(self, img, x, y, w, h, progress_ratio):
        color = (255, 255, 0) 
        l = 30; t = 3 
        cv2.line(img, (x, y), (x + l, y), color, t); cv2.line(img, (x, y), (x, y + l), color, t)
        cv2.line(img, (x + w, y), (x + w - l, y), color, t); cv2.line(img, (x + w, y), (x + w, y + l), color, t)
        cv2.line(img, (x, y + h), (x + l, y + h), color, t); cv2.line(img, (x, y + h), (x, y + h - l), color, t)
        cv2.line(img, (x + w, y + h), (x + w - l, y + h), color, t); cv2.line(img, (x + w, y + h), (x + w, y + h - l), color, t)

        step = 25
        for i in range(x + step, x + w, step):
            cv2.line(img, (i, y), (i, y + h), (200, 200, 0), 1)
        for j in range(y + step, y + h, step):
            cv2.line(img, (x, j), (x + w, j), (200, 200, 0), 1) 

        laser_y = y + int(h * progress_ratio)
        if laser_y > y + h: laser_y = y + h
        cv2.line(img, (x, laser_y), (x + w, laser_y), (0, 255, 255), 3) 
        
        cv2.putText(img, f"MAPPING FACIAL GEOMETRY... {int(progress_ratio*100)}%", (x, y - 10), cv2.FONT_HERSHEY_PLAIN, 1.2, color, 2)
        cv2.putText(img, "QUERYING DEEPFACE...", (x, y + h + 20), cv2.FONT_HERSHEY_PLAIN, 1.0, color, 1)

    def apply_night_vision(self, gray_frame):
        mean_brightness = np.mean(gray_frame)
        if mean_brightness < 90: 
            gamma = 1.5
            invGamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            brightened = cv2.LUT(gray_frame, table)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            night_vision_frame = clahe.apply(brightened)
            return night_vision_frame, True 
        return gray_frame, False

    def update_video(self):
        night_vision_active = False

        if self.system_state in ["IDLE", "ALIGNING"]:
            ret, live_frame = self.vid.read()
            if ret:
                live_frame = cv2.flip(live_frame, 1)
                display_frame = live_frame.copy()
                raw_gray = cv2.cvtColor(live_frame, cv2.COLOR_BGR2GRAY)
                gray, night_vision_active = self.apply_night_vision(raw_gray)
            else:
                self.window.after(10, self.update_video)
                return
        else:
            display_frame = self.frozen_frame.copy()

        if night_vision_active and self.system_state in ["IDLE", "ALIGNING"]:
            cv2.putText(display_frame, "NIGHT VISION ACTIVE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # --- STATE: IDLE ---
        if self.system_state == "IDLE":
            self.status_indicator.config(text="SYSTEM LOCKED - AWAITING STUDENT", fg="#94a3b8")
            self.video_label.config(highlightbackground="#1e293b")
            self.reset_db_labels()
            
            faces = self.faceCascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(120, 120))
            if len(faces) > 0:
                self.system_state = "ALIGNING"
                self.state_timer = time.time()

        # --- STATE: ALIGNING ---
        elif self.system_state == "ALIGNING":
            faces = self.faceCascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(120, 120))
            if len(faces) > 0:
                faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
                x, y, w, h = faces[0]
                
                self.status_indicator.config(text="FACE DETECTED - HOLD STILL", fg="#eab308")
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 215, 255), 2)
                
                if time.time() - self.state_timer > 1.2:
                    self.system_state = "PROCESSING"
                    self.state_timer = time.time()
                    self.frozen_frame = live_frame.copy()
                    self.frozen_box = (x, y, w, h)
                    
                    # Save the frozen frame temporarily for FaceNet to analyze
                    cv2.imwrite("temp_scan.jpg", self.frozen_frame)
            else:
                self.system_state = "IDLE"

        # --- STATE: PROCESSING (FACENET INTEGRATION) ---
        elif self.system_state == "PROCESSING":
            bx, by, bw, bh = self.frozen_box
            self.status_indicator.config(text="EXTRACTING 128-BYTE EMBEDDING...", fg="#38bdf8")
            
            elapsed = time.time() - self.state_timer
            progress_ratio = min(elapsed / 2.0, 1.0)
            
            self.draw_techy_scan_effects(display_frame, bx, by, bw, bh, progress_ratio)
            
            # Update UI immediately so it doesn't freeze before scanning
            cv2image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            self.current_imgtk = ImageTk.PhotoImage(image=img, master=self.window) 
            self.video_label.configure(image=self.current_imgtk)
            self.window.update_idletasks()
            self.window.update()

            if elapsed > 2.0:
                print("\n[AI DEBUG] Sending image to FaceNet Deep Learning Engine...")
                try:
                    # Execute FaceNet Cosine Similarity Match
                    dfs = DeepFace.find(img_path="temp_scan.jpg", 
                                        db_path=self.db_path, 
                                        model_name="Facenet", 
                                        distance_metric="cosine", 
                                        enforce_detection=False, 
                                        silent=True)
                    
                    # Check if FaceNet found any matches
                    if len(dfs) > 0 and not dfs[0].empty:
                        # Extract the matched filename (e.g., '1.jpg')
                        matched_path = dfs[0]['identity'][0]
                        filename = os.path.basename(matched_path)
                        matched_id = int(filename.split('.')[0])
                        distance_score = dfs[0]['distance'][0]
                        
                        print(f"[AI DEBUG] Match Found! Filename: {filename} | Cosine Distance: {distance_score:.4f}")
                        
                        # Verify the extracted ID exists in your student dictionary
                        if matched_id in self.student_db: 
                            self.system_state = "GRANTED"
                            self.current_user_id = matched_id
                        else:
                            self.system_state = "DENIED"
                    else:
                        print("[AI DEBUG] FaceNet rejected the scan. No match found.")
                        self.system_state = "DENIED"
                        
                except Exception as e:
                    print(f"[ERROR] FaceNet execution failed: {e}")
                    self.system_state = "DENIED"
                
                self.state_timer = time.time() 
                self.hardware_triggered_v = False 
                self.hardware_triggered_o = False 

        # --- STATE: GRANTED (Seat & Hardware Execution) ---
        elif self.system_state == "GRANTED":
            bx, by, bw, bh = self.frozen_box
            cv2.rectangle(display_frame, (bx, by), (bx+bw, by+bh), (166, 227, 161), 4)
            cv2.putText(display_frame, "MATCH FOUND", (bx, by - 10), cv2.FONT_HERSHEY_DUPLEX, 1.0, (166, 227, 161), 2)
            
            elapsed_granted = time.time() - self.state_timer
            student = self.student_db[self.current_user_id]
            current_course = student["course"]
            
            # --- PHASE 1: Verification Display (0 to 2 seconds) ---
            if not getattr(self, 'hardware_triggered_v', False):
                self.hardware_triggered_v = True
                self.hardware_triggered_o = False # Reset phase 2 trigger
                
                self.lbl_name.config(text=f"NAME: {student['name']}", fg="#a6e3a1")
                self.lbl_matric.config(text=f"MATRIC: {student['matric']}", fg="#a6e3a1")
                self.lbl_level.config(text=f"LEVEL: {student['level']}", fg="#a6e3a1")
                self.lbl_dept.config(text=f"DEPT: {student['dept']}", fg="#a6e3a1")
                self.lbl_course.config(text=f"COURSE: {current_course}", fg="#a6e3a1")
                
                # --- CONSTRAINT SATISFACTION ALGORITHM ---
                if self.current_user_id not in self.assigned_users:
                    valid_seats = []
                    for s in self.available_seats:
                        left_seat_course = self.seat_map.get(s - 1)
                        right_seat_course = self.seat_map.get(s + 1)
                        if left_seat_course != current_course and right_seat_course != current_course:
                            valid_seats.append(s)
                    
                    if valid_seats:
                        chosen_seat = random.choice(valid_seats)
                    elif len(self.available_seats) > 0:
                        chosen_seat = random.choice(self.available_seats) 
                    else:
                        chosen_seat = "FULL"

                    if chosen_seat != "FULL":
                        self.available_seats.remove(chosen_seat)
                        self.assigned_users[self.current_user_id] = chosen_seat
                        self.seat_map[chosen_seat] = current_course 
                    else:
                        self.assigned_users[self.current_user_id] = "FULL"
                
                seat = self.assigned_users[self.current_user_id]

                if seat == "FULL":
                    self.status_indicator.config(text="HALL CAPACITY REACHED", fg="#f43f5e")
                    self.lbl_seat_display.config(text="SEAT: FULL", fg="#f43f5e")
                    if not self.gate_open and self.serial_connected:
                        self.arduino.write(b'F\n')
                        self.gate_open = True
                else:
                    self.status_indicator.config(text="VERIFYING DETAILS...", fg="#eab308")
                    self.lbl_seat_display.config(text=f"SEAT: {seat}", fg="#a6e3a1")
                    
                    if self.serial_connected:
                        command = f"V,{student['matric']},{current_course}\n"
                        self.arduino.write(command.encode())
                        print(f">> Hardware (Phase 1): {command.strip()}")

            # --- PHASE 2: Open Gate & Show Seat (After 2 seconds) ---
            if elapsed_granted > 2.0 and not getattr(self, 'hardware_triggered_o', False):
                self.hardware_triggered_o = True
                seat = self.assigned_users[self.current_user_id]
                
                if seat != "FULL":
                    self.status_indicator.config(text="ACCESS GRANTED", fg="#a6e3a1")
                    if not self.gate_open and self.serial_connected:
                        command = f"O,{seat}\n"
                        self.arduino.write(command.encode())
                        print(f">> Hardware (Phase 2): {command.strip()}")
                        self.gate_open = True

            # --- PHASE 3: Close & Reset (After 7 seconds) ---
            if elapsed_granted > 7.0:
                self.system_state = "IDLE"
                self.hardware_triggered_v = False 
                self.hardware_triggered_o = False
                self.lock_hardware_gate()

        # --- STATE: DENIED ---
        elif self.system_state == "DENIED":
            bx, by, bw, bh = self.frozen_box
            cv2.rectangle(display_frame, (bx, by), (bx+bw, by+bh), (0, 0, 255), 4)
            cv2.putText(display_frame, "RECORD NOT FOUND", (bx, by - 10), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 255), 2)
            
            self.status_indicator.config(text="ACCESS DENIED - UNKNOWN", fg="#f43f5e")
            self.lbl_name.config(text="NAME: UNKNOWN", fg="#f43f5e")
            self.lbl_course.config(text="COURSE: --", fg="#f43f5e")
            self.lbl_seat_display.config(text="SEAT: N/A", fg="#f43f5e")
            
            if time.time() - self.state_timer > 3.0:
                self.system_state = "IDLE"

        # Update final frame to UI
        if self.system_state != "PROCESSING": # Processing updates inside its own block to prevent stutter
            cv2image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2image)
            self.current_imgtk = ImageTk.PhotoImage(image=img, master=self.window) 
            self.video_label.configure(image=self.current_imgtk)
        
        self.window.after(10, self.update_video)

    def on_closing(self):
        if self.serial_connected:
            self.arduino.close()
        self.vid.release()
        
        # Clean up the temporary scan file
        if os.path.exists("temp_scan.jpg"):
            os.remove("temp_scan.jpg")
            
        self.window.destroy()

if __name__ == "__main__":
    AuraPassSystem(tk.Tk(), "AuraPass Terminal")