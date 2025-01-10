import os
import time
import shutil
import subprocess
from src.download_code import sync_release_register, download_code, update_release_register
from dotenv import load_dotenv  

load_dotenv()

PROCESSES = int(os.environ.get('PROCESSES', 4))
USC_REPO = os.environ.get('USC_REPO', None)

def run_preflight(release_id):
	os.system(f'unzip -o storage/{release_id}.zip -d storage/usc')
	os.system('rm -rf out/usc')
	# Ensure downloaded files have consistent structure
	subprocess.run("./consistent_usc_files", shell=True) 

def pass_to_rust_handler():
	# Crazy fast
	print('Handing off to Rust to convert to Markdown...')
	return subprocess.run('./target/release/markdownconverter')

def cleanup():
	os.system('rm -rf storage/usc')
	os.system('rm -rf storage/__MACOSX')

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

		pass_to_rust_handler()

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


