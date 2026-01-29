"""
Temperature Monitor using Phone as Webcam
Uses OCR to read temperature from sensor display and alerts when threshold is reached.
"""

import cv2
import numpy as np
import pytesseract
import re
import time
import json
import os
from datetime import datetime
from threading import Thread
import winsound  # For Windows alert sound

class TemperatureMonitor:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.load_config()
        self.cap = None
        self.running = False
        self.last_temp = None
        self.alert_triggered = False
        
    def load_config(self):
        """Load or create configuration file"""
        default_config = {
            "camera_index": 0,
            "temperature_threshold": 50.0,
            "threshold_direction": "above",  # "above" or "below"
            "alert_cooldown_seconds": 60,
            "roi": {  # Region of interest for the temperature display
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 100
            },
            "ocr_config": "--psm 7 -c tessedit_char_whitelist=0123456789.-°CF",
            "enable_preview": True,
            "log_file": "temperature_log.txt"
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
            print(f"Created default config file: {self.config_file}")
            print("Please edit it with your settings before running again.")
            
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def extract_temperature(self, roi_frame):
        """Extract temperature value from ROI using OCR"""
        # Preprocess image for better OCR
        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to improve OCR accuracy
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        
        # Perform OCR
        text = pytesseract.image_to_string(
            denoised, 
            config=self.config['ocr_config']
        )
        
        # Extract numbers (including decimals)
        numbers = re.findall(r'-?\d+\.?\d*', text)
        
        if numbers:
            try:
                temp = float(numbers[0])
                return temp, text.strip()
            except ValueError:
                return None, text.strip()
        
        return None, text.strip()
    
    def play_alert_sound(self):
        """Play alert sound on Windows"""
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            time.sleep(0.5)
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except:
            pass
    
    def log_temperature(self, temp, status="normal"):
        """Log temperature to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Temperature: {temp}°C - Status: {status}\n"
        
        with open(self.config['log_file'], 'a') as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def check_alert(self, temp):
        """Check if temperature meets alert condition"""
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
        """Trigger alert when threshold is reached"""
        print(f"\n⚠️  ALERT! Temperature {temp}°C has reached threshold!")
        self.log_temperature(temp, status="ALERT")
        
        # Play alert sound in separate thread
        Thread(target=self.play_alert_sound, daemon=True).start()
        
        self.alert_triggered = True
        
        # Reset alert after cooldown
        def reset_alert():
            time.sleep(self.config['alert_cooldown_seconds'])
            self.alert_triggered = False
            print("\n✓ Alert reset. Monitoring resumed.")
        
        Thread(target=reset_alert, daemon=True).start()
    
    def draw_roi(self, frame):
        """Draw ROI rectangle on frame"""
        roi = self.config['roi']
        x, y = roi['x'], roi['y']
        w, h = roi['width'], roi['height']
        
        # Draw rectangle
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw label
        label = "Temperature ROI"
        cv2.putText(frame, label, (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame
    
    def run(self):
        """Main monitoring loop"""
        # Try to open camera
        camera_index = self.config['camera_index']
        print(f"Opening camera {camera_index}...")
        print("If using phone as webcam, make sure your phone app is running first.")
        
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {camera_index}")
            print("Trying camera 1...")
            self.cap = cv2.VideoCapture(1)
            if not self.cap.isOpened():
                print("Error: Could not open any camera")
                return
        
        print("\n✓ Camera opened successfully!")
        print(f"Monitoring temperature (threshold: {self.config['temperature_threshold']}°C)")
        print("Press 'q' to quit, 'r' to reset ROI selection, 'c' to capture test image")
        print("-" * 50)
        
        self.running = True
        roi_selection_mode = False
        roi_start = None
        
        while self.running:
            ret, frame = self.cap.read()
            
            if not ret:
                print("Error: Could not read frame")
                break
            
            # Get ROI coordinates
            roi = self.config['roi']
            x, y = roi['x'], roi['y']
            w, h = roi['width'], roi['height']
            
            # Extract ROI
            roi_frame = frame[y:y+h, x:x+w]
            
            # Extract temperature
            temp, raw_text = self.extract_temperature(roi_frame)
            
            if temp is not None:
                self.last_temp = temp
                
                # Check for alert
                if self.check_alert(temp):
                    self.trigger_alert(temp)
                
                # Display temperature on frame
                color = (0, 0, 255) if self.alert_triggered else (0, 255, 0)
                cv2.putText(frame, f"Temp: {temp}C", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                
                # Log temperature every 10 seconds
                if int(time.time()) % 10 == 0:
                    self.log_temperature(temp)
            
            # Draw ROI rectangle
            frame = self.draw_roi(frame)
            
            # Draw threshold info
            info_text = f"Threshold: {self.config['temperature_threshold']}C ({self.config['threshold_direction']})"
            cv2.putText(frame, info_text, (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Draw last raw OCR text
            if raw_text:
                cv2.putText(frame, f"OCR: {raw_text}", (10, frame.shape[0] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Show frame
            if self.config['enable_preview']:
                cv2.imshow('Temperature Monitor', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\nStopping monitor...")
                break
            elif key == ord('r'):
                # Reset ROI to center of frame
                h_frame, w_frame = frame.shape[:2]
                self.config['roi'] = {
                    "x": w_frame // 4,
                    "y": h_frame // 4,
                    "width": w_frame // 2,
                    "height": h_frame // 4
                }
                self.save_config()
                print("ROI reset to center of frame")
            elif key == ord('c'):
                # Capture test image
                filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved capture: {filename}")
            elif key == ord('+'):
                # Increase threshold
                self.config['temperature_threshold'] += 1
                self.save_config()
                print(f"Threshold increased to: {self.config['temperature_threshold']}C")
            elif key == ord('-'):
                # Decrease threshold
                self.config['temperature_threshold'] -= 1
                self.save_config()
                print(f"Threshold decreased to: {self.config['temperature_threshold']}C")
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        print("Monitor stopped.")

def setup_phone_webcam():
    """Instructions for setting up phone as webcam"""
    print("""
📱 PHONE WEBCAM SETUP OPTIONS:

Option 1 - DroidCam (Android/iOS):
   1. Install DroidCam app on your phone
   2. Install DroidCam client on PC from https://www.dev47apps.com/
   3. Connect via WiFi or USB
   4. Select DroidCam as camera in this script

Option 2 - Iriun Webcam (Android/iOS):
   1. Install Iriun Webcam app on phone
   2. Install Iriun Webcam software on PC
   3. Connect via WiFi or USB
   4. Usually appears as camera index 0 or 1

Option 3 - EpocCam (iOS):
   1. Install EpocCam app on iPhone
   2. Install drivers on Windows
   3. Connect to same WiFi network
   4. Select EpocCam as camera source

After setup, run this script and the phone camera should be available.
""")

def calibrate_roi():
    """Interactive ROI calibration tool"""
    print("\n🔧 ROI CALIBRATION MODE")
    print("This will help you position the temperature display in the frame.")
    print()
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    roi_config = {
        "x": 100,
        "y": 100,
        "width": 200,
        "height": 100
    }
    
    drawing = False
    start_x, start_y = -1, -1
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, start_x, start_y, roi_config
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_x, start_y = x, y
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                roi_config['x'] = min(start_x, x)
                roi_config['y'] = min(start_y, y)
                roi_config['width'] = abs(x - start_x)
                roi_config['height'] = abs(y - start_y)
                
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            roi_config['x'] = min(start_x, x)
            roi_config['y'] = min(start_y, y)
            roi_config['width'] = abs(x - start_x)
            roi_config['height'] = abs(y - start_y)
    
    cv2.namedWindow('Calibrate ROI')
    cv2.setMouseCallback('Calibrate ROI', mouse_callback)
    
    print("Drag to select the temperature display area")
    print("Press 's' to save, 'r' to reset, 'q' to quit without saving")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Draw current ROI
        x, y = roi_config['x'], roi_config['y']
        w, h = roi_config['width'], roi_config['height']
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Show coordinates
        coord_text = f"ROI: x={x}, y={y}, w={w}, h={h}"
        cv2.putText(frame, coord_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow('Calibrate ROI', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save to config
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            config['roi'] = roi_config
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            print(f"\n✓ ROI saved: {roi_config}")
            break
        elif key == ord('r'):
            roi_config = {"x": 100, "y": 100, "width": 200, "height": 100}
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            setup_phone_webcam()
        elif sys.argv[1] == "--calibrate":
            calibrate_roi()
        elif sys.argv[1] == "--help":
            print("""
Temperature Monitor - Usage:

  python temperature_monitor.py           Start monitoring
  python temperature_monitor.py --setup   Show webcam setup instructions
  python temperature_monitor.py --calibrate  Calibrate ROI selection
  python temperature_monitor.py --help    Show this help

Configuration file (config.json):
  - camera_index: Camera device index (usually 0 or 1)
  - temperature_threshold: Alert threshold value
  - threshold_direction: "above" or "below"
  - roi: Region of interest coordinates
  - alert_cooldown_seconds: Time between alerts

Controls during monitoring:
  q - Quit
  r - Reset ROI to center
  c - Capture test image
  + - Increase threshold by 1
  - - Decrease threshold by 1
""")
    else:
        # Check if tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            print("⚠️  Tesseract OCR not found!")
            print("Please install Tesseract OCR:")
            print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print("  Then add it to your PATH environment variable")
            print("\nOr install via:")
            print("  choco install tesseract")
            sys.exit(1)
        
        # Run monitor
        monitor = TemperatureMonitor()
        monitor.run()
