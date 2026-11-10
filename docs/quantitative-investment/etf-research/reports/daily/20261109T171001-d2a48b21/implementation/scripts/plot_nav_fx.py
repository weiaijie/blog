"""Plot ex-post NAV/price and cumulative peak-to-trough contributions from verified CSVs."""
import argparse
import csv
from datetime import date
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def plot(folder):
    with (folder/'drawdown.csv').open() as f:
        daily=list(csv.DictReader(f))
    start,end=daily[0]['previous'],daily[-1]['date']
    with (folder/'market.csv').open() as f:
        market=[r for r in csv.DictReader(f) if r['symbol']=='513500' and start<=r['date']<=end]
    days=[date.fromisoformat(r['date']) for r in market]
    with matplotlib.rc_context({'svg.hashsalt':'nav-fx-513500','font.family':'DejaVu Sans'}):
        fig,(marks,pnl)=plt.subplots(2,1,sharex=True,figsize=(9,6.5),layout='constrained')
        marks.plot(days,[float(r['close_cny']) for r in market],label='Shanghai close',color='#275b7a')
        marks.plot(days,[float(r['nav_cny']) for r in market],label='Same-date NAV',color='#ae531a')
        marks.set_ylabel('CNY per ETF unit')
        marks.set_title('513500 and the 50/50 account drawdown',loc='left')
        for cols,title,colour in [
                (['nav_in_fx_units'],'NAV excluding FX translation','#ae531a'),
                (['premium_gap'],'Market price minus NAV','#246e72'),
                (['fx_translation'],'FX translation','#857b28'),
                (['account_change'],'Total account P&L','#272f42')]:
            changes=[0]+[sum(float(r[k]) for k in cols)/1000 for r in daily]
            pnl.plot(days,np.cumsum(changes),label=title,color=colour,lw=1.6)
        pnl.set_ylabel('Cumulative P&L (CNY thousands)')
        pnl.xaxis.set_major_locator(mdates.MonthLocator())
        pnl.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        for ax in (marks,pnl):
            ax.legend(loc='best',frameon=False,ncol=2)
            ax.spines[['top','right']].set_visible(False)
            ax.grid(axis='y',alpha=.2)
        fig.savefig(folder/'drawdown.svg',metadata={'Date':None})
        plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('folder',type=Path)
    plot(p.parse_args().folder)
