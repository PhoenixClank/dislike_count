import settings

import secrets
import sqlite3

from flask import Flask
import flask

from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError

app = Flask(__name__)

app.secret_key = secrets.token_hex()

@app.route('/')
def index():
	return flask.redirect('/dislike_count/static/index.html', code=308)

@app.route('/authorize')
def authorize():
	flow = Flow.from_client_secrets_file(settings.server_secret_file, scopes=('https://www.googleapis.com/auth/youtube',))
	flow.redirect_uri = settings.callback_url

	url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
	flask.session['state'] = state
	return flask.redirect(url, code=307)

@app.route('/callback')
def callback():
	flow = Flow.from_client_secrets_file(settings.server_secret_file, scopes=('https://www.googleapis.com/auth/youtube',), state=flask.session['state'])
	flow.redirect_uri = settings.callback_url

	flask.session = {}

	try:
		flow.fetch_token(authorization_response=flask.request.url)
	except AccessDeniedError:
		return flask.redirect('/dislike_count/static/index.html', code=307)
	credentials = flow.credentials

	conn = sqlite3.connect(settings.user_secrets_file)
	with conn:
		conn.execute('INSERT INTO token(json) VALUES (?)', (credentials.to_json(),))
	conn.close()

	return flask.redirect('/dislike_count/static/success.html', code=307)
