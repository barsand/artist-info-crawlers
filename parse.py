import sys
import csv
import math
import operator
import json

#
# constants
SPOTIFY = 'spotify'
DEEZER = 'deezer'
SERVICES = [DEEZER, SPOTIFY]
COSINE = 'cosine'
COMAT = 'comat'
PERCENTILES = [i/100 for i in [0,25,50,75,90,95,96,97,98,99,99.5, 100]]

#
# parsing input data
csvfile = open(sys.argv[1], 'r')
csvreader = csv.reader(csvfile)
csvdata = [i for i in csvreader]
headers = csvdata.pop(0)
ratios_data = {}
for d in csvdata:
    i, cosine_deezer, comat_deezer, cosine_spotify, comat_spotify, countsq = d
    ratios_data[i] = {}
    ratios_data[i][COSINE] = {
        SPOTIFY: float(cosine_spotify),
        DEEZER: float(cosine_deezer)
    }
    ratios_data[i][COMAT] = {
        SPOTIFY: float(comat_spotify),
        DEEZER: float(comat_deezer)
    }
    ratios_data[i]['countsq'] = countsq
csvfile.close()

#
# organising data
comparison_data = {}
for i in ratios_data:
    comparison_data[i] = {}
    comparison_data[i][SPOTIFY] = {}
    comparison_data[i][DEEZER] = {}

#
# creating percentile indexes
datalen = len(ratios_data)
intervals = []
interval2slug = {}
for i in range(len(PERCENTILES)-1):
    interval = (
        (math.ceil(PERCENTILES[i]*datalen),
         math.floor(PERCENTILES[i+1]*datalen))
    )
    intervals.append(interval)
    interval2slug[interval] = str(PERCENTILES[i]) + '-' + str(PERCENTILES[i+1])

#
# assigning data to respective percentile according to sorted countsq
ids_and_countsqs = [(i, ratios_data[i]['countsq']) for i in ratios_data]
sorted_ids_and_countsqs = sorted(ids_and_countsqs, key=operator.itemgetter(1))

percentile_ratios = {}
for interval in intervals:
    interval_slug = interval2slug[interval]
    percentile_ratios[interval_slug] = {}
    for i in range(interval[0], interval[1]):
        _id = sorted_ids_and_countsqs[i][0]
        percentile_ratios[interval_slug][_id] = ratios_data[_id]

#
# generating input for distribution
outf = open('percentile_ratios.json', 'w')
outf.write(json.dumps(percentile_ratios, indent=4, sort_keys=True))
outf.close()

#
# counting comat > cosine and comat < cosine for each interval
collision_count = 0
collision_count2 = 0
ratio_comparison = {}
for service in SERVICES:
    ratio_comparison[service] = {}
    for interval in intervals:
        interval_slug = interval2slug[interval]
        ratio_comparison[service][interval_slug] = {}
        comat_gt_cosine = 0
        cosine_gt_comat = 0
        comat_eq_cosine = 0
        for i in range(interval[0], interval[1]):
            _id = sorted_ids_and_countsqs[i][0]
            data = percentile_ratios[interval_slug][_id]
            curr_comat = data[COMAT][service]
            curr_cosine = data[COSINE][service]
            if  curr_comat > curr_cosine:
                comat_gt_cosine += 1
            if curr_cosine > curr_comat:
                cosine_gt_comat += 1
            if curr_cosine == curr_comat:
                comat_eq_cosine += 1
        ratio_comparison[service][interval_slug] = {
            'comat>cosine': comat_gt_cosine,
            'cosine>comat': cosine_gt_comat,
            'comat=cosine': comat_eq_cosine,
            'total': comat_gt_cosine + cosine_gt_comat + comat_eq_cosine
        }

#
# generating input for pyramid plot
outf = open('ratio_comparison.json', 'w')
outf.write(json.dumps(ratio_comparison, indent=4, sort_keys=True))
outf.close()
