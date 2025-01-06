import requests
import re
import json
import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def fetch_release_points():
	# Get the download link
	print("Fetching US Code releases...")
	url = "https://uscode.house.gov/download/priorreleasepoints.htm"
	response = requests.get(url)
	soup = BeautifulSoup(response.content, "html.parser")
	ul = soup.find("ul", class_="releasepoints")
	release_point_items = ul.find_all("li")

	releases = {}
	for release_point in release_point_items:
		atag = release_point.find("a")
		date_match = re.findall(r'(\d{1,2})/(\d{1,2})/(\d{4})', atag.text)
		date = None
		if date_match:
			date_match = date_match[0]
			date = datetime.datetime(int(date_match[2]), int(date_match[0]), int(date_match[1]))

		release = {
			"link": 'https://uscode.house.gov/download/' + atag.get("href"),
			"description": atag.text,
			"date": date.strftime("%Y-%m-%d") if date else "Date Unclear",
			"synced": False,
		}
		release_id = release["link"].split("/")[-1].split(".")[0]
		release["id"] = release_id
		releases[release_id] = release

	return releases

def sync_release_register():
	# Check releases.json file
	saved_releases = json.loads(open("releases.json", "r").read())
	# Get the latest releases from web
	latest_releases = fetch_release_points()

	for latest in latest_releases:
		if latest in saved_releases and saved_releases[latest]["synced"] == True:
			latest_releases[latest]["synced"] = True
			
	# Write JSON file 
	with open("releases.json", "w") as f:
		json.dump(latest_releases, f, indent=4)
	return latest_releases

def update_release_register(id):
	# Check releases.json file
	releases = json.loads(open("releases.json", "r").read())
	releases[id]["synced"] = True
	# Write JSON file 
	with open("releases.json", "w") as f:
		json.dump(releases, f, indent=4)


def download_code(link, release_id):
	# Get the download link
	print("Fetching US Code download link...")
	response = requests.get(link)
	soup = BeautifulSoup(response.content, "html.parser")
	selector = "#content > div > div > div.uscitemlist > div:nth-child(1) > div.itemdownloadlinks > a:nth-child(2)"
	html_link = soup.select(selector)[0]
	download_slug = html_link.get("href")
	download_url = urljoin(link, download_slug)
	print(f"Downloading US Code {download_slug}...")
	response = requests.get(download_url)
	with open(f"storage/{release_id}.zip", "wb") as f:
		f.write(response.content)