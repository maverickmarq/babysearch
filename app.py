'''
This is the main module
'''
import os
import json
import requests
import urllib
import datetime
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS, cross_origin


APP = Flask(__name__, static_url_path='/static')
CORS(APP)

BASE_URL = os.getenv('BASE_URL', 'http://example.com/')
HOME_BASE = os.getenv('HOME_BASE', 'http://example.com/')
DATABASE_URL = os.getenv('DATABASE_URL', 'http://example.com/')

JSONIFY_PRETTYPRINT_REGULAR = True

# Translation table for sorting filters
sort_filters = {
    'title_asc': 1,
    'title_desc': 2,
    'time_desc': 3,
    'time_asc': 4,
    'size_desc': 5,
    'size_asc': 6,
    'seeds_desc': 7,
    'seeds_asc': 8,
    'leeches_desc': 9,
    'leeches_asc': 10,
    'uploader_asc': 11,
    'uploader_desc': 12,
    'category_asc': 13,
    'category_desc': 14
}

cats = {
    '101': 'Music',
    '102': 'Audio books',
    '103': 'Sound clips',
    '104': 'FLAC',
    '199': 'Music - Other',
    '201': 'Movies',
    '202': 'Movies DVDR',
    '203': 'Music videos',
    '204': 'Movie clips',
    '205': 'TV shows',
    '206': 'Handheld',
    '207': 'HD - Movies',
    '208': 'HD - TV shows',
    '209': '3D',
    '299': 'Video - Other',
    '301': 'Windows',
    '302': 'Mac',
    '303': 'UNIX',
    '304': 'Handheld',
    '305': 'IOS (iPad/iPhone)',
    '306': 'Android',
    '399': 'Other OS',
    '401': 'PC',
    '402': 'Mac',
    '403': 'PSx',
    '404': 'XBOX360',
    '405': 'Wii',
    '406': 'Handheld',
    '407': 'IOS (iPad/iPhone)',
    '408': 'Android',
    '499': 'Game - Other',
    '501': 'Movies',
    '502': 'Movies DVDR',
    '503': 'Pictures',
    '504': 'Games',
    '505': 'HD - Movies',
    '506': 'Movie clips',
    '599': 'Porn - Other',
    '601': 'E-books',
    '602': 'Comics',
    '603': 'Pictures',
    '604': 'Covers',
    '605': 'Physibles',
    '699': 'E-books - Other',
}

searchResults = None

@APP.route('/', methods=['GET', 'POST'])
def default_baby_search():
    term = request.form.get('term')

    if not term:
        return render_template('baby.html', existing = get_existing()), 200
    else:
        cat = request.form.get('cat')

        lucky = request.form.get('lucky')
        torrents = query_json(term, cat)

        if type(torrents) is not list:
            return render_template('baby.html', message = torrents, existing = get_existing()), 200

        if not lucky:
            return render_template('baby.html', torrents = torrents, existing = get_existing()), 200
        else:
            return lucky_search(torrents)


@APP.route('/search', methods=['GET'])
def search_baby_search():
    query = request.args.get('q')
    cat = request.form.get('cat')

    return lucky_search(query_json(query, cat))

def query_json(term, cat):
    torrents = requests.get(format_url(term, cat)).json()
    return add_magnets(torrents)

def format_url(term, cat):
    return BASE_URL + 'q.php?q=' + term + "&cat=" + cat

def add_magnets(torrents):
    for t in torrents:
        t["magnet"] = "magnet:?xt=urn:btih:" + t['info_hash'] + "&dn=" + urllib.parse.quote(t['name'])
        t["size"] = round(int(t["size"])/1024/1024/1024, 3)
        t["added"] = datetime.datetime.fromtimestamp(int(t["added"])).strftime('%c')
        t["category"] = cats[t["category"]]

    return torrents

def lucky_search(torrents):
    if type(torrents) is not list:
        return render_template('baby.html', message = torrents, existing = get_existing()), 200

    body = { "method" : "torrent-add", "arguments" : { "filename" : torrents[0]['magnet'] }}

    requests.post(url = HOME_BASE, data = json.dumps(body), headers = get_header())
    return render_template('baby.html', existing = get_existing()), 200

def get_header():
    transmission = requests.get(HOME_BASE)
    sessionId = transmission.headers.get('X-Transmission-Session-Id')

    return { 'X-Transmission-Session-Id' : sessionId }


def get_existing():
    body = { "arguments": { "fields": [ "id", "name", "percentDone" ]}, "method": "torrent-get"}
    existing = requests.post(url = HOME_BASE, data = json.dumps(body), headers = get_header()).json()
    if existing.get('arguments').get('torrents'):
        return existing
    else:
        return None

@APP.route('/edit/', methods=['POST'])
def edit_existing():
    clear = request.form.get("clearExisting")
    body = { "arguments": { "ids": [ int(clear) ] }, "method": "torrent-remove"}

    global searchResults
    requests.post(url = HOME_BASE, data = json.dumps(body), headers = get_header())
    return render_template('baby.html', torrents = searchResults, existing = get_existing())


@APP.route('/download/', methods=['POST'])
def download_baby_search():
    torrents = request.form.getlist('download')

    global searchResults
    for t in torrents:
        body = { "arguments" : { "filename" : t }, "method" : "torrent-add" }
        requests.post(url = HOME_BASE, data = json.dumps(body), headers = get_header())

    return render_template('baby.html', torrents = searchResults, existing = get_existing()), 200
