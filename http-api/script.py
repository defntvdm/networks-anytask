#!/usr/bin/python3

from argparse import ArgumentParser
from requests import get
import sys


def get_args():
	parser = ArgumentParser(epilog="(c)Николаев Вадим КБ-201", 
		description="Скачивает фото с альбома по id пользователя и названию альбома",
		prog='python3 script.py 49482756 "Тра тра та"')
	parser.add_argument("user_id",
						type=int,
						help="ID пользователя vk.com")
	parser.add_argument("album",
						help="Из какого альбома скачиваем")
	parser.add_argument("-d", "--directory", help="Куда скачивать", default=".")
	return parser.parse_args()


def download(urls, path):
	for url in urls:
		ind = url.rfind('/')
		name = url[ind+1:]
		with open(path + "/" + name, mode="wb") as img:
			req = get(url)
			img.write(req.content)


def get_photos(user, album):
	request = "https://api.vk.com/method/photos.get?owner_id=%s&album_id=%s"
	response = get(request % (user, album)).json()
	if "response" in response:
		return response["response"]
	print(response["error"]["error_msg"])
	sys.exit()


def get_album_id(user, album):
	request = "https://api.vk.com/method/photos.getAlbums?owner_id=%s"
	response = get(request % (user)).json()
	for title in response['response']:
		if 'title' in title:
			if title['title'] == album:
				return title['aid']


def get_urls(photos):
	urls = []
	for photo in photos:
		urls.append(find_url(photo))
	return urls


def find_url(photo):
	keys = [i for i in photo.keys() if "src" in i and "big" in i]
	if keys:
		key = max(keys, key=lambda y: len(y))
		return photo[key]
	else:
		return photo["src"]


def main():
	args = get_args()
	user = args.user_id
	album = args.album
	directory = args.directory
	album_id = get_album_id(user, album)
	photos = get_photos(user, album_id)
	urls = get_urls(photos)
	download(urls, directory)


if __name__ == '__main__':
	main()
