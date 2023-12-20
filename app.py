# Generates quizzes based on a given artist

# import necessary modules
import time
import json
import os
import spotipy

from spotipy.oauth2 import SpotifyOAuth
from answer_generation import *
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

# route to render quiz selection page
@app.route('/quizSelection')
def quiz_selection():
    top_artists = get_top_artists() # get top 5 artists name, id, and image
    return render_template('quiz_select.html', top_artists=top_artists)

#   tbd
#   arguments:
#   id = spotify artist id
@app.route('/quiz/<string:id>')
def quiz(id):
    questions = generate_questions(id)
    return questions

#   converts spotify artist url to artist id
#   arguments:
#   artist_url = spotify artist url
@app.route('/urlToId', methods=['POST'])
def grab_url():
    artist_url = request.form.get('artist_url')
    return artist_url

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

def generate_questions(artist_id):
    # Boilerplate Spotify authorization 
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")
    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Get artist data
    artist_info = sp.artist(artist_id)
    albums = sp.artist_albums(artist_id, album_type='album')
    top_tracks = sp.artist_top_tracks(artist_id)
    user_top_tracks = sp.current_user_top_tracks(limit=10, time_range='long_term')
    artist = {
        'artist_info': artist_info,
        'albums': albums,
        'top_tracks': top_tracks, 
        'user_top_tracks': user_top_tracks
        }  # Store all data needed or answers in one artist list

    # Load in questions
    with open('questions.json', 'r') as file:
        questions = json.load(file)

    # Replace artist_questions placeholders
    for artist_question in questions["artist_questions"]:
        artist_name = artist['artist_info']['name']
        artist_question["question"] = artist_question["question"].replace("<artist>", artist_name)
    
    # Generate answers for all questions
    generate_artist_answers(artist, questions)
    generate_album_answers(artist, questions)

    return questions

app.run(debug=True)