#!/usr/bin/env python3.8

import sqlite3
import json

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError

def handle_channel(credentials):
	with build('youtube', 'v3', credentials=credentials) as yt:
		playlist_id = yt.channels().list(
			mine=True,
			part='contentDetails',
			fields='items/contentDetails/relatedPlaylists/uploads'
		).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

		req_uploads = yt.playlistItems().list(
			playlistId=playlist_id,
			part='status, contentDetails',
			fields='nextPageToken, items(status/privacyStatus, contentDetails/videoId)',
			maxResults=50
		)
		video_ids = []
		while req_uploads is not None:
			resp_uploads = req_uploads.execute()
			for item in resp_uploads['items']:
				if item['status']['privacyStatus'] == 'public' or item['status']['privacyStatus'] == 'unlisted':
					video_ids.append(item['contentDetails']['videoId'])
			req_uploads = yt.playlistItems().list_next(req_uploads, resp_uploads)

		req_videos = yt.videos().list(
			id=','.join(video_ids),
			part='status, statistics, snippet, id',
			fields='nextPageToken, items(status/publicStatsViewable, statistics/dislikeCount, snippet(title, description, tags, categoryId, defaultLanguage), id)',
			maxResults=50
		)
		while req_videos is not None:
			resp_videos = req_videos.execute()
			for item in resp_videos['items']:
				if item['status']['publicStatsViewable']:
					dislike_count = int(item['statistics']['dislikeCount'])
					snippet_old = item['snippet']
					description = snippet_old['description']
					if description.startswith("dislike count: "):
						parts = description.split("\n", maxsplit=1)
						if int(parts[0][15:]) == dislike_count:
							continue
						description = None if len(parts) != 2 else parts[1]
					# WATCH OUT!
					# We are explicitly setting only a few values in the snippet here.
					# These are the values that YT's documentation currently lists as editable.
					# All editable values that aren't included in the request will be DELETED!
					# That means, if YT ever decides to make more values editable, this code MUST BE UPDATED!
					snippet_new = {
						'title': snippet_old['title'],
						'description': "dislike count: {}".format(dislike_count) if description is None else "dislike count: {}\n{}".format(dislike_count, description),
						'tags': snippet_old['tags'],
						'categoryId': snippet_old['categoryId']
					}
					if 'defaultLanguage' in snippet_old:
						snippet_new['defaultLanguage'] = snippet_old['defaultLanguage']
					yt.videos().update(
						part='snippet',
						body={'id': item['id'], 'snippet': snippet_new}
					).execute()
			req_videos = yt.videos().list_next(req_videos, resp_videos)

if __name__ == '__main__':
	conn = sqlite3.connect('file:../secret_stuff/dislike_count/user_secrets.db?mode=ro')
	with conn:
		conn.row_factory = sqlite3.Row
		strings = tuple(row['json'] for row in conn.execute('SELECT json FROM token'))
	conn.close()

	for text in strings:
		credentials = Credentials.from_authorized_user_info(json.loads(text))
		try:
			handle_channel(credentials)
		except RefreshError:
			conn = sqlite3.connect('../secret_stuff/dislike_count/user_secrets.db')
			with conn:
				conn.execute('DELETE FROM token WHERE json=?', (text,))
			conn.close()