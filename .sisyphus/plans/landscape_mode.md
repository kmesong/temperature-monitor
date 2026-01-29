# Landscape Mode Support

## Context
### Original Request
"Make the app work in landscape mode."

### Interview Summary
- **Layout Choice**: Split View (Video Left, Controls Right).
- **Goal**: Optimize for usability in horizontal orientation.

### Metis Review (Self-Simulated)
- **Gap Identified**: How to group header/controls/logs in right column without HTML changes?
- **Resolution**: Use CSS Grid with specific row/column assignments. Left column spans 3 rows.

---

## Work Objectives

### Core Objective
Implement responsive landscape layout using CSS Media Queries.

### Concrete Deliverables
- Update `mobile_web_version/style.css`

### Definition of Done
- [ ] App switches to Split View when device width > height.
- [ ] Camera takes up left side (majority width).
- [ ] Controls/Header/Logs stack on the right side.
- [ ] No elements are overlapping or inaccessible.

### Must Have
- `@media (orientation: landscape)`
- `display: grid` for `.app-container`

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (HTML/CSS only project for this part).
- **Manual QA**: YES.
- **Tools**: Chrome DevTools (Device Mode > Rotate).

---

## TODOs

- [x] 1. Implement Landscape Media Query
  **What to do**:
  - Add `@media (min-width: 480px) and (orientation: landscape)` block to `mobile_web_version/style.css`.
  - Modify `.app-container`:
    - `display: grid`
    - `grid-template-columns: 2fr 1fr` (Camera gets 2x space)
    - `grid-template-rows: auto 1fr 1fr` (Header, Controls, Logs)
    - `gap: 16px`
    - `height: 100vh`
    - `overflow: hidden` (prevent body scroll, let containers scroll)
  - Modify Children positioning:
    - `.camera-container`: `grid-column: 1`, `grid-row: 1 / span 3`, `height: 100%`
    - `header`: `grid-column: 2`, `grid-row: 1`
    - `.controls-container`: `grid-column: 2`, `grid-row: 2`, `overflow-y: auto`
    - `.logs-container`: `grid-column: 2`, `grid-row: 3`, `overflow-y: auto`

  **Verification**:
  - [ ] Open `mobile_web_version/index.html` in browser.
  - [ ] Toggle Device Toolbar (Ctrl+Shift+M).
  - [ ] Rotate to landscape.
  - [ ] Verify Split View layout appears.

  **References**:
  - `mobile_web_version/style.css` (existing styles to override)

---

## Success Criteria
- [ ] Camera feed is maximized on the left.
- [ ] Controls are easily accessible on the right.
- [ ] Layout breaks gracefully back to column on portrait.
