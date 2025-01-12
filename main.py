import os
import time
import subprocess
from src.download_code import sync_release_register, download_code, update_release_register
from dotenv import load_dotenv  

load_dotenv()

PROCESSES = int(os.environ.get('PROCESSES', 4))
USC_REPO = os.environ.get('USC_REPO', None)

def run_preflight(release_id):
	print('Unzipping files...')
	os.system(f'unzip -o storage/{release_id}.zip -d storage/usc')
	print('Removing old files...')
	os.system('rm -rf out/usc')
	# Ensure downloaded files have consistent structure
	print('Running preflight checks...\n')
	subprocess.run("./scripts/consistent_usc_files", shell=True) 

def rust_convert_to_markdown():
	# Crazy fast
	print('Handing off to Rust to convert to Markdown...')
	return subprocess.run('./target/release/markdownconverter')

def cleanup():
	print('Cleaning up...')
	os.system('rm -rf storage/usc')
	os.system('rm -rf storage/__MACOSX')

def handle_usc_repository_functions(release):
	if not USC_REPO: return
	print('Copying out/usc to main repository...')
	os.system(f'rm -rf {USC_REPO}/usc')
	os.system(f'mv out/usc {USC_REPO}/')
	print('Running git commands... Terminate at your own risk during this step.')
	commit_msg = f"release: {release['id']} - {release['date']}"
	description = f"USC repository update\n{release['description']}\n{release['link']}"
	subprocess.run(f"./scripts/githook '{commit_msg}' '{description}'", shell=True)

def main():
	releases = sync_release_register()
	inversed_releases = list(releases.keys())[::-1]
	
	for id in inversed_releases:
		release = releases[id]
		date = release['date']
		if release['synced']: continue

		print(f'Processing release: {id} {date}')
		# Check for existing download
		existing_download = os.path.exists(f'storage/{id}.zip')   
		if not existing_download:
			download_code(release['link'], id)
		
		# Begin main program
		time_start = time.time() 
		run_preflight(id)
		rust_convert_to_markdown() # Pass off to Rust program
		end_time = time.time() # Time the main program
		print(f'\nDone! Time taken: {end_time - time_start:.2f} seconds')
		
		cleanup() # Remove some temporary files and zip to save space.
		update_release_register(id) # Update releases.json
		handle_usc_repository_functions(release) # Copy out/usc to main repo and commit
		
if __name__ == '__main__':
	main()


