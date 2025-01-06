import os
import time
import multiprocessing
import shutil
from pathlib import Path
from src.download_code import update_release_register, download_code
from src.file_monitor import html_file_monitor, markdown_file_monitor	
from src.split_html import split_html
from src.convert_to_markdown import convert_to_markdown
from dotenv import load_dotenv  

load_dotenv()
PROCESSES = int(os.environ.get('PROCESSES', 4))
USC_REPO = os.environ.get('USC_REPO', None)

def run_preflight(release_id):
    # Unzip the usc files
    os.system('rm -rf out/templates/html')
    os.system(f'unzip -o storage/{release_id}.zip -d storage/usc')
    # Remove previous output
    os.system('rm -rf out/usc')
    os.system('rm -rf out/templates/markdown')
    
def handle_html_files(release_id):
      # Split HTML documents based on chapters and prune unnecessary tags from the content
    export_files = os.listdir(f'storage/{release_id}')
    for file in export_files:
        print(f'Processing {file}...')
        split_html(file)
        
def handle_markdown_conversion():
    # Convert HTML files to markdown
    html_files = os.listdir('out/templates/html')
    os.makedirs('out/templates/markdown', exist_ok=True)	
    for file in html_files:
        print(f'Processing {file}...')
        convert_to_markdown(file)

def handle_html_files_async(release_id):
    # Split HTML documents based on chapters and prune unnecessary tags from the content
    monitor_process = multiprocessing.Process(target=html_file_monitor)
    monitor_process.start()
    try:
        export_files = os.listdir(f'storage/{release_id}')
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

def handle_markdown_conversion_async():
    # Convert HTML files to markdown
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
    releases = update_release_register()
    inversed_releases = list(releases.keys())[::-1]
    
    for id in inversed_releases:
        print(f'\nProcessing release: {id}')
        release = releases[id]
        time_start = time.time()   
        # Download the code from https://uscode.house.gov/download/download.shtml
        download_code(release['link'], id)

        # Preflight: unzip the usc files and remove previous output.
        run_preflight(id)

        # Handle file conversions.
        handle_html_files_async(id)
        handle_markdown_conversion_async()
        
        # Remove some temporary files and zip to save space.
        cleanup()

        # We copy the output to our public repo here.
        if USC_REPO:
            os.system(f'rm -rf {USC_REPO}/usc')
            shutil.copytree('out/usc', f"{USC_REPO}/usc")

        end_time = time.time()  
        print(f'\nDone! Time taken: {end_time - time_start:.2f} seconds')
        break

if __name__ == '__main__':
    main()


