import numpy as np
import pandas as pd
from scipy import stats, integrate
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import json

SERVICES = ['deezer', 'spotify']
PLOT_NCOLS = 3
PLOT_NROWS = 4

sns.set(color_codes=True)

jdata = json.loads(open(sys.argv[1], 'r').read())

data_cosine_gt_comat = {}

for percentile in jdata:
    data_cosine_gt_comat[percentile] = {}
    for service in SERVICES:
        data_cosine_gt_comat[percentile][service] = []
        for _id in jdata[percentile]:
            curr_comat = jdata[percentile][_id]['comat'][service]
            curr_cosine = jdata[percentile][_id]['cosine'][service]

            if curr_comat > curr_cosine:
                data_cosine_gt_comat[percentile][service].append(curr_comat)

#
# multiplot config
ig, ax = plt.subplots(figsize=(10,5), ncols=PLOT_NCOLS, nrows=PLOT_NROWS)

left   =  0.125  # the left side of the subplots of the figure
right  =  0.9    # the right side of the subplots of the figure
bottom =  0.1    # the bottom of the subplots of the figure
top    =  0.9    # the top of the subplots of the figure
wspace =  .5     # the amount of width reserved for blank space between subplots
hspace =  1.1    # the amount of height reserved for white space between subplots

# This function actually adjusts the sub plots using the above paramters
plt.subplots_adjust(
    left    =  left,
    bottom  =  bottom,
    right   =  right,
    top     =  top,
    wspace  =  wspace,
    hspace  =  hspace
)


i = 0
j = 0
for percentile in jdata:
    print(i, j, percentile)
    S_data = np.array(data_cosine_gt_comat[percentile]['spotify'])
    sns.distplot(S_data, color='lightgreen', ax=ax[i][j]);

    D_data = np.array(data_cosine_gt_comat[percentile]['deezer'])
    sns.distplot(D_data, color='lightgray', ax=ax[i][j]);

    percentile_slug = percentile.replace('0.', '').replace('1.', '10')

    ax[i][j].set_title(percentile_slug)

    j += 1
    if j >= PLOT_NCOLS:
        j = 0
        i += 1

    if i >= PLOT_NROWS:
        i = 0

    # plt.savefig('distribution-' + percentile_slug + '.png')

ax[3][2].set_axis_off()
plt.suptitle('distribution cosine > comat')
plt.savefig('out-distribution.pdf')





