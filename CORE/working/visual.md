# working — visual

When `list(thread)` is called, an image is generated alongside the text response.

## What it shows

- Thread title
- Temperature indicator (Hot / Warm / Cold)
- Thread description/content
- Note titles listed with timestamps
- Created date, last touched date

## How it works

HTML template on disk at `VISUAL/working_thread.html`. Server fills in data, renders to image, returns image path alongside text response.

## Open Questions

- Exact HTML layout / styling — TBD
- Render method: screenshot HTML (playwright/selenium), or generate with matplotlib/pillow?
- Image saved where? `VISUAL/` folder? Overwritten each call or timestamped?
- Does the overview list (no params) also get a visual, or just text?
