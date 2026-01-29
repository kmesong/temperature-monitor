"""Headless Temperature Monitor - No GUI version"""

import cv2
import numpy as np
import pytesseract
import re
import time
import json
import os
from datetime import datetime
from threading import Thread
import winsound

class TemperatureMonitorHeadless:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.load_config()
        self.cap = None
        self.running = False
        self.last_temp = None
        self.alert_triggered = False
        self.frame_count = 0
        
    def load_config(self):
        default_config = {
            "camera_index": 0,
            "temperature_threshold": 50.0,
            "threshold_direction": "above",
            "alert_cooldown_seconds": 60,
            "roi": {
                "x": 200,
                "y": 150,
                "width": 150,
                "height": 80
            },
            "ocr_config": "--psm 7 -c tessedit_char_whitelist=0123456789.-°CF",
            "log_file": "temperature_log.txt",
            "capture_interval": 1,
            "log_interval": 10
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
            
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    @staticmethod
    def list_available_cameras(max_cameras=10):
        available_cameras = []
        print("\n🔍 Scanning for available cameras...")
        print("-" * 50)
        
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    available_cameras.append({
                        'index': i,
                        'width': width,
                        'height': height,
                        'fps': fps
                    })
                    print(f"  [{i}] ✓ Camera {i}: {width}x{height} @ {fps}fps")
                cap.release()
            else:
                cap.release()
        
        if not available_cameras:
            print("  ❌ No cameras found!")
        else:
            print(f"\n  Found {len(available_cameras)} camera(s)")
        
        print("-" * 50)
        return available_cameras
    
    def select_camera_interactive(self):
        cameras = self.list_available_cameras()
        
        if not cameras:
            print("\nNo cameras detected. Make sure your phone webcam app is running.")
            return None
        
        if len(cameras) == 1:
            print(f"\n✓ Auto-selecting camera {cameras[0]['index']}")
            return cameras[0]['index']
        
        print("\nMultiple cameras found. Please select one:")
        for cam in cameras:
            print(f"  {cam['index']}: Camera {cam['index']} ({cam['width']}x{cam['height']})")
        
        while True:
            try:
                choice = input(f"\nEnter camera number (0-{len(cameras)-1}): ").strip()
                if choice == "":
                    selected = cameras[0]['index']
                    print(f"Using default camera {selected}")
                    return selected
                
                selected = int(choice)
                if any(cam['index'] == selected for cam in cameras):
                    print(f"✓ Selected camera {selected}")
                    return selected
                else:
                    print(f"❌ Camera {selected} not available. Try again.")
            except ValueError:
                print("❌ Please enter a number.")
    
    def test_camera(self, camera_index):
        print(f"\n📹 Testing camera {camera_index}...")
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            print(f"❌ Cannot open camera {camera_index}")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            height, width = frame.shape[:2]
            print(f"✓ Camera {camera_index} working: {width}x{height}")
            return True
        else:
            print(f"❌ Camera {camera_index} not capturing frames")
            return False
    
    def auto_select_camera(self):
        cameras = self.list_available_cameras()
        
        for cam in cameras:
            if self.test_camera(cam['index']):
                return cam['index']
        
        return None
            
    def extract_temperature(self, roi_frame):
        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        text = pytesseract.image_to_string(denoised, config=self.config['ocr_config'])
        numbers = re.findall(r'-?\d+\.?\d*', text)
        
        if numbers:
            try:
                temp = float(numbers[0])
                return temp, text.strip()
            except ValueError:
                return None, text.strip()
        
        return None, text.strip()
    
    def play_alert_sound(self):
        try:
            for _ in range(3):
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                time.sleep(0.3)
        except:
            pass
    
    def log_temperature(self, temp, status="normal"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Temperature: {temp}°C - Status: {status}"
        
        with open(self.config['log_file'], 'a') as f:
            f.write(log_entry + "\n")
        
        print(log_entry)
    
    def check_alert(self, temp):
        if self.alert_triggered:
            return False
            
        threshold = self.config['temperature_threshold']
        direction = self.config['threshold_direction']
        
        if direction == "above" and temp >= threshold:
            return True
        elif direction == "below" and temp <= threshold:
            return True
        
        return False
    
    def trigger_alert(self, temp):
        print(f"\n{'='*50}")
        print(f"⚠️  ALERT! Temperature {temp}°C has reached threshold!")
        print(f"{'='*50}\n")
        self.log_temperature(temp, status="ALERT")
        
        Thread(target=self.play_alert_sound, daemon=True).start()
        
        self.alert_triggered = True
        
        def reset_alert():
            time.sleep(self.config['alert_cooldown_seconds'])
            self.alert_triggered = False
            print("\n✓ Alert reset. Monitoring resumed.\n")
        
        Thread(target=reset_alert, daemon=True).start()
    
    def run(self, camera_index=None):
        if camera_index is None:
            camera_index = self.config['camera_index']
        
        print(f"\n📷 Opening camera {camera_index}...")
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            print(f"❌ Error: Could not open camera {camera_index}")
            return False
        
        ret, test_frame = self.cap.read()
        if not ret or test_frame is None:
            print(f"❌ Error: Camera {camera_index} opened but not capturing")
            self.cap.release()
            return False
        
        print(f"✓ Camera {camera_index} ready")
        
        print("\n" + "="*50)
        print("✓ HEADLESS MODE - No GUI window")
        print("="*50)
        print(f"Threshold: {self.config['temperature_threshold']}°C ({self.config['threshold_direction']})")
        print(f"ROI: {self.config['roi']}")
        print(f"Logging to: {self.config['log_file']}")
        print("-"*50)
        print("Press Ctrl+C to stop\n")
        
        self.running = True
        last_log_time = time.time()
        roi = self.config['roi']
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("⚠️  Warning: Could not read frame")
                    time.sleep(1)
                    continue
                
                self.frame_count += 1
                
                roi_frame = frame[roi['y']:roi['y']+roi['height'], 
                                 roi['x']:roi['x']+roi['width']]
                
                temp, raw_text = self.extract_temperature(roi_frame)
                
                if temp is not None:
                    self.last_temp = temp
                    
                    if self.check_alert(temp):
                        self.trigger_alert(temp)
                    
                    current_time = time.time()
                    if current_time - last_log_time >= self.config['log_interval']:
                        self.log_temperature(temp)
                        last_log_time = current_time
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")
        finally:
            if self.cap:
                self.cap.release()
            print(f"\nMonitor stopped. Processed {self.frame_count} frames.")
        
        return True

def show_help():
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Temperature Monitor - Webcam Selection             ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  python temperature_monitor_headless.py           Auto-select camera
  python temperature_monitor_headless.py --list    List all cameras
  python temperature_monitor_headless.py --select  Interactive selection
  python temperature_monitor_headless.py 0         Use camera 0
  python temperature_monitor_headless.py 1         Use camera 1
  python temperature_monitor_headless.py --help    Show this help

Examples:
  # Let it auto-detect and select the best camera
  python temperature_monitor_headless.py
  
  # See all available cameras first
  python temperature_monitor_headless.py --list
  
  # Manually choose from available cameras
  python temperature_monitor_headless.py --select
  
  # Use a specific camera directly
  python temperature_monitor_headless.py 2

Note: If using phone as webcam, start the phone app first!
    """)

if __name__ == "__main__":
    import sys
    
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        print("⚠️  Tesseract OCR not found!")
        print("Please install Tesseract OCR first")
        sys.exit(1)
    
    monitor = TemperatureMonitorHeadless()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg in ['--help', '-h', '/?']:
            show_help()
            sys.exit(0)
        
        elif arg == '--list':
            monitor.list_available_cameras()
            sys.exit(0)
        
        elif arg == '--select':
            selected_camera = monitor.select_camera_interactive()
            if selected_camera is not None:
                monitor.config['camera_index'] = selected_camera
                monitor.save_config()
                monitor.run(selected_camera)
            sys.exit(0)
        
        else:
            try:
                camera_index = int(arg)
                print(f"Using camera {camera_index} from command line")
                monitor.run(camera_index)
                sys.exit(0)
            except ValueError:
                print(f"❌ Unknown argument: {arg}")
                print("Use --help for usage information")
                sys.exit(1)
    
    # No arguments - auto select
    print("🔍 Auto-detecting cameras...")
    selected_camera = monitor.auto_select_camera()
    
    if selected_camera is None:
        print("\n❌ No working cameras found!")
        print("\nTroubleshooting:")
        print("  1. Make sure your phone webcam app is running")
        print("  2. Try: python temperature_monitor_headless.py --list")
        print("  3. Check Windows Device Manager for camera devices")
        sys.exit(1)
    
    print(f"\n✓ Auto-selected camera {selected_camera}")
    print("Use --select flag next time to choose manually\n")
    
    monitor.config['camera_index'] = selected_camera
    monitor.save_config()
    monitor.run(selected_camera)
