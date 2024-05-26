from flask import Flask, request, session, redirect, render_template, url_for, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from answer_generation import fill_out_answers

# Create a Flask app instance
app = Flask(__name__)

# Set secret key for session management
app.secret_key = os.environ.get('SECRET_KEY')

# Retrieve Spotify API credentials from environment variables
SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = 'http://localhost:5000/callback'

# Spotipy authentication scope (determine what permissions your app needs)
SCOPE = 'user-top-read'

# Define a route to render the home page
@app.route('/')
def home():
    return render_template('index.html')

# Define a route to initiate Spotify authentication
@app.route('/login')
def login():
    # Create a SpotifyOAuth instance with client credentials and redirect URI
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
    )
    # Get the authorization URL for Spotify authentication
    auth_url = sp_oauth.get_authorize_url()
    # Redirect the user to the authorization URL
    return redirect(auth_url)

# Define a route to handle the callback from Spotify after successful authentication
@app.route('/callback')
def callback():
    # Get the authorization code from the query parameters
    code = request.args.get('code')
    # Create a SpotifyOAuth instance with client credentials and redirect URI
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
    )
    # Exchange the authorization code for an access token
    token_info = sp_oauth.get_access_token(code)
    # Store the token information in the session
    session['token_info'] = token_info
    # Redirect the user to the profile page
    return redirect('/profile')

# Define a route to display the user's profile information
@app.route('/profile')
def profile():
    # Retrieve token information from the session
    token_info = session.get('token_info', None)
    # If token information is not available, redirect the user to the login page
    if not token_info:
        return redirect('/login')
    
    # Extract the access token from the token information
    access_token = token_info['access_token']
    # Create a Spotify client with the access token
    sp = spotipy.Spotify(auth=access_token)
    # Retrieve the user's profile information
    user_info = sp.current_user()
    
    # Get the user's top 5 recent artists
    top_artists = sp.current_user_top_artists(limit=5, time_range='short_term')

    return render_template('quiz_select.html', user_info=user_info, top_artists=top_artists['items'])

@app.route('/quiz/<artist_uri>')
def quiz(artist_uri):
    # Retrieve token information from the session
    token_info = session.get('token_info', None)
    # If token information is not available, redirect the user to the login page
    if not token_info:
        return redirect('/login')
    
    # Extract the access token from the token information
    access_token = token_info['access_token']
    # Create a Spotify client with the access token
    sp = spotipy.Spotify(auth=access_token)

    # Get artist information
    artist_info = sp.artist(artist_uri)

    # Extract Spotify URL from artist information
    spotify_url = artist_info['external_urls']['spotify']

    quiz_data = fill_out_answers(sp,artist_info['id'])

    # Store the quiz data in the session
    session['quiz_data'] = quiz_data

    return render_template('quiz.html',quiz_data=quiz_data)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    user_answers = {}
    quiz_data = session.get('quiz_data', [])

    for question in quiz_data:
        question_id = question['id']
        selected_answer = request.form.get(f'question_{question_id}')
        user_answers[question_id] = selected_answer

    # Compare user answers with the correct answers
    correct_count = 0
    total_questions = len(quiz_data)
    results = []
    for question in quiz_data:
        question_id = question['id']
        correct_answer = next((ans for ans in question['answers'] if ans['correct']), None)
        user_answer = user_answers.get(question_id)
        is_correct = user_answer == correct_answer['answer']
        if is_correct:
            correct_count += 1
        results.append({
            'question_id': question_id,
            'user_answer': user_answer,
            'correct_answer': correct_answer['answer'],
            'is_correct': is_correct
        })

    # Calculate the percentage score
    score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0

    return render_template('results.html', results=results, correct_count=correct_count, total_questions=total_questions, score_percentage=score_percentage)


@app.route('/process_input', methods=['POST'])
def process_input():
    search_text = request.form['input_field']
    # Redirect to the route with input as argument
    return redirect(url_for('search_artist', artist_name=search_text))

@app.route('/search/<artist_name>')
def search_artist(artist_name):
    # Retrieve token information from the session
    token_info = session.get('token_info', None)
    # If token information is not available, redirect the user to the login page
    if not token_info:
        return redirect('/login')
    
    # Extract the access token from the token information
    access_token = token_info['access_token']
    # Create a Spotify client with the access token
    sp = spotipy.Spotify(auth=access_token)

    # Search for the artist using the provided string
    results = sp.search(q=artist_name, type='artist', limit=10)

    print(results)
    # Extract artist information from the search results
    artists = []
    for item in results['artists']['items']:
        if 'images' in item and item['images']:
            artists.append({
                'name': item['name'],
                'img': item['images'][0]['url'],
                'uri': item['uri']
            })

    # Render the template with the artist information
    return render_template('search.html', artists=artists, search=artist_name)

# Run the app if this script is executed
if __name__ == '__main__':
    app.run(debug=True)
