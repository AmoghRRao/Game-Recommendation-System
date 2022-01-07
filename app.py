from flask import Flask, url_for, request, render_template, redirect
import pandas as pd
from pandas.io import pickle
import requests
import json
import pickle

app = Flask(__name__, static_folder='static')
df = pd.read_csv('Windows_info_complete.csv')


@app.route('/')
def home():
    games = df['titles'].values
    return render_template("index.html", games=games)


@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['search']
    return redirect(url_for('game_recomend_page', game_name=text))


@app.route('/<game_name>', methods=['POST'])
def search_from_recommend_page(game_name):
    text = request.form['search']
    return redirect(url_for('game_recomend_page', game_name=text))


@app.route('/<game_name>', methods=['POST', 'GET'])
def game_recomend_page(game_name):

    game_index = df[df['titles'] == game_name].index[0]
    game_id = int(df.iloc[game_index].id)
    game_summary = df.iloc[game_index].summary
    game_story = df.iloc[game_index].storyline if not str(
        df.iloc[game_index].storyline) == 'nan' else ''
    genre = df.iloc[game_index].genres
    recommendation_data = get_recomendation(game_index)
    cover_image = get_game_info(game_id)
    game_data = {'cover_image': cover_image,
                 'game_title': game_name, 'game_summary': game_summary, 'game_story': game_story, 'genre': genre}

    games = df['titles'].values
    return render_template('games.html', game_data=game_data, recommendation_data=recommendation_data, keys=list(recommendation_data.keys()), games=games)


def get_recomendation(ids):
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    distance = similarity[ids]
    game_list = sorted(list(enumerate(distance)),
                       reverse=True, key=lambda x: x[1])[1:6]
    recomendations = {}
    for i in game_list:
        cover_url = get_game_info(int(df.iloc[i[0]].id))
        recomendations[df.iloc[i[0]].titles] = [
            int(df.iloc[i[0]].id), cover_url]
    return recomendations


def get_game_info(ids):
    client_id = "w1fyitudqawwvjzj2ucnyylud40ce9"
    client_secret = "5vm3uutzy08x9755hmknlwt336pptq"
    url = f'https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials'
    x = requests.post(url)
    details = json.loads(x.text)
    access_token = details['access_token']
    cover_url = 'https://api.igdb.com/v4/covers'
    header = {'Client-ID': client_id,
              'Authorization': f'Bearer {access_token}'}

    x = requests.post(cover_url, headers=header, data=(
        f'fields *; where game = ({ids});').encode('utf-8'))

    if x.status_code == 500:
        return

    cover_info = json.loads(x.text)
    return cover_info[0]['url'].replace('thumb', 'cover_big')


if __name__ == "__main__":
    app.run(debug=False, threaded=True)