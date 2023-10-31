# Generates quizzes based on a given artist

# import necessary modules
import time
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template

# initialize Flask app
app = Flask(__name__)

# set the name of the session cookie
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

# set a random secret key to sign the cookie
app.secret_key = os.getenv("COOKIE_SECRET")

# set the key for the token info in the session dictionary
TOKEN_INFO = 'token_info'

# route to handle logging in
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    # create a SpotifyOAuth instance and get the authorization URL
    auth_url = create_spotify_oauth().get_authorize_url()
    # redirect the user to the authorization URL
    return redirect(auth_url)
    
# route to handle the redirect URI after authorization
@app.route('/redirect')
def redirect_page():
    # clear the session
    session.clear()
    # get the authorization code from the request parameters
    code = request.args.get('code')
    # exchange the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code)
    # save the token info in the session
    session[TOKEN_INFO] = token_info
    # redirect the user to the quiz_selection route
    return redirect(url_for('quiz_selection',_external=True))

# route to save the Discover Weekly songs to a playlist
@app.route('/quizSelection')
def quiz_selection():

    top_artists = get_top_artists()
    
    return render_template('quiz_select.html', top_artists=top_artists)
   # Get user's top 5 most listened to artists from medium_term
   # Strip the JSON down to just artist, image, and ID
   # return JSON

# function to get the token info from the session
def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        # if the token info is not found, redirect the user to the login route
        redirect(url_for('login', _external=False))
    
    # check if the token is expired and refresh it if necessary
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv("CLIENT_ID"),
        client_secret = os.getenv("CLIENT_SECRET"),
        redirect_uri = url_for('redirect_page', _external=True),
        scope='user-top-read '
    )

def get_top_artists():
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")

    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # get top 5 artists for user in the last 6 months
    top_artists_data = sp.current_user_top_artists(limit = 5)

    # create dictionary that will be returned 
    top_artists = []

    # iterate over artists and add only name, id, and image to top_artists
    for artist in top_artists_data['items']:
        artist_name = artist['name']
        artist_id = artist['id']    
        # if artist has an image, get the first one
        if (len(artist['images']) != 0):
            artist_image = artist['images'][0]['url']
        else:   # if artist doesn't have an image, return empty string
            artist_image = ''   

        # append artist dictionary to list of top 5
        top_artists.append({
        'name': artist_name,
        'id': artist_id,
        'image': artist_image
        })
    
    return top_artists

app.run(debug=True)