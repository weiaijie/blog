"""Draw the two-year fresh accounts from archived daily closes."""
import argparse
import csv
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

LABELS = {'510300':'CSI 300','513500':'S&P 500','159920':'Hang Seng','equal':'Equal equity sleeves'}


def plot(folder):
    with (folder/'daily.csv').open() as f:
        rows = [r for r in csv.DictReader(f) if r['years']=='2']
    with matplotlib.rc_context({'svg.hashsalt':'etf-rmb-two-years','font.family':'DejaVu Sans'}):
        fig, (nav, dd) = plt.subplots(2,1,figsize=(9,5.8),sharex=True,layout='constrained')
        for (code,label), color in zip(LABELS.items(),['#3679a8','#b85119','#6f64a7','#167450']):
            sub = [r for r in rows if r['group']==code]
            days = [date.fromisoformat(r['date']) for r in sub]
            values = np.array([float(r['equity']) for r in sub])
            nav.plot(days,values/1000,label=label,color=color,lw=1.7 if code=='equal' else 1)
            dd.plot(days,(values/np.maximum.accumulate(values)-1)*100,color=color,lw=1.7 if code=='equal' else 1)
        nav.set_title('50% equity / 50% China government bond ETF',loc='left')
        nav.set_ylabel('Account value (RMB thousands)')
        nav.legend(ncol=2,loc='upper left',frameon=False)
        dd.set_ylabel('Closing drawdown (%)')
        dd.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
        dd.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        for ax in (nav,dd):
            ax.grid(axis='y',alpha=.22)
            ax.spines[['top','right']].set_visible(False)
        fig.savefig(folder/'two-years.svg',metadata={'Date':None})
        plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    plot(parser.parse_args().folder)
