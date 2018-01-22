# popularity-vs-similarity

Usage:

- first, install the requirements:

`pip3 install -r requirements.txt`

- then, generate the JSON input for the plot-generating scripts:

`python3 parse.py clean_out_no_zeroes.txt`

to generate pyramid plot:
`python3 generate-pyramid-plots.py ratio_comparison.json`

to generate distributions plot:
`python3 generate-distribution-plots.py percentile_ratios.json`
