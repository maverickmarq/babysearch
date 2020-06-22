'''
This is the main module
'''
import os
import json
import requests
import re
import time
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

APP = Flask(__name__, static_url_path='/static')
CORS(APP)

BASE_URL = os.getenv('BASE_URL', 'http://example.com/')
HOME_BASE = os.getenv('HOME_BASE', 'http://example.com/')

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

@APP.route('/', methods=['GET', 'POST'])
def default_baby_search():
    term = request.form.get('term')
    
    if not term:
        return render_template('baby.html'), 200    
    else:
        url = BASE_URL + '/search/' + term
        print(url)
        lucky = request.form.get('lucky')
        if not lucky:
            return render_template('baby-search.html',torrents = baby_parse_page(url)), 200
        else:
            return lucky_search(baby_parse_page(url))

def lucky_search(torrents):
    transmission = requests.get(HOME_BASE)
    sessionId = transmission.headers.get('X-Transmission-Session-Id')
   
    header = { 'X-Transmission-Session-Id' : sessionId }
    body = { "method" : "torrent-add", "arguments" : { "filename" : torrents[0]['magnet'] }}
    r = requests.post(url = HOME_BASE, data = json.dumps(body), headers = header)
    return jsonify(r.json()), 200


@APP.route('/download/', methods=['POST'])
def download_baby_search():
    magnets = []
    torrents = request.form.getlist('download')
   
    transmission = requests.get(HOME_BASE)
    sessionId = transmission.headers.get('X-Transmission-Session-Id')
   
    header = { 'X-Transmission-Session-Id' : sessionId }
    body = { "method" : "torrent-add" }

    addRequest = []

    for t in torrents:
        b = body
        b.update({ "arguments" : { "filename" : t } })
        print(b)
        r = requests.post(url = HOME_BASE, data = json.dumps(b), headers = header)
        addRequest.append(r.json())
    return jsonify(addRequest), 200

def baby_parse_page(url, sort=None):
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    
    driver.get(url)
    delay = 25 # seconds
    try:
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID,'torrents')))
        soup = BeautifulSoup(driver.page_source, 'lxml')
    except TimeoutException:
        return "Could not load search results!"
    
    '''
    This function parses the page and returns list of torrents
    '''
    titles = parse_titles(soup)
    magnets = parse_magnet_links(soup)
    times = parse_times(soup)
    seeders, leechers = parse_seed_leech(soup)
    cat, subcat = parse_cat(soup)
    torrents = []
    for torrent in zip(titles, magnets, times, seeders, subcat):
        torrents.append({
            'title': torrent[0],
            'magnet': torrent[1],
            'time': convert_to_date(torrent[2]),
            'seeds': int(torrent[3]),
            'subcat': torrent[4]
        })

    if sort:
        sort_params = sort.split('_')
        torrents = sorted(torrents, key=lambda k: k.get(sort_params[0]), reverse=sort_params[1].upper() == 'DESC')

    return torrents

def parse_magnet_links(soup):
    '''
    Returns list of magnet links from soup
    '''
    magnets = soup.find('ol', {'id': 'torrents'}).find_all('a', href=True)
    magnets = [magnet['href'] for magnet in magnets if 'magnet' in magnet['href']]
    return magnets


def parse_titles(soup):
    '''
    Returns list of titles of torrents from soup
    '''
    titles = soup.find_all(class_='list-item item-name item-title')
    titles[:] = [title.get_text() for title in titles]
    return titles


def parse_links(soup):
    '''
    Returns list of links of torrents from soup
    '''
    links = soup.find_all(class_='list-item item-name item-title')
    links = [link.find_all('a', href=True) for link in links ]
    links[:] = [link[0]['href'] for link in links]
    return links


def parse_sizes(soup):
    '''
    Returns list of size from soup
    '''
    sizes = soup.find_all(class_='list-item item-size')
    sizes[:] = [size.get_text() for size in sizes]

    return sizes

	
def parse_times(soup):
    '''
    Returns list of time from soup
    '''
    times = soup.find_all(class_='list-item item-uploaded')
    times[:] = [time.get_text() for time in times]

    return times


def parse_uploaders(soup):
    '''
    Returns list of uploader from soup
    '''
    uploaders = soup.find_all(class_='list-item item-user')
    uploaders[:] = [uploader.get_text() for uploader in uploaders]

    return uploaders


def parse_seed_leech(soup):
    '''
    Returns list of numbers of seeds and leeches from soup
    ''' 
    seeders = soup.find_all(class_='list-item item-seed')
    seeders[:] = [seeder.get_text() for seeder in seeders]

    leechers = soup.find_all(class_='list-item item-leech')
    leechers[:] = [leecher.get_text() for leecher in leechers]

    return seeders, leechers


def parse_cat(soup):
    '''
    Returns list of category and subcategory
    '''
    cat_subcat = soup.find_all(class_='list-item item-type')
    cat = [cat.find_all('a', href=True)[::2] for cat in cat_subcat ]
    subcat = [subcat.find_all('a', href=True)[1::2] for subcat in cat_subcat ]
    
    cat[:] = [c[0].get_text() for c in cat]
    subcat[:] = [s[0].get_text() for s in subcat]
    
    return cat, subcat


def convert_to_bytes(size_str):
    '''
    Converts torrent sizes to a common count in bytes.
    '''
    size_data = size_str.split()

    multipliers = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']

    size_magnitude = float(size_data[0])
    multiplier_exp = multipliers.index(size_data[1])
    size_multiplier = 1024 ** multiplier_exp if multiplier_exp > 0 else 1

    return size_magnitude * size_multiplier


def convert_to_date(date_str):
    '''
    Converts the dates into a proper standardized datetime.
    '''
    date_format = None

    if re.search('^[0-9]+ min(s)? ago$', date_str.strip()):
        minutes_delta = int(date_str.split()[0])
        torrent_dt = datetime.now() - timedelta(minutes=minutes_delta)
        date_str = '{}-{}-{} {}:{}'.format(torrent_dt.year, torrent_dt.month, torrent_dt.day, torrent_dt.hour, torrent_dt.minute)
        date_format = '%Y-%m-%d %H:%M'

    elif re.search('^[0-9]*-[0-9]*\s[0-9]+:[0-9]+$', date_str.strip()):
        today = datetime.today()
        date_str = '{}-'.format(today.year) + date_str
        date_format = '%Y-%m-%d %H:%M'
    
    elif re.search('^Today\s[0-9]+\:[0-9]+$', date_str):
        today = datetime.today()
        date_str = date_str.replace('Today', '{}-{}-{}'.format(today.year, today.month, today.day))
        date_format = '%Y-%m-%d %H:%M'
    
    elif re.search('^Y-day\s[0-9]+\:[0-9]+$', date_str):
        today = datetime.today() - timedelta(days=1)
        date_str = date_str.replace('Y-day', '{}-{}-{}'.format(today.year, today.month, today.day))
        date_format = '%Y-%m-%d %H:%M'

    else:
        date_format = '%Y-%m-%d'

    return datetime.strptime(date_str, date_format)
