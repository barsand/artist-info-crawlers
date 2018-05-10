import sys
import datetime
from SpotifyCrawler import SpotifyCrawler as SC
import json

sc = SC(sys.argv[3])

outpath = sys.argv[2] + '-spotify_names2ids' + '.txt'
open(outpath, 'w').close()

logpath = sys.argv[2] + '-log-spotify.txt'
open(logpath, 'w').close()

timestamp = str(datetime.datetime.now())
artists = open(sys.argv[1], 'r').read().splitlines()
len_artists_str = str(len(artists))


count = 0
for name in artists:
    count += 1
    print('\nartist_id fetching started @' + sys.argv[2] + ':\t' + timestamp)
    print('Fetching spotify id ' + str(count) + ' of ' + len_artists_str + ' for\t' + name)
    try:
        res = sc.name2id(name)
        import ipdb; ipdb.set_trace()
        if res[0] is not None:
            f = open(outpath, 'a')
            f.write(name + '\t' + str(res[1]) + '\n')
            f.close()
            print('succes!')
        else:
            log = open(logpath, 'a')
            log.write('ERROR fetching\t' + name + '\n')
            log.close()
            print('failed!')
    except Exception as e:
        log = open(logpath, 'a')
        log.write('ERROR with request\t' + name + ': ' + str(e) + '\n')
        log.close()
        print('failed!')


id_list = [x.split('\t')[1] for x in open(outpath).read().splitlines()]
len_id_list_str = str(len(id_list))

outpath = sys.argv[2] + '-spotify_ids2related' + '.txt'
open(outpath, 'w').close()


count = 0
for name in id_list:
    count += 1
    print('\nartist_related fetching started @' + sys.argv[2] + ':\t' + timestamp)
    print('Fetching spotify related ' + str(count) + ' of ' + len_artists_str + ' for\t' + name)
    try:
        res = sc.id2related(name)
        if res[0] is not None:
            f = open(outpath, 'a')
            f.write(name + '\t' + str(res[1]) + '\n')
            f.close()
            print('succes!')
        else:
            log = open(logpath, 'a')
            log.write('ERROR fetching\t' + name + '\n')
            log.close()
            print('failed!')
    except Exception as e:
        log = open(logpath, 'a')
        log.write('ERROR with request\t' + name + ': ' + str(e) + '\n')
        log.close()
        print('failed!')
