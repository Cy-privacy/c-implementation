import ctypes
import cv2
import json
import math
import mss
import os
import sys
import time
import torch
import numpy as np
import win32api
from termcolor import colored
from ultralytics import YOLO
from PyQt6.QtCore import QObject, pyqtSignal

class Aimbot(QObject):
    status_update = pyqtSignal(str)
    
    def __init__(self, box_constant=350, collect_data=False, mouse_delay=0.0009):
        super().__init__()
        self.box_constant = box_constant
        self.collect_data = collect_data
        self.mouse_delay = mouse_delay
        self.screen = mss.mss()
        self.extra = ctypes.c_ulong(0)
        self.ii_ = Input_I()
        self.pixel_increment = 1
        
        # Load sensitivity settings
        with open("lib/config/config.json") as f:
            self.sens_config = json.load(f)
            
        # Initialize model
        self.status_update.emit("Loading neural network model...")
        self.model = YOLO('lib/best.pt')
        
        if torch.cuda.is_available():
            self.status_update.emit("CUDA acceleration enabled")
        else:
            self.status_update.emit("CUDA acceleration unavailable")
            
        self.enabled = True
        self.conf = 0.45
        self.iou = 0.45
        
        # Screen setup
        self.screen_res_x = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_res_y = ctypes.windll.user32.GetSystemMetrics(1)
        self.screen_x = int(self.screen_res_x / 2)
        self.screen_y = int(self.screen_res_y / 2)
        
    def toggle(self):
        self.enabled = not self.enabled
        status = "enabled" if self.enabled else "disabled"
        self.status_update.emit(f"Aimbot {status}")
        
    def left_click(self):
        ctypes.windll.user32.mouse_event(0x0002)
        self.sleep(0.0001)
        ctypes.windll.user32.mouse_event(0x0004)

    def sleep(self, duration, get_now=time.perf_counter):
        if duration == 0: return
        now = get_now()
        end = now + duration
        while now < end:
            now = get_now()

    def is_shooting(self):
        return win32api.GetKeyState(0x01) in (-127, -128)
    
    def is_targeted(self):
        return win32api.GetKeyState(0x02) in (-127, -128)

    def is_target_locked(self, x, y):
        threshold = 5
        return (self.screen_x - threshold <= x <= self.screen_x + threshold and 
                self.screen_y - threshold <= y <= self.screen_y + threshold)

    def move_crosshair(self, x, y):
        if self.is_targeted():
            scale = self.sens_config["targeting_scale"]
        else:
            return

        for rel_x, rel_y in self.interpolate_coordinates_from_center((x, y), scale):
            self.ii_.mi = MouseInput(rel_x, rel_y, 0, 0x0001, 0, ctypes.pointer(self.extra))
            input_obj = Input(ctypes.c_ulong(0), self.ii_)
            ctypes.windll.user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(input_obj))
            self.sleep(self.mouse_delay)

    def interpolate_coordinates_from_center(self, absolute_coordinates, scale):
        diff_x = (absolute_coordinates[0] - self.screen_x) * scale/self.pixel_increment
        diff_y = (absolute_coordinates[1] - self.screen_y) * scale/self.pixel_increment
        length = int(math.dist((0,0), (diff_x, diff_y)))
        if length == 0: return
        unit_x = (diff_x/length) * self.pixel_increment
        unit_y = (diff_y/length) * self.pixel_increment
        x = y = sum_x = sum_y = 0
        for k in range(0, length):
            sum_x += x
            sum_y += y
            x, y = round(unit_x * k - sum_x), round(unit_y * k - sum_y)
            yield x, y

    def start(self):
        self.status_update.emit("Starting screen capture...")
        half_screen_width = self.screen_res_x/2
        half_screen_height = self.screen_res_y/2
        detection_box = {
            'left': int(half_screen_width - self.box_constant//2),
            'top': int(half_screen_height - self.box_constant//2),
            'width': int(self.box_constant),
            'height': int(self.box_constant)
        }

        while True:
            if not self.enabled:
                time.sleep(0.1)
                continue
                
            start_time = time.perf_counter()
            frame = np.array(self.screen.grab(detection_box))
            
            if frame is None or frame.size == 0:
                continue
                
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            boxes = self.model.predict(source=frame, verbose=False, conf=self.conf, iou=self.iou)
            result = boxes[0]
            
            if len(result.boxes.xyxy) != 0:
                least_crosshair_dist = None
                closest_detection = None
                player_in_frame = False
                
                for box in result.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box)
                    height = y2 - y1
                    relative_head_X = int((x1 + x2)/2)
                    relative_head_Y = int((y1 + y2)/2 - height/10)
                    
                    own_player = x1 < 15 or (x1 < self.box_constant/5 and y2 > self.box_constant/1.2)
                    crosshair_dist = math.dist((relative_head_X, relative_head_Y), 
                                             (self.box_constant/2, self.box_constant/2))
                    
                    if least_crosshair_dist is None:
                        least_crosshair_dist = crosshair_dist
                        
                    if crosshair_dist <= least_crosshair_dist and not own_player:
                        least_crosshair_dist = crosshair_dist
                        closest_detection = {
                            "x1": x1, "y1": y1,
                            "relative_head_X": relative_head_X,
                            "relative_head_Y": relative_head_Y
                        }
                        
                    if own_player and not player_in_frame:
                        player_in_frame = True
                        
                if closest_detection:
                    absolute_head_X = closest_detection["relative_head_X"] + detection_box['left']
                    absolute_head_Y = closest_detection["relative_head_Y"] + detection_box['top']
                    
                    if self.is_target_locked(absolute_head_X, absolute_head_Y):
                        if True and not self.is_shooting():  # use_trigger_bot is always True
                            self.left_click()
                            
                    if self.enabled:
                        self.move_crosshair(absolute_head_X, absolute_head_Y)
                        
            cv2.waitKey(1)

# Required class definitions from the original code
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]