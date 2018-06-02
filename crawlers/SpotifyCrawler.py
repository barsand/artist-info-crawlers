from collections import deque
from argparse import ArgumentParser
from base64 import b64encode
import requests
import _thread
import urllib
import json
import time

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

    def __init__(self, crawler_id, outpfx, crawler_keys,
                 should_flush_conversion=True):
        self.ACCESS_TOKEN = None
        self.should_flush_conversion = should_flush_conversion
        self.id2name_outpath = outpfx + '-id2name.txt'
        open(self.id2name_outpath, 'w').close()
        self.crawler_keys = json.loads(open(crawler_keys).read())

        self.client_id = self.crawler_keys[crawler_id]['id']
        self.client_secret = self.crawler_keys[crawler_id]['secret']


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

        if flush_flag == 2 and self.should_flush_conversion:
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

    def id2artist_info(self, artist_ids):
        try:
            res = self.get('artists/?ids=' + ','.join(artist_ids))
            res_status = res.status_code

            if res_status == 200:
                artists_infos = res.json()['artists']
                return res_status, artists_infos

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
                              help='crawler id in the specified CRAWLER_KEYS',
                              required=True)

        required.add_argument('-i', dest='inputpath', metavar='PATH',
                              help='input artist names path', required=False)

        required.add_argument('-o', dest='outpfx', metavar='PATH PFX',
                              help='data output prefix file path',
                              required=True)

        required.add_argument('-a', dest='artist_name', metavar='NAME',
                              help='artist name to build the related net from',
                              required=False)


        return parser.parse_args()

    def save_artist_info(outpfx, data):
        try:
            outfile = open(outpfx + INFO_SUFFIX, 'a')
            outfile.write(json.dumps(data)  + '\n')
            outfile.close()
            return True

        except Exception as e:
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
            return False, e

    def create_artist_related_net(crawler_id, artist_name, outpfx):
        sc = SpotifyCrawler(crawler_id, outpfx)
        open(outpfx + INFO_SUFFIX, 'w').close()
        open(outpfx + RELATED_SUFFIX, 'w').close()
        # successfully_exported_info_ids = set()
        successfully_exported_related_ids = set()

        status, artist_info = sc.name2artist_info(artist_name)

        if status != 200:
            return

        print('starting from: ' + artist_info['name'])

        next_artist_ids = deque()
        next_artist_ids.append(artist_info['id'])
        count = 0

        while(len(next_artist_ids)):
            if count % 100 == 0:
                queue_bkp = open(outpfx + '-log.txt', 'w')
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

    def crawl_id_list(crawler_id, idlist_path, outpfx, crawler_keys):
        sc = SpotifyCrawler(crawler_id, outpfx, crawler_keys)
        artist_ids = list(set(open(idlist_path).read().splitlines()))
        outpath = outpfx + '-artist-info.txt'
        open(outpath, 'w').close()

        len_artist_ids = len(artist_ids)
        chunk_size = 50  # spotify allows up to 50 ids to be fetched per request

        for i in range(0, len_artist_ids, chunk_size):
            artist_id_chunk = artist_ids[i:i+chunk_size]
            status, res = sc.id2artist_info(artist_id_chunk)

            if status != 200: continue

            # import ipdb; ipdb.set_trace()

            outfile = open(outpath, 'a')
            for artist in res:
                data = [
                    artist['id'],
                    artist['name'],
                    str(artist['popularity']),
                ]

                try:
                    data.append(str(artist['followers']['total']))
                except:
                    data.append('N/A')

                data.append(json.dumps(artist['genres']))

                outfile.write('\t'.join(data) + '\n')
            outfile.close()

            print(str(int(((i+chunk_size)/len_artist_ids) * 100)) + '%')



    def run():
        args = get_arguments()

        # if not args.artist_name:
        #     print('must provide artist_name to perform BFS crawling')
        #     exit()
        # create_artist_related_net(args.crawler_id, args.artist_name,
        #                           args.outpfx + '-' + args.artist_name)


        crawl_id_list(args.crawler_id, args.inputpath, args.outpfx,
                      args.crawler_keys)

    run()