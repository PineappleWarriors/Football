"""Live dashboard: rl/runs/latest/dashboard.html (auto-refreshes while training; open in a browser)."""
import json
import os
import time

MAX_SNAPSHOTS = 60
MAX_POINTS = 600


def _thin(points, limit):
    while len(points) > limit:
        points[:] = points[::2]


class Recorder:
    def __init__(self, out_dir, total_minutes):
        self.dir = out_dir
        self.m = {"started": time.time(), "total_minutes": total_minutes, "status": "starting",
                  "stages": {}, "note": ""}
        self.last = 0.0
        path = os.path.join(out_dir, "metrics.json")
        if os.path.exists(path):                       # resume: keep earlier curves
            try:
                old = json.load(open(path))
                self.m["stages"] = old.get("stages", {})
                self.m["prior_elapsed"] = old.get("elapsed", 0.0)
            except Exception:                          # noqa: BLE001
                pass

    def _st(self, stage):
        return self.m["stages"].setdefault(stage, {
            "history": [], "reward": [], "ce": [], "entropy": [], "imit_loss": [],
            "snapshots": [], "ref": None, "state": {}})

    def set_status(self, status, note=""):
        self.m["status"], self.m["note"] = status, note
        self.flush(force=True)

    def set_reference(self, stage, gt, vit, vit_score=None):
        st = self._st(stage)
        st["ref"] = {"gt": gt, "vit": vit}
        if vit_score is not None:
            st["viterbi"] = [round(vit_score[0], 4), round(vit_score[1], 4)]

    def metric(self, stage, name, it, value):
        pts = self._st(stage)[name]
        pts.append([it, round(value, 4)])
        _thin(pts, MAX_POINTS)

    def snapshot(self, stage, it, phase, strip, conf, entry):
        st = self._st(stage)
        st["history"] = [h for h in st["history"] if not (h["it"] == it and h["phase"] == phase)]
        st["history"].append(entry)
        if strip is not None:
            st["snapshots"].append({"it": it, "phase": phase, "strip": strip, "conf": conf})
            _thin(st["snapshots"], MAX_SNAPSHOTS)
        self.flush(force=True)

    def update(self, stage, state, budget):
        st = self._st(stage)
        st["state"] = {"phase": state["phase"], "it": state["it"], "best": state["best"],
                       "best_it": state["best_it"], "elapsed": state["elapsed"], "budget": budget}
        self.flush()

    def flush(self, force=False):
        if not force and time.time() - self.last < 10:
            return
        self.last = time.time()
        self.m["elapsed"] = self.m.get("prior_elapsed", 0.0) + (time.time() - self.m["started"])
        self.m["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        tmp = os.path.join(self.dir, "metrics.json.tmp")
        with open(tmp, "w") as fh:
            json.dump(self.m, fh)
        os.replace(tmp, os.path.join(self.dir, "metrics.json"))
        refresh = "" if self.m["status"] in ("done", "stopped") else '<meta http-equiv="refresh" content="15">'
        html = TEMPLATE.replace("__REFRESH__", refresh).replace("__DATA__", json.dumps(self.m))
        tmp = os.path.join(self.dir, "dashboard.html.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(html)
        os.replace(tmp, os.path.join(self.dir, "dashboard.html"))


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
__REFRESH__
<title>Possession RL Dashboard</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b1f24;--mute:#5f6b7a;--line:#dde2e8;--H:#2a6fdb;--A:#e8772e;--D:#9aa4b2;--X:#e9ecf0;--rl:#1a9b6c;--vit:#7b5cd6}
@media(prefers-color-scheme:dark){:root{--bg:#12161b;--card:#1b2128;--ink:#e8ecf1;--mute:#9aa6b4;--line:#2d3641;--H:#5b9bff;--A:#ff9a52;--D:#6f7b8a;--X:#242c35;--rl:#3ccf9a;--vit:#a48cff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:0 0 4px}p.sub{margin:0 0 14px;color:var(--mute);font-size:13px}
.grid{display:grid;gap:14px}.cards{grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.k{font-size:12px;color:var(--mute);text-transform:uppercase;letter-spacing:.04em}.v{font-size:22px;font-weight:650;margin-top:2px}
.two{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
canvas{width:100%;display:block}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--mute);margin:6px 0}
.sw{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.row{display:flex;align-items:center;gap:10px;margin:3px 0}.row b{width:96px;font-size:13px;font-weight:600;flex:none}
.row canvas{height:22px;border-radius:4px;background:var(--X)}
.ctl{display:flex;gap:10px;align-items:center;margin:10px 0;flex-wrap:wrap}.ctl input[type=range]{flex:1;min-width:200px}
button{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:5px 12px;cursor:pointer;font:inherit}
.bar{height:8px;background:var(--line);border-radius:5px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--rl)}
.note{font-size:13px;color:var(--mute)}
@media(max-width:560px){.two{grid-template-columns:1fr}}
</style></head><body><main>
<h1>Possession bot: RL training dashboard</h1>
<p class="sub" id="sub"></p>
<div class="grid cards" id="cards"></div>
<div class="card" style="margin-top:14px"><div class="k">Overall progress</div><div class="bar" style="margin-top:8px"><i id="pbar" style="width:0%"></i></div><div class="note" id="ptxt" style="margin-top:6px"></div></div>
<div id="stages"></div>
</main>
<script>
const D = __DATA__;
const C = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
const fmt = (x,d=3)=> (x==null||isNaN(x))?'–':Number(x).toFixed(d);
const hms = s => { s=Math.max(0,Math.round(s)); return Math.floor(s/3600)+'h '+String(Math.floor(s%3600/60)).padStart(2,'0')+'m'; };
document.getElementById('sub').textContent = 'Status: '+D.status+(D.note?(' · '+D.note):'')+' · updated '+D.updated+(D.status==='done'||D.status==='stopped'?'':' · auto-refreshing every 15 s');
function line(canvas, series, opts){
  const dpr=window.devicePixelRatio||1, w=canvas.clientWidth, h=opts.h||200; canvas.width=w*dpr; canvas.height=h*dpr; canvas.style.height=h+'px';
  const g=canvas.getContext('2d'); g.scale(dpr,dpr); g.clearRect(0,0,w,h);
  const pad={l:44,r:10,t:8,b:22}; let xs=[],ys=[];
  series.forEach(s=>s.pts.forEach(p=>{xs.push(p[0]);ys.push(p[1]);})); (opts.hlines||[]).forEach(l=>ys.push(l.y));
  if(!xs.length){g.fillStyle=C('--mute');g.font='13px system-ui';g.fillText('waiting for data…',pad.l,h/2);return;}
  let x0=Math.min(...xs),x1=Math.max(...xs); if(x0===x1)x1=x0+1; let y0=Math.min(...ys),y1=Math.max(...ys); const m=(y1-y0)*0.1||0.05; y0-=m;y1+=m;
  const X=x=>pad.l+(x-x0)/(x1-x0)*(w-pad.l-pad.r), Y=y=>h-pad.b-(y-y0)/(y1-y0)*(h-pad.t-pad.b);
  g.strokeStyle=C('--line');g.fillStyle=C('--mute');g.font='11px system-ui';g.lineWidth=1;
  for(let i=0;i<=4;i++){const y=y0+(y1-y0)*i/4;g.beginPath();g.moveTo(pad.l,Y(y));g.lineTo(w-pad.r,Y(y));g.stroke();g.fillText(y.toFixed(2),4,Y(y)+4);}
  g.fillText(String(Math.round(x0)),pad.l,h-6);g.fillText(String(Math.round(x1)),w-pad.r-24,h-6);
  (opts.hlines||[]).forEach(l=>{g.strokeStyle=l.c;g.setLineDash([6,4]);g.lineWidth=2;g.beginPath();g.moveTo(pad.l,Y(l.y));g.lineTo(w-pad.r,Y(l.y));g.stroke();g.setLineDash([]);});
  series.forEach(s=>{g.strokeStyle=s.c;g.lineWidth=2;g.beginPath();s.pts.forEach((p,i)=>{i?g.lineTo(X(p[0]),Y(p[1])):g.moveTo(X(p[0]),Y(p[1]));});g.stroke();
    if(s.dots)s.pts.forEach(p=>{g.fillStyle=s.c;g.beginPath();g.arc(X(p[0]),Y(p[1]),3,0,7);g.fill();});});
}
function smooth(pts,k){return pts.map((p,i)=>{const a=pts.slice(Math.max(0,i-k),i+1);return [p[0],a.reduce((s,q)=>s+q[1],0)/a.length];});}
function strip(canvas,str){const dpr=window.devicePixelRatio||1,w=canvas.clientWidth;canvas.width=w*dpr;canvas.height=22*dpr;const g=canvas.getContext('2d');g.scale(dpr,dpr);
  const col={H:C('--H'),A:C('--A'),D:C('--D'),X:C('--X')};const n=str.length;for(let i=0;i<n;i++){g.fillStyle=col[str[i]]||col.X;g.fillRect(i/n*w,0,Math.ceil(w/n)+0.5,22);}}
function conf(canvas,arr){const dpr=window.devicePixelRatio||1,w=canvas.clientWidth;canvas.width=w*dpr;canvas.height=22*dpr;const g=canvas.getContext('2d');g.scale(dpr,dpr);
  arr.forEach((v,i)=>{g.fillStyle=C('--rl');g.globalAlpha=Math.max(0.08,(v-0.34)/0.66);g.fillRect(i/arr.length*w,0,Math.ceil(w/arr.length)+0.5,22);});g.globalAlpha=1;}
function agree(a,b){let n=0,t=0;for(let i=0;i<a.length;i++){if(a[i]==='X')continue;t++;if(a[i]===b[i])n++;}return t?100*n/t:NaN;}
const stages=document.getElementById('stages'); let totalIt=0,bestOverall=null;
Object.entries(D.stages).forEach(([name,st])=>{
  const sec=document.createElement('section');sec.style.marginTop='22px';
  const s=st.state||{};const pretty=name.replace(/_/g,' ');
  const rl=st.history.filter(h=>h.phase==='rl'), im=st.history.filter(h=>h.phase==='imit');
  const vitRep=(D.stages[name].viterbi||{}); 
  sec.innerHTML='<h2>'+pretty+'</h2><p class="sub">'+(s.phase?('phase: '+s.phase+' · step '+s.it+' · best selected step '+(s.best_it||'–')):'')+'</p>'+
   '<div class="grid two"><div class="card"><h2>Held-out spellF1 (the ranking metric)</h2><p class="sub">Game the bot never trained on. Dashed = the current Viterbi model; higher is better.</p><canvas id="c1_'+name+'"></canvas><div class="legend"><span><i class="sw" style="background:var(--rl)"></i>RL bot (reported half)</span><span><i class="sw" style="background:var(--vit)"></i>Viterbi model</span></div></div>'+
   '<div class="card"><h2>Held-out macroF1</h2><p class="sub">Per-frame accuracy across H/A/D (secondary).</p><canvas id="c2_'+name+'"></canvas></div></div>'+
   '<div class="grid two" style="margin-top:14px"><div class="card"><h2>Training reward</h2><p class="sub">Average reward of the bot\'s sampled decisions on training windows (smoothed). It should drift up.</p><canvas id="c3_'+name+'"></canvas></div>'+
   '<div class="card"><h2>Loss and exploration</h2><p class="sub">Label-anchor loss (lower = closer to the event labels) and policy entropy (how undecided the bot is).</p><canvas id="c4_'+name+'"></canvas><div class="legend"><span><i class="sw" style="background:var(--H)"></i>anchor loss</span><span><i class="sw" style="background:var(--A)"></i>entropy</span></div></div></div>'+
   '<div class="card" style="margin-top:14px"><h2>What the bot decides</h2><p class="sub">The same 5-minute stretch of the held-out game at each checkpoint. Drag the slider (or press play) to watch the bot\'s decisions change as it trains.</p>'+
   '<div class="legend"><span><i class="sw" style="background:var(--H)"></i>Home</span><span><i class="sw" style="background:var(--A)"></i>Away</span><span><i class="sw" style="background:var(--D)"></i>Dead ball</span></div>'+
   '<div class="ctl"><button id="pl_'+name+'">▶ play</button><input type="range" id="sl_'+name+'" min="0" max="0" value="0"><span id="lb_'+name+'" class="note"></span></div>'+
   '<div class="row"><b>Truth</b><canvas id="s0_'+name+'"></canvas></div><div class="row"><b>Viterbi</b><canvas id="s1_'+name+'"></canvas></div><div class="row"><b style="color:var(--rl)">RL bot</b><canvas id="s2_'+name+'"></canvas></div><div class="row"><b>Bot confidence</b><canvas id="s3_'+name+'"></canvas></div>'+
   '<p class="note" id="ag_'+name+'"></p></div>';
  stages.appendChild(sec);
  const vit=(st.ref&&st.ref.vit&&st.history.length)?null:null;
  const viterbiLines=[];
  if(D.stages[name].viterbi){viterbiLines.push({y:D.stages[name].viterbi[0],c:C('--vit')});}
  const sp=rl.map(h=>[h.it,h.rep_spell]), mf=rl.map(h=>[h.it,h.rep_macro]);
  const s1=[{pts:sp,c:C('--rl'),dots:true}];
  if(im.length){const last=im[im.length-1];viterbiLines.push({y:last.rep_spell,c:C('--mute')});}
  line(document.getElementById('c1_'+name),s1,{hlines:viterbiLines});
  line(document.getElementById('c2_'+name),[{pts:mf,c:C('--rl'),dots:true}],{});
  line(document.getElementById('c3_'+name),[{pts:smooth(st.reward||[],15),c:C('--rl')}],{});
  line(document.getElementById('c4_'+name),[{pts:smooth(st.ce||[],10),c:C('--H')},{pts:smooth(st.entropy||[],10),c:C('--A')}],{});
  const sn=st.snapshots||[]; const sl=document.getElementById('sl_'+name); sl.max=Math.max(0,sn.length-1);
  const key='sl_'+name; const saved=sessionStorage.getItem(key); sl.value=(saved!==null&&saved!=='live')?Math.min(saved,sl.max):sl.max;
  function show(){const i=+sl.value;const x=sn[i];if(!x||!st.ref){document.getElementById('lb_'+name).textContent='no checkpoint yet';return;}
    document.getElementById('lb_'+name).textContent=x.phase+' step '+x.it+'  ('+(i+1)+'/'+sn.length+')';
    strip(document.getElementById('s0_'+name),st.ref.gt);if(st.ref.vit)strip(document.getElementById('s1_'+name),st.ref.vit);
    strip(document.getElementById('s2_'+name),x.strip);conf(document.getElementById('s3_'+name),x.conf);
    const a=agree(st.ref.gt,x.strip),b=st.ref.vit?agree(st.ref.gt,st.ref.vit):NaN;
    document.getElementById('ag_'+name).textContent='Frame agreement with the truth on this stretch: RL bot '+fmt(a,1)+'%'+(st.ref.vit?(' · Viterbi '+fmt(b,1)+'%'):'')+'. Frame agreement is only a rough guide: possession-level scoring (left charts) cares about whole spells.';
    sessionStorage.setItem(key,i===sn.length-1?'live':i);}
  sl.oninput=show; show(); window.addEventListener('resize',show);
  let timer=null;document.getElementById('pl_'+name).onclick=function(){if(timer){clearInterval(timer);timer=null;this.textContent='▶ play';return;}
    this.textContent='⏸ pause';sl.value=0;show();timer=setInterval(()=>{if(+sl.value>=+sl.max){clearInterval(timer);timer=null;document.getElementById('pl_'+name).textContent='▶ play';return;}sl.value=+sl.value+1;show();},600);};
  totalIt+=(s.it||0); if(rl.length){const b=Math.max(...rl.map(h=>h.rep_spell));bestOverall=Math.max(bestOverall||0,b);} });
const lastStage=Object.values(D.stages).slice(-1)[0]||{state:{}};const ls=lastStage.state||{};
const cards=[['Status',D.status],['Running time',hms(D.elapsed)],['Total budget',hms(D.total_minutes*60)],['Training steps (all stages)',totalIt],['Best held-out spellF1 so far',fmt(bestOverall)]];
document.getElementById('cards').innerHTML=cards.map(c=>'<div class="card"><div class="k">'+c[0]+'</div><div class="v">'+c[1]+'</div></div>').join('');
const frac=Math.min(1,D.elapsed/(D.total_minutes*60));document.getElementById('pbar').style.width=(100*frac).toFixed(1)+'%';
document.getElementById('ptxt').textContent=(100*frac).toFixed(0)+'% of the time budget used. The run also stops early on Ctrl+C and saves everything.';
const y=sessionStorage.getItem('scrollY');if(y)window.scrollTo(0,+y);window.addEventListener('scroll',()=>sessionStorage.setItem('scrollY',window.scrollY));
</script></body></html>
"""
