# OCR Tuning & Flashlight Support

## Context
### Original Request
"on monitoring mode the temperature sensor screen becomes black... when activating the backlight, the OCR performance is really bad"
### Specific Constraint
"Only turn on the flashlight once per minute the time to capture and process the image"

### Interview Summary
- **Problem**: Lighting issues. Phone shadows make screen dark; sensor backlight causes glare.
- **Sensor Type**: Standard LCD (Dark on Light).
- **Strategy**: 
  1. Add Flashlight (Torch) to provide even lighting from phone.
  2. Add OCR Tuning (Threshold Slider, Debug View) to handle glare/contrast variations.

### Metis Review (Self-Simulated)
- **Gap Identified**: UI Placement for debug canvas.
- **Resolution**: Place small debug canvas in the Controls panel so it doesn't obscure the main video.
- **Edge Case**: Torch API support on iOS is poor. Feature should be "progressive enhancement" (hide button if not supported).

---

## Work Objectives

### Core Objective
Improve OCR reliability in difficult lighting conditions.

### Concrete Deliverables
- Update `mobile_web_version/index.html`: Add Torch button, Threshold slider, Debug canvas.
- Update `mobile_web_version/app.js`: Implement Torch logic, variable thresholding, debug rendering.
- Update `mobile_web_version/style.css`: Style new controls.

### Definition of Done
- [x] User can toggle Flashlight (on supported devices).
- [x] User can see what the OCR engine "sees" (binary image).
- [x] User can adjust the threshold to make digits readable.
- [x] Invert mode available for unusual displays.

---

## Verification Strategy
- **Infrastructure**: Manual QA.
- **Tools**: Real Device (Android/iOS) needed for Torch. Chrome DevTools for UI/Logic.

---

## TODOs

- [x] 1. Add Torch & Tuning Controls to HTML
  **What to do**:
  - Add "🔦" button overlay on the camera view (top-right?).
  - Add "Tuning" section in `.controls-container`:
    - Range Input: `min="0" max="255" value="128"` (Threshold)
    - Checkbox: "Invert Colors"
    - Canvas: `<canvas id="debugCanvas">` (Small preview)

- [x] 2. Implement Torch Logic in app.js
  **What to do**:
  - In `startCamera`, check `track.getCapabilities().torch`.
  - Implement `setTorch(bool)` function.
  - Implement `Pulse Mode` logic:
    - Interval timer (default 60s).
    - Sequence: Torch ON -> Wait 1s (exposure) -> Process Frame -> Torch OFF.
    - While in Pulse Mode, disable standard `processFrame` loop? Or just synchronize it.
  - Update UI to select Flash Mode: `Off`, `On`, `Pulse (1m)`.

- [x] 3. Implement OCR Tuning Logic in app.js
  **What to do**:
  - Modify `processFrame`:
    - Use `state.config.threshold` instead of `128`.
    - Apply Invert logic if checked.
    - Draw the processed binary image to `#debugCanvas`.

- [x] 4. Style the new elements
  **What to do**:
  - Make the Torch button look like a floating action button (FAB).
  - Style the Debug Canvas to be small but visible (e.g., width: 100%).
  - Clean up inline styles from `index.html` (if any) and move to `style.css`.
  - Ensure the Tuning controls look integrated with the existing settings panel.

  **Verification**:
  - [x] UI elements appear correctly.
  - [x] Slider changes the Debug Canvas output in real-time.
  - [x] Torch toggles (if device supports).

---

## Success Criteria
- [x] "Black screen" solved via Torch.
- [x] "Glare" solved via Threshold tuning.
