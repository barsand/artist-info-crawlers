from argparse import ArgumentParser
import requests
import time

class DeezerCrawler():
    def __init__(self, outpfx, should_flush_conversion=True):
        self.api_url = 'https://api.deezer.com/'
        self.should_flush_conversion = should_flush_conversion
        self.id2name_outpath = outpfx + '-id2name.txt'
        self._name2id = {}
        self._id2name = {}

    def update_conversion_dicts(self, artist_name, artist_id):
        flush_flag = 0

        artist_id = str(artist_id)

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
                        return res_status, crawled_artist

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

            import ipdb; ipdb.set_trace()

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

if __name__ == '__main__':
    def get_arguments():
        parser = ArgumentParser(description='Deezer artist info crawler that\
            fetches information to be compared with SpotifyCrawler output.')

        required = parser.add_argument_group('required arguments')

        required.add_argument('-i', dest='input_path', metavar='PATH',
                              help='path to list of itens to have its info\
                              crawled. content  should be mapping spotify ids\
                              to names.', required=True)

        required.add_argument('-o', dest='outpfx', metavar='PATH PFX',
                              help='data output prefix file path',
                              required=True)

        return parser.parse_args()

    def add_deezer_ids(names2spotify_ids, outpfx):
        # receives a list of spotify names mapped to respective ids and adds
        # deezer data to it
        dc = DeezerCrawler(outpfx, should_flush_conversion=False)
        input_siz = len(names2spotify_ids)
        str_input_siz = str(input_siz)
        count = 0

        outpath = outpfx + '-crawled-data.txt'
        logpath = outpfx + '-log.txt'
        open(outpath, 'w').close()
        open(logpath, 'w').close()

        for artist_name in names2spotify_ids:
            print('\n' + outpfx + ' crawling ' + artist_name)
            print('\t>' + str(count) + ' of ' + str_input_siz)
            count += 1

            try:
                status, res = dc.name2id(artist_name)
                assert status == 200
                f = open(outpath, 'a')
                f.write(names2spotify_ids[artist_name] + '\t' + artist_name)
                f.write('\t' + str(res['id']) + '\t' + res['name'] + '\n')
                f.close()

            except Exception as e:
                f = open(logpath, 'a')
                f.write('couldnt fetch data for ' + artist_name + '\n')
                f.close()

    def crawl_related_artists(artist_ids, outpfx):
        dc = DeezerCrawler(outpfx)
        input_siz = len(artist_ids)
        str_input_siz = str(input_siz)
        count = 0

        outpath = outpfx + '-crawled-related.txt'
        logpath = outpfx + '-log.txt'
        open(outpath, 'w').close()
        open(logpath, 'w').close()

        for artist_id in artist_ids:
            print('\n' + outpfx + ' crawling ' + artist_id)
            print('\t>' + str(count) + ' of ' + str_input_siz)
            count += 1

            try:
                status, res = dc.id2related(artist_id)
                import ipdb; ipdb.set_trace()
                assert status == 200
                f = open(outpath, 'a')
                f.write(names2spotify_ids[artist_name] + '\t' + artist_name)
                f.write('\t' + str(res['id']) + '\t' + res['name'] + '\n')
                f.close()

            except Exception as e:
                f = open(logpath, 'a')
                f.write('couldnt fetch data for ' + artist_name + '\n')
                f.close()

    args = get_arguments()

    # add_deezer_ids({
    #     l.split('\t')[1]: l.split('\t')[0]
    #     for l in open(args.input_path).read().splitlines()
    # }, args.outpfx)

    crawl_related_artists(open(args.input_path).read().splitlines(),
                          args.outpfx)