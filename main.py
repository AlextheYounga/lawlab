import os
import time
import multiprocessing
import shutil
import redis
from src.download_code import sync_release_register, download_code, update_release_register
from src.file_monitor import html_file_monitor, markdown_file_monitor	
from src.split_html import split_html, split_html_async
from src.convert_to_markdown import convert_to_markdown, convert_to_markdown_async
from dotenv import load_dotenv  

load_dotenv()

r = redis.Redis(host='localhost', port=6379, db=0)
PROCESSES = int(os.environ.get('PROCESSES', 4))
USC_REPO = os.environ.get('USC_REPO', None)

def run_preflight(release_id):
	# Unzip the usc files
	r.flushall()
	os.system('rm -rf out/templates/html')
	os.system(f'unzip -o storage/{release_id}.zip -d storage/usc')
	# Remove previous output
	os.system('rm -rf out/usc')
	os.system('rm -rf out/templates/markdown')
	# Check for inconsistencies in the file structure
	if 'temp' in os.listdir('storage/usc'):
		os.system('mv storage/usc/temp/* storage/usc/')
		os.system('rm -rf storage/usc/temp')

def handle_html_files():
	  # Split HTML documents based on chapters and prune unnecessary tags from the content
	export_files = os.listdir('storage/usc')
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

def handle_html_files_async():
	# Split HTML documents based on chapters and prune unnecessary tags from the content
	monitor_process = multiprocessing.Process(target=html_file_monitor)
	monitor_process.start()
	try:
		export_files = os.listdir(f'storage/usc')
		os.makedirs('out/templates/html', exist_ok=True)
		with multiprocessing.Pool(PROCESSES) as pool:
			for _ in pool.imap_unordered(split_html_async, export_files):
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
			for _ in pool.imap_unordered(convert_to_markdown_async, html_files):
				pass
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


def handle_usc_repository_functions(release):
	if not USC_REPO: return
	os.system(f'rm -rf {USC_REPO}/usc')
	shutil.copytree('out/usc', f"{USC_REPO}/usc")
	commit_msg = f"release: {release['id']} - {release['date']}"
	description = f"USC repository update\n{release['description']}\n{release['link']}"
	os.system(f"sh githook.sh '{commit_msg}' '{description}'")


def main():
	releases = sync_release_register()
	inversed_releases = list(releases.keys())[::-1]
	
	for id in inversed_releases:
		print(f'\nProcessing release: {id}')
		release = releases[id]
		   
		# Download the code from https://uscode.house.gov/download/download.shtml
		download_code(release['link'], id)

		time_start = time.time() 
		# Preflight: unzip the usc files and remove previous output.
		run_preflight(id)

		# Handle file conversions.
		handle_html_files_async()
		handle_markdown_conversion_async()
		end_time = time.time() # Time the main program
		
		# Remove some temporary files and zip to save space.
		cleanup()
		update_release_register(id)
		handle_usc_repository_functions(release)
		
		print(f'\nDone! Time taken: {end_time - time_start:.2f} seconds')

if __name__ == '__main__':
	main()


