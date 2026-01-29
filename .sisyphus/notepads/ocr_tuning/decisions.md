# Implementation Decisions

## Pulse Mode Logic
- Implemented a 3-state Torch system: Off, On, Pulse.
- **Pulse Sequence**: 
    1. Torch ON
    2. Wait 1000ms (Exposure stabilization)
    3. Capture Frame
    4. Torch OFF (delayed by 200ms to ensure capture concurrency safety)
    5. Wait 60s
- **Concurrency**: 
    - Disabled the standard `processFrame` loop (`setTimeout`) when in Pulse Mode to prevent double-processing.
    - Used a separate `setInterval` for the pulse trigger.
    - Added checks in `processFrame` to ensure it doesn't loop if mode is 'pulse'.

## Torch Support
- Added `getCapabilities().torch` check in `startCamera`.
- Button is hidden if API returns false (Progressive Enhancement).
- Note: iOS WebRTC support for Torch is limited/non-standard in some versions, but this implementation follows the W3C spec (`applyConstraints` with `advanced`).

### CSS Refactoring (Style the new elements)
- **Decision**: Moved inline styles from `index.html` to `style.css` for better maintainability and separation of concerns.
- **Details**:
  - Created `.btn-torch` for the floating action button (FAB) style.
  - Created `.debug-canvas` for the debug canvas styling.
  - Created `.tuning-panel` and related classes (`.slider-container`, `.slider-input`, `.slider-value`, `.canvas-row`) to style the image tuning controls.
  - Utilized existing `.setting-row label` styles to remove redundant inline styles.
