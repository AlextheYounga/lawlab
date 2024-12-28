import os
import time
import multiprocessing
import shutil
from pathlib import Path
from src.download_code import download_code
from src.file_monitor import html_file_monitor, markdown_file_monitor	
from src.split_html import split_html
from src.convert_to_markdown import convert_to_markdown
from dotenv import load_dotenv  

load_dotenv()
PROCESSES = int(os.environ.get('PROCESSES', 4))
USC_REPO = os.environ.get('USC_REPO', None)

def handle_html_files():
    # Unzip the usc files
    os.system('rm -rf out/templates/html')
    os.system('unzip -o storage/usc.zip -d storage/usc')
    monitor_process = multiprocessing.Process(target=html_file_monitor)
    monitor_process.start()
    try:
        export_files = os.listdir('storage/usc')
        os.makedirs('out/templates/html', exist_ok=True)
        with multiprocessing.Pool(PROCESSES) as pool:
            for result in pool.imap_unordered(split_html, export_files):
                pass
    except KeyboardInterrupt:
        print('Exiting...')
        monitor_process.kill()
        exit(0)
    print('Done processing HTML files')
    monitor_process.kill()

def handle_markdown_conversion():
    os.system('rm -rf out/usc')
    os.system('rm -rf out/templates/markdown')
    monitor_process = multiprocessing.Process(target=markdown_file_monitor)
    monitor_process.start()
    try:
        html_files = os.listdir('out/templates/html')
        os.makedirs('out/templates/markdown', exist_ok=True)	
        with multiprocessing.Pool(PROCESSES) as pool:
            pool.map(convert_to_markdown, html_files)
    except KeyboardInterrupt:
        print('Exiting...')
        monitor_process.join()
        exit(0)
    monitor_process.join()

def cleanup():
    print('Zipping files...')
    os.system('rm -rf storage/usc')
    os.system('rm -rf storage/__MACOSX')
    os.system('cd out/templates/ && zip -qrq markdown.zip markdown')
    os.system('cd out/templates/ && zip -qrq html.zip html')
    os.system('rm -rf out/templates/markdown')
    os.system('rm -rf out/templates/html')
    

def main():
    time_start = time.time()    

    # Split HTML documents based on chapters and prune unnecessary tags from the content
    handle_html_files()

    # Convert HTML files to markdown
    handle_markdown_conversion()

    if USC_REPO:
        os.system(f'rm -rf {USC_REPO}/usc')
        shutil.copytree('out/usc', f"{USC_REPO}/usc")

    cleanup()

    end_time = time.time()  
    print(f'\nDone! Time taken: {end_time - time_start:.2f} seconds')


def test_sync():
    # Unzip the usc files
    os.system('rm -rf out/templates/html')
    os.system('unzip -o storage/usc.zip -d storage/usc')

    export_files = os.listdir('storage/usc')
    os.makedirs('out/templates/html', exist_ok=True)
    for doc in export_files:
        print(f'Processing {doc}...')
        split_html(doc)


if __name__ == '__main__':
    # Download the code from https://uscode.house.gov/download/download.shtml
    download_code()
    main()
    # test_sync()


