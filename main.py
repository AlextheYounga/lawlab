import os
import time
import subprocess
from src.download_code import sync_release_register, download_code, update_release_register
from dotenv import load_dotenv  
from termcolor import colored
load_dotenv()

PROCESSES = int(os.environ.get('PROCESSES', 4))
USC_REPO = os.environ.get('USC_REPO', None)

def run_preflight(release_id):
	print('Running preflight checks...', end='\r')
	print('Unzipping files...', end='\r')
	os.system(f'unzip -o storage/{release_id}.zip -d storage/usc > /dev/null')
	print('Removing old files...', end='\r')
	os.system('rm -rf out/usc')
	# Ensure downloaded files have consistent structure
	print('Ensuring consistent file structure...', end='\r')
	subprocess.run("./scripts/consistent_usc_files", shell=True) 
	print('\n')

def rust_convert_to_markdown():
	# Crazy fast
	print(colored('Handing off to Rust to convert to Markdown...', 'green'))
	return subprocess.run('./target/release/markdownconverter')

def cleanup():
	print('\nCleaning up...')
	os.system('rm -rf storage/usc')
	os.system('rm -rf storage/__MACOSX')

def handle_usc_repository_functions(release):
	if not USC_REPO: return
	print('Copying out/usc to main repository...')
	os.system(f'rm -rf {USC_REPO}/usc')
	os.system(f'mv out/usc {USC_REPO}/')
	print(colored('Running git commands... Terminate at your own risk during this step.', 'yellow'))
	release_number = release['id'].split('@')[1]
	commit_msg = f"release: {release['date']} - public law {release_number}"
	description = f"USC repository update\n{release['description']}\n{release['link']}"
	subprocess.run(f"./scripts/githook '{commit_msg}' '{description}'", shell=True)
	print('\n')

def main():
	releases = sync_release_register()
	inversed_releases = list(releases.keys())[::-1]
	
	for id in inversed_releases:
		release = releases[id]
		date = release['date']
		if release['synced']: continue

		print(colored(f'\nProcessing release: {id} {date}', 'yellow'))
		time_start = time.time() 
		# Check for existing download
		existing_download = os.path.exists(f'storage/{id}.zip')   
		if not existing_download:
			download_code(release['link'], id)
		
		# Begin main program
		run_preflight(id)
		rust_convert_to_markdown() # Pass off to Rust program

		# Housekeeping
		cleanup() # Remove some temporary files and zip to save space.
		update_release_register(id) # Update releases.json
		handle_usc_repository_functions(release) # Copy out/usc to main repo and commit
		end_time = time.time() # Time the main program
		print(colored(f'\nDone! Time taken: {end_time - time_start:.2f} seconds', 'green'))
		
if __name__ == '__main__':
	main()


