# Temperature Monitor with Phone Webcam

Monitor a temperature sensor display using your phone as a webcam, with OCR to read values and alerts when thresholds are reached.

## Features

- **Phone as Webcam**: Use your Android/iPhone as a webcam via DroidCam, Iriun, or EpocCam
- **OCR Recognition**: Reads temperature digits from the sensor display
- **Configurable Alerts**: Set temperature thresholds (above/below)
- **Real-time Preview**: Visual feedback with temperature overlay
- **Logging**: Automatic temperature logging to file
- **ROI Calibration**: Easy selection of the temperature display area

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH
- Or use: `choco install tesseract`

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 3. Setup Phone as Webcam

Choose one of these apps:

**Option A: DroidCam (Recommended)**
- Install DroidCam app on your phone
- Install DroidCam client on PC from https://www.dev47apps.com/
- Connect via WiFi or USB

**Option B: Iriun Webcam**
- Install Iriun Webcam app on phone and PC
- Connect via WiFi or USB

**Option C: IP Webcam (Android)**
- Install IP Webcam app
- Use the URL as video source

## Usage

### First Time Setup

1. **Calibrate the ROI** (Region of Interest):
```bash
python temperature_monitor.py --calibrate
```
Drag to select the area where the temperature is displayed on your sensor.

2. **Edit Configuration**:
Open `config.json` and set:
- `temperature_threshold`: The temperature that triggers alert
- `threshold_direction`: "above" or "below"
- `camera_index`: Usually 0 or 1 (try both)

### Run the Monitor

```bash
python temperature_monitor.py
```

### Keyboard Controls

- **q** - Quit
- **r** - Reset ROI to center
- **c** - Capture test image
- **+** - Increase threshold by 1
- **-** - Decrease threshold by 1

## Configuration (config.json)

```json
{
    "camera_index": 0,
    "temperature_threshold": 50.0,
    "threshold_direction": "above",
    "alert_cooldown_seconds": 60,
    "roi": {
        "x": 100,
        "y": 100,
        "width": 200,
        "height": 100
    },
    "enable_preview": true,
    "log_file": "temperature_log.txt"
}
```

## Tips for Best OCR Results

1. **Good Lighting**: Ensure the temperature display is well-lit
2. **Stable Phone**: Use a tripod or phone holder
3. **Focus**: Make sure the display is in focus
4. **ROI Size**: Select only the temperature digits, not the entire display
5. **Contrast**: Higher contrast between digits and background helps OCR

## Troubleshooting

**Camera not found:**
- Try different camera_index values (0, 1, 2)
- Ensure your phone webcam app is running first

**OCR not reading numbers:**
- Recalibrate ROI with `--calibrate`
- Ensure good lighting on the display
- Check that Tesseract is installed and in PATH

**False readings:**
- Make ROI smaller and more precise
- Adjust the position to avoid glare

## Example Output

```
2025-01-29 10:30:15 - Temperature: 23.5C - Status: normal
2025-01-29 10:30:25 - Temperature: 23.7C - Status: normal
⚠️  ALERT! Temperature 50.5C has reached threshold!
2025-01-29 10:30:35 - Temperature: 50.5C - Status: ALERT
✓ Alert reset. Monitoring resumed.
```

## License

MIT