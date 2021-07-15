'''
This is the main module
'''
import datetime
import json
import os
import re
import urllib

import requests
from flask import Flask, render_template, request
from pathlib import Path

app = Flask(__name__, static_url_path='/static')
# CORS(app)

BASE_URL = os.getenv('BASE_URL', 'http://example.com/')
HOME_BASE = os.getenv('HOME_BASE', 'http://example.com/')
DATABASE_URL = os.getenv('DATABASE_URL', 'http://example.com/')
TRANSMISSION_DOWNLOAD_DIR = os.getenv('TRANSMISSION_DOWNLOAD_DIR', '/downloads')

JSONIFY_PRETTYPRINT_REGULAR = True

global search_results

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
    '0': 'All',
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

@app.route('/', methods=['GET', 'POST'])
def default_baby_search():
    term = request.form.get('term')

    if not term:
        return render_baby()
    else:
        cat = request.form.get('cat')
        lucky = request.form.get('lucky')

        get_torrents(term,cat)

        if not lucky:
            return render_baby()
        else:
            return lucky_search(get_results())


@app.route('/search', methods=['GET'])
def search_baby_search():
    query = request.args.get('q')
    cat = request.form.get('cat')

    return lucky_search(get_torrents(query, cat))


def query_json(term, cat):
    torrents = requests.get(format_url(term, cat)).json()
    return add_magnets(torrents)


def format_url(term, cat):
    return BASE_URL + 'q.php?q=' + term + "&cat=" + cat


def add_magnets(torrents):
    for t in torrents:
        t["magnet"] = "magnet:?xt=urn:btih:" + t['info_hash'] + "&dn=" + urllib.parse.quote(t['name'])
        t["size"] = round(int(t["size"]) / 1024 / 1024 / 1024, 3)
        t["added"] = datetime.datetime.fromtimestamp(int(t["added"])).strftime('%c')
        t["category"] = cats[t["category"]]

    return torrents


def lucky_search(torrents):
    if type(torrents) is not list:
        return render_baby()

    body = {"method": "torrent-add", "arguments": {"filename": torrents[0]['magnet']}}


    requests.post(url=HOME_BASE, data=json.dumps(body), headers=get_header())
    return render_baby()


def get_header():
    transmission = requests.get(HOME_BASE)
    session_id = transmission.headers.get('X-Transmission-Session-Id')

    return {'X-Transmission-Session-Id': session_id}


def get_existing():
    body = {"arguments": {"fields": ["id", "name", "percentDone"]}, "method": "torrent-get"}
    existing = requests.post(url=HOME_BASE, data=json.dumps(body), headers=get_header()).json()
    if existing.get('arguments').get('torrents'):
        return existing
    else:
        return None


def get_torrents(term, cat):
    if not term:
        return None
    if not cat:
        cat = '0'
    global search_results
    search_results = query_json(term, cat)
    return search_results


def get_results():
    try:
        global search_results
        return search_results
    except NameError:
        return None


def render_baby():
    return render_template('baby.html', torrents=get_results(), existing=get_existing()), 200


@app.route('/edit/', methods=['POST'])
def edit_existing():
    clear = request.form.get("clearExisting")
    body = {"arguments": {"ids": [int(clear)]}, "method": "torrent-remove"}

    requests.post(url=HOME_BASE, data=json.dumps(body), headers=get_header())
    return render_baby()

#something like this
@app.route('/download/', methods=['POST'])
def download_baby_search():
    magnet = request.form.get('magnet')
    cat = request.form.get('category')

    path = Path(TRANSMISSION_DOWNLOAD_DIR, str(cat))
    path.mkdir(parents=True, exist_ok=True)

    body = {"arguments": {"filename": magnet, "download-dir": str(path) }, "method": "torrent-add"}
    requests.post(url=HOME_BASE, data=json.dumps(body), headers=get_header())

    return render_baby()


@app.route('/progress/<id>/', methods=['GET'])
def progress(id):
    torrents = get_existing().get('arguments').get('torrents')
    err = False
    for s in range(len(torrents)):
        pattern = r""+str(id)
        sequence = str(torrents[s].get('id'))
        if re.match(pattern, sequence):
            return str(torrents[s].get('percentDone'))
        else:
            err = True
    if err:
        return "69"
