import os
import re
import shutil
import redis
from pathlib import Path
from markdownify import markdownify as md

r = redis.Redis(host='localhost', port=6379, db=0)

def copy_to_out(doc:str):
    document_id = doc.replace('.md', '')
    path_value = r.get(document_id)
    file_path = path_value.decode('utf-8')
    out_path = Path(f'out/usc/{file_path}.md')
    os.makedirs(out_path.parent, exist_ok=True)
    shutil.copyfile(f'out/templates/markdown/{doc}', out_path.__str__())  


def remove_excess_line_breaks(text):
    # Replace any occurrence of more than two line breaks with exactly two line breaks
    text = text.replace('  ', '')
    cleaned_text = re.sub(r'\n{3,}', '\n\n', text)
    return cleaned_text


def convert_to_markdown(doc:str):
    content = open(f'out/templates/html/{doc}', 'rb').read()
    markdown = md(content, heading_style="ATX_CLOSED")
    markdown = remove_excess_line_breaks(str(markdown))
    filename = doc.replace('.html', '.md')
    out_path = Path(f'out/templates/markdown/{filename}')
    with open(out_path, 'w') as f:
        f.write(markdown)
    copy_to_out(filename)




