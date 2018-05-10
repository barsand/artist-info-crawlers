import requests
import time


class DeezerCrawler():
    def __init__(self):
        self.api_url = 'https://api.deezer.com/'
        self._name2id = {}
        self._id2name = {}

    def update_conversion_dicts(self, artist_name, artist_id):
        if not artist_name in self._name2id:
            self._name2id[artist_name] = artist_id

        if not artist_id in self._id2name:
            self._id2name[artist_id] = artist_name

    def name2id(self, artist_name):
        # TODO: consider using https://github.com/seatgeek/fuzzywuzzy
        artist_name = str.lower(artist_name)
        try:
            url = self.api_url + 'search/artist?q=' + artist_name
            res = requests.get(url)
            res_status = res.status_code

            if res_status != 200:
                return res_status, None

            if len(res.json()['data']):
                crawled_artists = res.json()['data']
                for crawled_artist in crawled_artists:
                    if str.lower(crawled_artist['name']) == artist_name:
                        self.update_conversion_dicts(crawled_artist['name'],
                                                     crawled_artist['id'])
                        return res_status, crawled_artist['id']

            else:
                return None, 'no results.'

        except Exception as e:
            return None, e

    def id2related(self, artist_id):
        try:
            url = self.api_url + 'artist/' + artist_id + '/related'
            res = requests.get(url)
            res_status = res.status_code
            if res_status != 200:
                return res_status, None

            if len(res.json()['data']):
                related_artists = [(a['name'], a['id'])
                                   for a in res.json()['data']]
                related_ids = []
                for artist_name, artist_id in related_artists:
                    self.update_conversion_dicts(artist_name, artist_id)
                    related_ids.append(artist_id)

                return res_status, related_ids

            else:
                return None, 'no results.'



        except Exception as e:
            return None, e
