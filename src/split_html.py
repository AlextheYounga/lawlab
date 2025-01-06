import os
import re
from pathlib import Path
from bs4 import BeautifulSoup, Comment
import redis
import logging

r = redis.Redis(host='localhost', port=6379, db=0)
logging.basicConfig(filename='out/errors.log', 
					level=logging.ERROR, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

def format_name(name: str) -> str:
	"""
	Sanitize a string for use as a file name component.
	"""
	name = (name.replace('/', '-')
				.replace('—', '-')
				.replace(' ', '-')
				.lower())
	name = re.sub(r"[^a-z0-9-]", "", name)
	name = name.split('-')[:5]
	return '-'.join(name)

def write_file(output_path: Path, content: str) -> None:
	"""
	Write HTML content to a file, ensuring parent directories exist.
	"""
	os.makedirs(output_path.parent, exist_ok=True)
	with open(output_path, 'w', encoding='utf-8') as f:
		f.write(content)

def format_citation(citation):
	citation = (citation.lower().strip()
			.replace(' ', '-')
			.replace('expcite:', '')
			.replace('.', '')
			.replace('/', '')
			.replace(',', ''))   
	return citation.replace('!@!', '/')

def handle_appendix(doc, soup: BeautifulSoup) -> None:
	# The appendix can never be broken up.
	"""
	If the file is an appendix (a.htm), we just dump it to a single .html file
	that ends with _appendix.html.
	"""
	# Have to load main title to get expcite
	title_number = re.search(r"\d+a", doc).group(0)
	main_title = doc.replace(title_number, title_number[:-1])
	main_path = Path(f'storage/usc/{main_title}')
	main_content = open(main_path, 'rb').read()
	main_soup = BeautifulSoup(main_content, 'html.parser')  

	citation = None
	comments = main_soup.find_all(string=lambda text: isinstance(text, Comment))
	for comment in comments:
		if 'expcite' in comment:
			citation = format_citation(comment)
			break
	
	file_path = f"{citation}/appendix"
	document_id = doc.replace('PRELIMusc', '').replace('.htm', '')
	r.set(document_id, file_path)
	out_path = Path(f'out/templates/html/{document_id}.html')
	write_file(out_path, str(soup))

# Find the last comment above the target tag containing the desired string
def find_item_citation(tag):
	for element in tag.previous_elements:
		if isinstance(element, Comment) and 'expcite' in element:
			return format_citation(element)
	raise Exception('Could not find citation for item.')

def find_document_id(tag):
	for element in tag.previous_elements:
		if isinstance(element, Comment) and 'documentid' in element:
			return element.split('documentid:')[1].split(' ')[0].strip()
	raise Exception('Could not find document id for item.')

def split_html(doc: str):
	if not doc.endswith('.htm'): return
	doc_path = Path(f'storage/usc/{doc}')
	doc_content = open(doc_path, 'rb').read()
	soup = BeautifulSoup(doc_content, 'html.parser')
	doc_title = soup.find('h1', class_="usc-title-head")

	if 'appendix' in doc_title.text.lower(): 
		return handle_appendix(doc, soup)
	
	content_str = str(soup)
	section_tags = soup.find_all('h3', class_='section-head')
	sections = content_str.split('<h3 class="section-head">')
	front_matter = sections.pop(0)

	for i, section in enumerate(sections):
		section_tag = section_tags[i]
		section_content = str(section_tag) + section
		section_path = find_item_citation(section_tag)
		document_id = find_document_id(section_tag)
		r.set(document_id, section_path)

		if i == 0:
			section_content = front_matter + section_content + "</div></body></html>"
		if i == len(sections) - 1:
			section_content = "<html><body><div>" + section_content

		out_path = Path(f'out/templates/html/{document_id}.html')
		write_file(out_path, section_content)


def split_html_async(doc: str):
	try:
		split_html(doc)
	except Exception as e:
		logging.error(f'Error converting {doc}: {e}')
	

