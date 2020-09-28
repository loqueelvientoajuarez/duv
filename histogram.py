from astropy.table import Table
import numpy as np
from matplotlib import pylab as plt

FORMAT = 'ascii.fixed_width_two_line'

def plot_histogram(ax, tab, *, key='age_group', unique=False, min, max):
   
    timed = tab['performance_unit'][0] == 'km'
    if not timed:
        fact = 1 / 3600
        xlabel = 'time [h]'
        step = 1 / 12 
        if tab['event'][0] == '50km':
            step = 1 / 30
        if tab['event'][0] == '100mi':
            step = 1 / 6
    else:
        fact = 1
        xlabel = 'distance [km]'
        step = 1
        if tab['event'][0] == '6d':
            step = 10
        if tab['event'][0] == '48h':
            step = 5
        if tab['event'][0] == '24h':
            step = 2

    bins = np.arange(min, max + step/2, step)     

    # find groups    
    groups = np.unique(tab[key])
    end = []
    start = []
    if groups[0] == '#NA':
        end = ['#NA']
        groups = groups[1:]
    if groups[-1][1:] == 'U23':
        start = [groups[-1]]
        groups = groups[:-1]
    groups = start + groups.tolist() + end

    # subtables by age group
    tabs = [tab[tab[key] == g] for g in groups]

    if unique:
        ylabel = '# of runners'
        for i, tab in enumerate(tabs):
            index = np.argsort(tab['performance'])
            if timed:
                index = index[::-1] 
            tab = tab[index] # sort
            runner_id, index = np.unique(tab['runner_id'], return_index=True)
            tab = tab[index] # keep unique performers
            tabs[i] = tab
    else:
        ylabel = '# of performances'
    
    perf = [tab['performance'] * fact for tab in tabs]
   
    ax.hist(perf, label=groups, histtype='bar', stacked=True, bins=bins)     
    ax.set_xlim(min, max)
    ax.set_xlabel(xlabel) 
    ax.set_ylabel('# of performances')
    ax.legend(fontsize='x-small', ncol=2)

# def make_histogram(event):

def print_event(event):
    tab = Table.read(f"txt/results-{event}.txt", format=FORMAT)

    if event == '100km':
        min, max = 6, 24
    elif event == '50km':
        min, max = 2.5, 10
    elif event == '50mi':
        min, max=  5, 20
    elif event == '100mi':
        min, max = 11, 36
    elif event == '24h':
        min, max = 60, 312
    elif event == '48h':
        min, max = 120, 480
    elif event == '6d':
        min, max = 256, 1048

    fig = plt.figure(1, figsize=(6,8))
    fig.clf()
    for i, gender in enumerate(['M', 'W'], start=1):
        ax = fig.add_subplot(2, 1, i)
        plot_histogram(ax, tab[tab['gender'] == gender], min=min, max=max,
            unique=False) 
        if i < 2:
            ax.set_xlabel('')
            ax.set_xticklabels([])
    fig.tight_layout()
    fig.subplots_adjust(wspace=0, hspace=0)
    fig.show() 
    fig.savefig(f"pdf/histogram-{event}.pdf")


if __name__ == "__main__":
    print_event(sys.argv[0])

#print_event('50km')
#print_event('50mi')
#print_event('100km')
#print_event('100mi')
#print_event('24h')
#print_event('48h')
# print_event('6d')
# print_event('6h')
# print_event('12h')
