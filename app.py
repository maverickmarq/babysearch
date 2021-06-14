'''
This is the main module
'''
import os
import json
import requests
import urllib
import datetime
import paramiko
import threading
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS, cross_origin


APP = Flask(__name__, static_url_path='/static')
CORS(APP)

BASE_URL = os.getenv('BASE_URL', 'http://example.com/')
HOME_BASE = os.getenv('HOME_BASE', 'http://example.com/')
DATABASE_URL = os.getenv('DATABASE_URL', 'http://example.com/')

HOST = os.getenv('HOST', 'https://example.com')
HOST_SSH_PORT = os.getenv('HOST_SSH_PORT', 22)
HOST_PATH = os.getenv('HOST_PATH', '/docker/babysearch/')
HOST_USER = os.getenv('HOST_USER', 'admin')
HOST_PASS = os.getenv('PASS', 'admin')

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
    '0': 'Nothing',
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
    elif term.startswith('magnet:'):
        return add_magnet(term)
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
    
    if not query:
        return render_template('baby.html', existing = get_existing()), 200
    if not cat:
        return render_template('baby.html', existing = get_existing()), 200

    return lucky_search(query_json(query, cat))

@APP.route('/reset', methods=['GET'])
def reset_baby_search():
    thread = threading.Thread(target=my_threaded_func)
    thread.start()
    return render_template('baby.html', message="Rebooting..."), 200

def my_threaded_func():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.3', username='root', password='123Calvin@', port=22456)
    print("connected")
    ssh.exec_command('cd /volume1/docker/babysearch')
    print("changed dir")
    ssh.exec_command('sudo ./code')
    print("sent restart")
    
def query_json(term, cat):
    torrents = requests.get(format_url(term, cat)).json()
    return add_magnets(torrents)

def format_url(term, cat):
    return BASE_URL + 'q.php?q=' + term + "&cat=" + cat

def add_magnets(torrents):
    for t in torrents:
        t["magnet"] = "magnet:?xt=urn:btih:" + t['info_hash'] + "&dn=" + urllib.parse.quote(t['name']) + "&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2F9.rarbg.me%3A2850%2Fannounce&tr=udp%3A%2F%2F9.rarbg.to%3A2920%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969%2Fannounce"
        t["size"] = round(int(t["size"])/1024/1024/1024, 3)
        t["added"] = datetime.datetime.fromtimestamp(int(t["added"])).strftime('%c')
        t["category"] = cats[t["category"]]

    return torrents

def add_magnet(mag):
    requests.post(url = HOME_BASE, data = json.dumps(get_body(mag)), headers = get_header())
    return render_template('baby.html', existing = get_existing()), 200

def lucky_search(torrents):
    if type(torrents) is not list:
        return render_template('baby.html', message = torrents, existing = get_existing()), 200

    requests.post(url = HOME_BASE, data = json.dumps(get_body(torrents[0]['magnet'])), headers = get_header())
    return render_template('baby.html', existing = get_existing()), 200

def get_body(filename):
    return { "method" : "torrent-add", "arguments" : { "filename" : filename }}

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
