import secrets
import sqlite3

from flask import Flask
import flask

from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError

app = Flask(__name__)

app.secret_key = secrets.token_hex()

@app.route('/authorize')
def authorize():
	flow = Flow.from_client_secrets_file('../secret_stuff/dislike_count/server_secret.json', scopes=('https://www.googleapis.com/auth/youtube',))
	flow.redirect_uri = 'https://phoenixc.uber.space/dislike_count/callback'

	url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
	flask.session['state'] = state
	return flask.redirect(url)

@app.route('/callback')
def callback():
	flow = Flow.from_client_secrets_file('../secret_stuff/dislike_count/server_secret.json', scopes=('https://www.googleapis.com/auth/youtube',), state=flask.session['state'])
	flow.redirect_uri = 'https://phoenixc.uber.space/dislike_count/callback'

	flask.session = {}

	try:
		flow.fetch_token(authorization_response=flask.request.url)
	except AccessDeniedError:
		return flask.redirect('/dislike_count/static/index.html')
	credentials = flow.credentials

	conn = sqlite3.connect('../secret_stuff/dislike_count/user_secrets.db')
	with conn:
		conn.execute('INSERT INTO token(json) VALUES (?)', (credentials.to_json(),))
	conn.close()

	return flask.redirect('/dislike_count/static/success.html')