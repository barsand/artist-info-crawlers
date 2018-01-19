import sys
import json
import numpy as np
import matplotlib.pyplot as plt

_COMAT_GT_COSINE = 'comat>cosine'
_COSINE_GT_COMAT = 'cosine>comat'

S_data = json.loads(open(sys.argv[1], 'r').read())['spotify']
D_data = json.loads(open(sys.argv[1], 'r').read())['deezer']


ylabels = sorted(S_data.keys())

S_tmp = [S_data[y][_COMAT_GT_COSINE]/S_data[y]['total'] for y in ylabels]
S_comat_gt_cosine_ratio = np.array(S_tmp)
S_cosine_gt_comat_ratio = np.array([1 - i for i in S_comat_gt_cosine_ratio])

D_tmp = [D_data[y][_COMAT_GT_COSINE]/D_data[y]['total'] for y in ylabels]
D_comat_gt_cosine_ratio = np.array(D_tmp)
D_cosine_gt_comat_ratio = np.array([1 - i for i in D_comat_gt_cosine_ratio])


bar_width = 3
margin = 0

y = np.array([i * bar_width*2.5 for i in range(S_cosine_gt_comat_ratio.size)])

fig, axes = plt.subplots(ncols=2, sharey=True)
axes[0].barh(y, S_comat_gt_cosine_ratio, bar_width, align='center',
             color='lightgreen')
axes[0].barh(y + bar_width, D_comat_gt_cosine_ratio, bar_width, align='center',
             color='lightgray')
axes[0].set(title='coMat > cosine')

axes[1].barh(y, S_cosine_gt_comat_ratio, bar_width, align='center',
             color='lightgreen')
axes[1].barh(y + bar_width, D_cosine_gt_comat_ratio, bar_width, align='center',
             color='lightgray')
axes[1].set(title='cosine > coMat')

# axes[1].set(yticks=y, yticklabels=ylabels)
# margin = 1
axes[1].set(yticks=[])

axes[0].invert_xaxis()
axes[0].set_xlim(0.9,0)
axes[1].set_xlim(0,0.9)
axes[0].yaxis.tick_right()

for ax in axes.flat:
    ax.margins(0.02)

fig.tight_layout()
fig.subplots_adjust(wspace=margin)
fig.savefig('out.png')
