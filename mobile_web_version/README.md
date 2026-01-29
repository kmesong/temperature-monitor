# Mobile Temperature Monitor

This is a web-based version of the Temperature Monitor designed to run directly on your phone's browser. It processes the video feed locally on your device using Tesseract.js.

## Features
- **Zero Install**: Runs in the browser (Chrome/Safari).
- **Offline Capable**: All processing happens on the phone (after initial load).
- **Touch Controls**: Drag and resize the ROI (Region of Interest) box with touch.
- **Audio/Visual Alerts**: Beeps and flashes when threshold is reached.

## How to Run

### Option 1: GitHub Pages (Recommended)
The easiest way to run this on your phone is to host it on GitHub Pages.
1. Upload this folder (`mobile_web_version`) to a GitHub repository.
2. Go to Repository Settings > Pages.
3. Select the branch and folder.
4. Open the generated HTTPS URL on your phone.

*Note: Camera access requires HTTPS.*

### Option 2: Local Server (Advanced)
If you want to run it from your PC and access it on your phone via WiFi:

1. **Start a server** inside this folder:
   ```bash
   cd mobile_web_version
   python -m http.server 8000
   ```

2. **Accessing from Phone**:
   - **Problem**: Most mobile browsers block camera access on "insecure" (HTTP) connections like `http://192.168.1.5:8000`.
   - **Solution**: You need to treat the connection as secure.
     - **Android (Chrome)**: 
       1. Connect phone via USB.
       2. Enable USB Debugging.
       3. On PC Chrome: `chrome://inspect/#devices`.
       4. Click "Port forwarding".
       5. Add rule: Port `8000` -> `localhost:8000`.
       6. On Phone: Open `http://localhost:8000`.

### Option 3: Pythonista (iOS) or Termux (Android)
You can technically run the `http.server` directly on the phone if you have a terminal app, then open `http://localhost:8000` in the browser on the same device.

## Usage
1. Open the app.
2. Grant Camera Permissions.
3. Select the "Back Camera".
4. **Calibrate**: Tap "Adjust ROI" and drag/resize the green box to frame ONLY the temperature digits on your sensor.
5. Tap "Start Monitoring".
