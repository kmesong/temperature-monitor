# CSS Grid for Landscape Layout
- Used CSS Grid to create a split-view layout for landscape orientation without modifying HTML structure.
- `grid-template-columns: 2fr 1fr` allows the camera to take up 2/3 of the screen width while keeping controls accessible.
- Resetting `max-width` to `none` (or implicit) is crucial for landscape mode to utilize the full screen width, unlike the centered portrait view.
- `aspect-ratio: auto` on the camera container is necessary when using `height: 100%` in a grid cell to preventing conflicting size constraints.
