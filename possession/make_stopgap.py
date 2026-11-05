"""STOPGAP submission: python -m possession.make_stopgap (needs data/tactical smart tagging XML)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'starter')]
os.chdir(ROOT)
import numpy as np, games
import load_smart_tagging as t
from possession.from_baseline_raw import run
lab=run('evaluation/results/baseline_raw.csv', t.load(), games.half_video_blocks('BAR-ATH'), 199319)
with open('evaluation/results/stopgap_v1.csv','w') as f:
    f.write('frame,label\n'); f.writelines('%d,%s\n'%(i,l) for i,l in enumerate(lab))
for h,lo,hi in games.half_video_blocks('BAR-ATH'):
    seg=lab[lo:hi+1]; ch=np.flatnonzero(seg[1:]!=seg[:-1])+1
    st=np.r_[0,ch]; en=np.r_[ch,len(seg)]
    live=[(b-a)/25 for a,b in zip(st,en) if seg[a] in 'HA']
    print('half',h,{k:int((seg==k).sum()) for k in 'HAD'},'live spells',len(live),'mean %.1fs'%np.mean(live))
