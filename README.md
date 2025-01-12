From https://uscode.house.gov/download/download.shtml

# Scripts Used to Translate the US Code into Markdown

## Getting Started

Build the Rust target library

`cargo build --release` 

Install Python packages

`pip install -r requirements.txt`

Run the converter

`python main.py`

## Notes
This was originally all written in Python, but the overhead of multiprocessing was simply too slow. I even made [python-markdownify](https://github.com/matthewwithanm/python-markdownify/pull/162) 5x faster trying to save time. 

In the end I did the meme and rewrote the project in Rust. It is certainly amazing see the time to convert go from 5 minutes to 5 seconds by switching to Rust. In fairness, I also improved the logic quite a bit when I rewrote it in Rust, so that's not all Python's fault.