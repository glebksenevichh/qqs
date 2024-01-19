# Generates quizzes based on a given artist

# import necessary modules
import time
import os
import spotipy
import answer_generation

from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template, flash

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
    session.clear()                                             # clear the session
    code = request.args.get('code')                             # get the authorization code from the request parameters
    token_info = create_spotify_oauth().get_access_token(code)  # exchange the authorization code for an access token and refresh token
    session[TOKEN_INFO] = token_info                            # save the token info in the session
    return redirect(url_for('quiz_selection',_external=True))   # redirect the user to the quiz_selection route

 # route to render quiz selection page
@app.route('/quizSelection')
def quiz_selection():
    top_artists = get_top_artists()                                         # get top 5 artists name, id, and image
    return render_template('select.html', top_artists=top_artists)     # display the page with top_artists as an argument

@app.route('/quiz_redirect/<string:artist_id>')
def quiz_redirect(artist_id):
    
    # Check for valid input
    artist_id_valid = is_valid_artist(artist_id)

    if artist_id_valid:
        #If artist ID is valid, generate questions and pass them as an argument to /quiz
        questions = generate_answers(artist_id)

        ####
        return questions
        #return redirect(url_for('quiz', quiz_questions=questions))
        ####
    else:
        #If artist ID is invalid, send a flash message and redirect to same page
        flash('Invalid URL. Please input a valid Spotify Artist URL.')  # Flash a message
        return redirect(url_for('quiz_selection'))                      # Redirect to the quiz_selection route

@app.route('/quiz')
def quiz_page():
    #Retrieves quiz questions as an argument from quiz_redirect redirect
    quiz_questions = request.args.get('quiz_questions')

    return render_template('quiz.html')

# uses spotify to check if the argument is a valid spotify artist id
# argument:
# string artist_id
# returns:
# boolean: true if artist ID corresponds to a spotify artist (is valid), false if not.
def is_valid_artist(artist_id):
    try: 
        # get the token info from the session
        token_info = get_token()
    except:
        # if the token info is not found, redirect the user to the login route
        print('User not logged in')
        return redirect("/")
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    if(artist_id == 'invalid'):         #ID will be set to 'invalid' if it is such
        #print(f"URL is not valid.")     
        return False                    
    try:
        # Attempt to retrieve information about the artist
        artist_info = sp.artist(artist_id)
        if artist_info:
            #print(f"Artist ID {artist_id} is valid. Artist name: {artist_info['name']}")
            return True
    except spotipy.SpotifyException as e:
        # Handle exceptions (e.g., invalid artist ID)
        print(f"Error: {e}")
    
    print(f"Artist ID {artist_id} is not valid.")
    return False

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

def generate_answers(artist_id):
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

    # fill out questions
    answers = fill_out_answers(sp, artist_id)

    return answers

app.run(debug=True)