from collections import deque
from argparse import ArgumentParser
from base64 import b64encode
import requests
import _thread
import urllib
import json
import time

CRAWLER_KEYS = None

ID2NAME = '-id2name.txt'
NAME2ID = '-name2id.txt'
INFO_SUFFIX = '-artist-info.txt'
RELATED_SUFFIX = '-artist-related.txt'


class SpotifyCrawler():
    def update_access_token(self):
    # uses crawler id information to fetch the token used on the HTTP requests
        url = 'https://accounts.spotify.com/api/token'
        res = requests.post(url, auth=(self.client_id, self.client_secret),
                            data={'grant_type': 'client_credentials'})
        # print (res.json())
        self.ACCESS_TOKEN = res.json()['access_token']
        return(res.json()['expires_in'] * 0.75)
        print('new token: ' + self.ACCESS_TOKEN)

    def periodically_refresh_access_token(self):
    # spotify uses the oauth2.0 method to authenticate users. an application
    # should be created on the spotify developers' area and will be used to
    # by the thread that keeps the token necessary to perform HTTP requests
    # updated.
        while True:
            time_until_next_update = self.update_access_token()
            time.sleep(time_until_next_update)

    def __init__(self, crawler_id, outpfx):
        self.ACCESS_TOKEN = None
        self.id2name_outpath = outpfx + '-id2name.txt'
        open(self.id2name_outpath, 'w').close()

        global CRAWLER_KEYS
        self.client_id = CRAWLER_KEYS[crawler_id]['id']
        self.client_secret = CRAWLER_KEYS[crawler_id]['secret']


        # we do this here in order to make sure the first request after the
        # class init is done and the first iteration of the token updating
        # thread is not done yet. basically, we are making sure that there will
        # be always an ACCESS_TOKEN.
        self.update_access_token()

        _thread.start_new_thread(self.periodically_refresh_access_token, ())

        self.api_url = 'https://api.spotify.com/v1/'
        self._name2id = dict()
        self._id2name = dict()

    def update_conversion_dicts(self, artist_name, artist_id):
        flush_flag = 0

        if not artist_name in self._name2id:
            self._name2id[artist_name] = artist_id
            flush_flag += 1

        if not artist_id in self._id2name:
            self._id2name[artist_id] = artist_name
            flush_flag += 1

        if flush_flag == 2:
            outfile = open(self.id2name_outpath, 'a')
            outfile.write(artist_id + '\t' + artist_name + '\n')
            outfile.close()


    def get(self, url):
        headers = {'Authorization': 'Bearer ' + self.ACCESS_TOKEN}
        return requests.get(self.api_url + url, headers=headers)

    def name2artist_info(self, artist_name):
        # fetches artist data using search endpoint
        # TODO: consider using https://github.com/seatgeek/fuzzywuzzy
        artist_name = str.lower(artist_name)
        try:
            res = self.get('search?type=artist&q=' + artist_name)
            res_status = res.status_code

            if res_status != 200:
                return res_status, None

            if len(res.json()['artists']['items']):
                crawled_artists = res.json()['artists']['items']
                for crawled_artist in crawled_artists:
                    if str.lower(crawled_artist['name']) == artist_name:
                        self.update_conversion_dicts(
                            crawled_artist['name'], crawled_artist['id']
                        )
                        return res_status, crawled_artist

            else:
                return None, 'no results.'

        except Exception as e:
            return None, e

    def id2artist_info(self, artist_id):
        try:
            res = self.get('artists/' + artist_id)
            res_status = res.status_code

            if res_status == 200:
                artist_info = res.json()
                self.update_conversion_dicts(artist_info['name'], artist_id)
                return res_status, artist_info

            else:
                return None, 'no results.'

        except Exception as e:
            return None, e

    def id2related(self, artist_id):
        try:
            res = self.get('artists/' + artist_id + '/related-artists')
            res_status = res.status_code

            if res_status != 200:
                return res_status, None

            res_json = res.json()
            if len(res_json['artists']):
                related_artists = [(a['name'], a['id'])
                                   for a in res_json['artists']]
                related_ids = []
                for artist_name, artist_id in related_artists:
                    self.update_conversion_dicts(artist_name, artist_id)
                    related_ids.append(artist_id)

                return res_status, res_json['artists']

            else:
                return None, 'no results.'

        except Exception as e:
            return None, e

if __name__ == '__main__':
    def get_arguments():
        parser = ArgumentParser(description='Spotify artist info crawler')

        required = parser.add_argument_group('required arguments')

        required.add_argument('-k', dest='crawler_keys', metavar='PATH',
                              help='crawler keys JSON file path', required=True)

        required.add_argument('-c', dest='crawler_id', metavar='ID',
                              help='crawler id in the CRAWLER_KEYS constant',
                              required=True)

        required.add_argument('-i', dest='inputpath', metavar='PATH',
                              help='input artist names path', required=True)

        required.add_argument('-o', dest='outpfx', metavar='PATH PFX',
                              help='data output prefix file path',
                              required=True)

        required.add_argument('-a', dest='artist_name', metavar='NAME',
                              help='artist name to build the related net from',
                              required=True)


        return parser.parse_args()

    def save_artist_info(outpfx, data):
        try:
            outfile = open(outpfx + INFO_SUFFIX, 'a')
            outfile.write(json.dumps(data)  + '\n')
            outfile.close()
            return True

        except Exception as e:
            # import ipdb; ipdb.set_trace()
            return False

    def save_artist_related(outpfx, artist_id, related_ids):
        try:
            outfile = open(outpfx + RELATED_SUFFIX, 'a')
            outfile.write(artist_id + '\t')
            outfile.write('\t'.join(related_ids))
            outfile.write('\n')
            outfile.close()
            return True

        except Exception as e:
            # import ipdb; ipdb.set_trace()
            return False, e

    def create_artist_related_net(crawler_id, artist_name, outpfx):
        sc = SpotifyCrawler(crawler_id, outpfx)
        open(outpfx + INFO_SUFFIX, 'w').close()
        open(outpfx + RELATED_SUFFIX, 'w').close()
        # successfully_exported_info_ids = set()
        successfully_exported_related_ids = set()

        status, artist_info = sc.name2artist_info(artist_name)

        # import ipdb; ipdb.set_trace()
        if status != 200:
            return

        print('starting from: ' + artist_info['name'])

        next_artist_ids = deque()
        next_artist_ids.append(artist_info['id'])
        count = 0

        while(len(next_artist_ids)):
            if count % 100 == 0:
                queue_bkp = open(outpfx + 'log', 'w')
                queue_bkp.write(str(next_artist_ids))
                queue_bkp.close()

            curr_id = next_artist_ids.popleft()
            if curr_id in successfully_exported_related_ids:
                continue

            print(curr_id + ' ' + sc._id2name[curr_id])
            # print(json.dumps(
            #     [sc._id2name[i] for i in successfully_exported_related_ids ],
            #     indent=2
            # ) + str(len(successfully_exported_related_ids)))

            status, res = sc.id2related(curr_id)

            if status != 200: continue

            related_ids = [artist['id'] for artist in res]

            success = save_artist_related(outpfx, curr_id, related_ids)
            if success:
                successfully_exported_related_ids.add(curr_id)
            else:
                print('\terror exporting related for ' + sc._id2name[curr_id])

            for artist_id in related_ids:
                next_artist_ids.append(artist_id)

            count += 1
            print('\t\t\tdone with iteration#.' + str(count))
            print('\t\t\tqueue size: ' + str(len(next_artist_ids)) + '\n')

    def run():
        args = get_arguments()
        global CRAWLER_KEYS
        CRAWLER_KEYS = json.loads(open(args.crawler_keys).read())
        create_artist_related_net(args.crawler_id, args.artist_name,
                                  args.outpfx + '-' + args.artist_name)

    run()