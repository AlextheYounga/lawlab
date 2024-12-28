import requests
import os
from bs4 import BeautifulSoup


def download_code():
	# Get the download link
	print("Fetching US Code download link...")
	url = "https://uscode.house.gov/download/download.shtml"
	response = requests.get(url)
	soup = BeautifulSoup(response.content, "html.parser")
	selector = "#content > div > div > div.uscitemlist > div:nth-child(1) > div.itemdownloadlinks > a:nth-child(2)"
	download_link = soup.select(selector)[0].get("href")

	# Download the file
	download_url = f"https://uscode.house.gov/download/{download_link}"
	print(f"Downloading US Code {download_url}...")
	response = requests.get(download_url)
	with open("storage/usc.zip", "wb") as f:
		f.write(response.content)