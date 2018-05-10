import argparse
import sys
import csv
import numpy as np
from scipy.sparse import csr_matrix, coo_matrix
import json
import copy
import ipdb
from collections import defaultdict
from scipy.stats import rankdata

def get_arguments():
    parser = argparse.ArgumentParser(
        description='Calculates cosing similarity using dataset obtained from\
        last.fm\n'
    )

    required = parser.add_argument_group('required arguments')
    required.add_argument('--song_hash', dest='song_hash', required=True)
    required.add_argument('--train', dest='train', required=True)
    required.add_argument('-o', dest='outpath', required=True)

    return parser.parse_args()

def related2ratio(data, artist2artistId, useCosine=False):
    #id2name = dict()
    name2id = json.loads(open(data['name2ids'], encoding="utf-8").read())
    id2artistId = dict()
    for name in name2id:
        try:
            id2artistId[name2id[name]] = artist2artistId[name]
        except:
            pass

    artistId2ratio = dict()
    with open(data['ids2related'], 'r') as file_in:
        for line in file_in:
            id_i, related = line.split('\t')
            related = related.strip().split(' ')
            n_related = len(related)
            if id_i in id2artistId:
                artistId_i = id2artistId[id_i]
                if useCosine:
                    unsorted_row = np.zeros(coMat.shape[1])
                    vals,inds = coMat[artistId_i,].nonzero()
                    unsorted_row[inds] = [-cosine(artistId_i,ind) for ind in inds]
                    rank = rankdata(unsorted_row, method='ordinal')
                else:
                    rank = rankdata(coMat[artistId_i,].todense(), method='ordinal')

                dcg = 0.0
                for id_j in related:
                    if id_j in id2artistId:
                        artistId_j = id2artistId[id_j]
                        dcg += 1.0/np.log2(rank[artistId_j]+1+1)

                artistId2ratio[artistId_i] = dcg

    return artistId2ratio

def cosine(i,j):
    return coMat[i,j]/np.sqrt(countsSq[i]*countsSq[j])



def run(args):
    # read files to create maps
    songId2artistId = dict()
    artist2artistId = dict()


    print('Reading song hash...',)
    # dataset/yes_small/song_hash.txt
    infile = open(args.song_hash,'r')
    for line in infile.read().splitlines():
        record = line.split('\t')
        songId = int(record[0])
        try:
            artist = record[2]
        except:
            import ipdb; ipdb.set_trace()
        if artist not in artist2artistId:
            artist2artistId[artist] = len(artist2artistId)
        songId2artistId[songId] = artist2artistId[artist]
    infile.close()
    print('\tdone.')


    n = len(artist2artistId)
    global coMat
    global countsSq
    print(str(n))
    #coMat = np.zeros((n,n))
    countsSq = np.zeros(n)

    pair2data = defaultdict(int)


    print('Reading train...',)
    # dataset/yes_small/train.txt
    with open(args.train,'r') as tsvin:
        tsvin = csv.reader(tsvin, delimiter=' ')
        for playlist in tsvin:
            counts = defaultdict(int)
            playlist = playlist[0:-1]
            for songId in playlist:
                sid = int(songId)
                if sid in songId2artistId:
                    counts[songId2artistId[sid]] += 1
            for k,v in counts.items():
                countsSq[k] += v*v
            artistIds = sorted(counts.keys())
            n = len(artistIds)
            for i in range(n-1):
                id_i = artistIds[i]
                for j in range(i+1,n):
                    id_j = artistIds[j]
                    pair2data[(id_i,id_j)] += counts[id_i] * counts[id_j]
    print('\tdone.')


    data = list(pair2data.values())
    source, destination = zip(*pair2data.keys())
    coMat = coo_matrix((data,(source,destination)))
    coMat = coMat.tocsr()
    np.savez('coMat_countSq', coMat=coMat, countSq=countsSq)

    #print('Deepcopying coMat...',)
    #cosine = copy.deepcopy(coMat)
    #print('\tdone.')


    n = coMat.shape[0]
    len_n = str(len(range(n-1)))

    ##cosine_json = {}
    #for i in range(n-1):
    #    print('calculating cos similary ' + str(i) + ' of ' + len_n)
    #    #cosine_json[i] = {}
    #    for j in range(i+1,n):
    #        cosine[i,j] /= np.sqrt(countsSq[i]*countsSq[j]);
    #        #cosine_json[i][j] = cosine[i,j]
    #    print('\tdone.')


    deezer_data = {'ids2related': 'parsed/filtered_deezer_id2related.txt',
            'name2ids': 'json/deezer_names2ids.json'}

    spotify_data = {'ids2related': 'parsed/filtered_spotify_id2related.txt',
            'name2ids': 'json/spotify_names2ids.json'}

    print('calculating d_cosine_ratio...',)
    d_cosine_ratio = related2ratio(deezer_data, artist2artistId, True)
    print('\tdone.')

    print('calculating d_coMat_ratio...',)
    d_coMat_ratio  = related2ratio(deezer_data, artist2artistId)
    print('\tdone.')

    print('calculating s_cosine_ratio...',)
    s_cosine_ratio = related2ratio(spotify_data, artist2artistId, True)
    print('\tdone.')

    print('calculating s_coMat_ratio...',)
    s_coMat_ratio  = related2ratio(spotify_data, artist2artistId)
    print('\tdone.')


    print('saving data...',)
    with open(args.outpath,'w') as outfile:
        csvout = csv.writer(outfile, delimiter=',')
        csvout.writerow(['i', 'd_cosine_ratio[i]', 'd_coMat_ratio[i]', 's_cosine_ratio[i]', 's_coMat_ratio[i]'])
        for i in range(len(artist2artistId)):
            if i in d_cosine_ratio and i in s_cosine_ratio:
                csvout.writerow([i, d_cosine_ratio[i], d_coMat_ratio[i], s_cosine_ratio[i], s_coMat_ratio[i]])
    print('\tdone.')



if __name__ == '__main__':
    args = get_arguments()
    run(args)
