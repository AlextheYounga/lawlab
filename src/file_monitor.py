import os
import time
# A thread process which monitors the conversion of HTML files to markdown files.

DISPLAY_LIMIT = 35

def html_file_monitor():
    log_path = 'out/log.txt'
    open(log_path, 'w').close()
    while True:
        time.sleep(1)
        html_files = os.listdir('out/templates/html')
        index = {}

        for f in html_files:
            title_num = f.split('_')[0].replace('.html', '')
            if title_num not in index:
                index[title_num] = 0
            index[title_num] += 1
            
        with open(log_path, 'w') as f:
            for title in index.keys():
                f.write(f'Created {index[title]} files from Title {title}.\n')
            f.write('\n\n')
            f.write(f'Processed {len(html_files)}\n')

        # Clear the terminal
        os.system('clear')
        # Read and display the current file contents
        with open(log_path, 'r') as file:
            print(file.read())


def markdown_file_monitor():
    html_files = set(os.listdir('out/templates/html'))
    html_count = len(html_files)
    log_path = 'out/log.txt'
    open(log_path, 'w').close()
    while True:
        time.sleep(1)
        markdown_files = set(os.listdir('out/templates/markdown'))
        if len(markdown_files) == html_count:
            break

        still_processing = []
        for file in html_files:
            mdfilename = file.replace('.html', '.md')
            if mdfilename not in markdown_files:
                still_processing.append(file)
            
        with open(log_path, 'w') as f:
            for file in still_processing[:DISPLAY_LIMIT]:
                f.write(f'Converting to markdown: {file}...\n')
            if len(still_processing) > DISPLAY_LIMIT:
                f.write(f'...and {len(still_processing) - DISPLAY_LIMIT} more files\n')
            f.write('\n\n')
            f.write(f'Processed {len(markdown_files)} out of {html_count} files\n')

        # Clear the terminal
        os.system('clear')
        # Read and display the current file contents
        with open(log_path, 'r') as file:
            print(file.read())
