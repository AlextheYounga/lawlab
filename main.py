import os
import time
import multiprocessing
import shutil
import redis
from pathlib import Path
import subprocess
from src.download_code import sync_release_register, download_code, update_release_register
from src.file_monitor import html_file_monitor, markdown_file_monitor	
from src.split_html import split_html, split_html_async
from dotenv import load_dotenv  

load_dotenv()

r = redis.Redis(host='localhost', port=6379, db=0)
PROCESSES = int(os.environ.get('PROCESSES', 4))
USC_REPO = os.environ.get('USC_REPO', None)

def run_preflight(release_id):
	# Unzip the usc files
	r.flushall()
	os.system('rm -rf out/templates/html')
	os.system('rm -rf out/templates/markdown')
	os.system(f'unzip -o storage/{release_id}.zip -d storage/usc')
	os.system('rm -rf out/usc')
	# Recursively find the htm files
	subprocess.run("./consistent_usc_files", shell=True)

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


def handle_rust_markdown_conversion():
	# Crazy fast
	print('Handing off to Rust to convert to Markdown...')
	return subprocess.run('./target/release/markdownconverter')


def copy_to_out():
	for mdfile in os.listdir(f'./out/templates/markdown'):
		document_id = mdfile.replace('.md', '')
		path_value = r.get(document_id)
		file_path = path_value.decode('utf-8')
		out_path = Path(f'out/usc/{file_path}.md')
		os.makedirs(out_path.parent, exist_ok=True)
		shutil.copyfile(f'out/templates/markdown/{mdfile}', out_path.__str__())  


def cleanup():
	os.system('rm -rf storage/usc')
	os.system('rm -rf storage/__MACOSX')
	os.system('rm -rf out/templates/markdown')
	os.system('rm -rf out/templates/html')


def handle_usc_repository_functions(release):
	if not USC_REPO: return
	os.system(f'rm -rf {USC_REPO}/usc')
	shutil.copytree('out/usc', f"{USC_REPO}/usc")
	commit_msg = f"release: {release['id']} - {release['date']}"
	description = f"USC repository update\n{release['description']}\n{release['link']}"
	subprocess.run(f"./githook '{commit_msg}' '{description}'", shell=True)

def main():
	releases = sync_release_register()
	inversed_releases = list(releases.keys())[::-1]
	
	for id in inversed_releases:
		print(f'\nProcessing release: {id}')
		release = releases[id]
		if release['synced']: continue
		
		existing_download = os.path.exists(f'storage/{id}.zip')   
		if not existing_download:
			download_code(release['link'], id)
		else:
			print('Code already downloaded.')

		time_start = time.time() 
		# Preflight: unzip the usc files and remove previous output.
		run_preflight(id)

		# Handle file conversions.
		handle_html_files_async()
		handle_rust_markdown_conversion()
		copy_to_out() # now this is slow
		# handle_markdown_conversion_async()
		end_time = time.time() # Time the main program
		print(f'\nDone! Time taken: {end_time - time_start:.2f} seconds')
		
		# Remove some temporary files and zip to save space.
		# cleanup()
		# update_release_register(id)
		# handle_usc_repository_functions(release)
		break
		

if __name__ == '__main__':
	main()


