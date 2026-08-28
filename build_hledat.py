#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sestaví hledat.html — jedno hledání přes celý portál.

Index: usnesení zastupitelstva (text, téma, částka), veřejné zakázky z profilu
zadavatele, příjemci dotací a darů a rozpočtové oblasti (odvětví) za poslední
uzavřený rok. Hledání běží v prohlížeči (bez diakritiky, všechna slova musí sedět).

Spouštět PO build_dotace.py (čte data/dotace.json)."""
import sys, json, re
from collections import defaultdict
import portal_common as pc

sys.stdout.reconfigure(encoding="utf-8")
zo = json.load(open("dataset_ZO.json", encoding="utf-8"))
zak = json.load(open("data/zakazky.json", encoding="utf-8"))
dot = json.load(open("data/dotace.json", encoding="utf-8"))
roz = json.load(open("data/rozpocet_ostopovice.json", encoding="utf-8"))


def iso(d):
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", (d or "").replace(" ", ""))
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else ""


# položka indexu: [typ, nadpis, text, datum ISO, odkaz, částka|null, podtitul]
IDX = []
for m in zo:
    n = m["cislo_zasedani"]
    lbl = "Ustavující zasedání ZO" if n == 0 else f"Zastupitelstvo č. {n}/{m['rok']}"
    for b in m["body"]:
        IDX.append(["ZO", lbl, b["text"].replace("Zastupitelstvo obce Ostopovice ", ""), m.get("datum") or "",
                    f"zastupitelstvo.html?zo={m['rok']}-{n}", b.get("castka"), b.get("tema") or ""])

for z in zak:
    uv = re.search(r"úvěr", z["nazev"], re.I)
    IDX.append(["ZAK", z["nazev"], f"veřejná zakázka uveřejněná {z['datum']}" + (" · výběr banky (úvěr)" if uv else ""),
                iso(z["datum"]), z["url"], z.get("hodnota"), "veřejná zakázka"])

rec = defaultdict(lambda: [0, set(), []])
for d in dot:
    a = rec[d["prijemce"]]
    a[0] += d["castka"]; a[1].add(d["rok"]); a[2].append(d["text"][:110])
for p, (tot, yrs, txt) in rec.items():
    IDX.append(["DOT", p, f"dotace a dary z rozpočtu obce {min(yrs)}–{max(yrs)} · " + " · ".join(txt[:2]),
                f"{max(yrs)}-12-31", "dotace.html", tot, "příjemce dotace"])

LY = max(int(k) for k in roz["struktura"])
for o in roz["struktura"][str(LY)]["vydaje_oblast"]:
    if o["skut"]:
        IDX.append(["ROZ", o["name"], f"výdaje obce v roce {LY}: {o['skut']/1e6:.2f} mil. Kč".replace(".", ",")
                    + f" (schválený rozpočet {o['schv']/1e6:.2f} mil. Kč)".replace(".", ","),
                    f"{LY}-12-31", "rozpocet.html", o["skut"], "rozpočet obce"])

DATA = {"idx": IDX}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

body = '''<header class="hero">
  <h1>Hledat na portálu</h1>
  <p>Jedno hledání přes všechno: usnesení zastupitelstva, veřejné zakázky obce, příjemce dotací i oblasti rozpočtu.</p>
</header>
<section>
  <div class="panel">
    <div class="hsrch"><span class="hico">⌕</span><input id="hq" type="search" autocomplete="off" placeholder="např. škola, kanalizace, Sokol, pozemek, úvěr…" aria-label="Hledat"></div>
    <div class="hopts"><span class="hint">Hledání nerozlišuje diakritiku, velikost písmen ani koncovky; musí sedět všechna zadaná slova.</span>
      <span class="hsamples" id="hsamples"></span></div>
    <div class="htabs" id="htabs"></div>
  </div>
</section>
<section id="res" hidden>
  <div class="sec-h"><h2 id="resH">Výsledky</h2><span class="hint" id="resHint"></span></div>
  <div id="resList"></div>
  <button class="more" id="resMore" hidden>Zobrazit další</button>
</section>'''

CSS = '''<style>
.hsrch{position:relative}
.hsrch input{width:100%;box-sizing:border-box;font:inherit;font-size:17px;padding:14px 16px 14px 44px;border-radius:12px;border:1px solid var(--line);background:var(--inset);color:var(--text)}
.hsrch input:focus{outline:2px solid var(--accent);outline-offset:1px}
.hico{position:absolute;left:15px;top:50%;transform:translateY(-50%);font-size:20px;color:var(--muted)}
.hopts{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:10px;align-items:center}
.hsamples button,.htabs button{font:inherit;font-size:12.5px;border:1px solid var(--line);background:var(--inset);color:var(--muted);border-radius:999px;padding:4px 11px;cursor:pointer;margin:2px}
.hsamples button:hover,.htabs button:hover{color:var(--text)}
.htabs{margin-top:12px;display:flex;flex-wrap:wrap;gap:4px}
.htabs button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.htabs button b{font-weight:700;margin-left:4px}
.hres{display:block;text-decoration:none;color:var(--text);background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:8px}
.hres:hover{border-color:var(--accent)}
.hres .hh{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin-bottom:4px}
.hres .ht{font-size:14px;line-height:1.5}
.hres mark{background:rgba(250,204,21,.35);color:inherit;border-radius:3px;padding:0 1px}
.htema{display:inline-flex;align-items:center;gap:5px;font-size:11px;color:var(--muted);background:var(--inset);border:1px solid var(--line);border-radius:999px;padding:1px 8px}
.htema i{width:8px;height:8px;border-radius:2px;display:inline-block}
.htype{font-size:11px;font-weight:700;letter-spacing:.02em;padding:2px 8px;border-radius:999px;color:#fff}
.hamt{margin-left:auto;font-weight:600;color:var(--text);font-variant-numeric:tabular-nums}
.more{display:block;margin:10px auto;font:inherit;padding:9px 18px;border-radius:10px;border:1px solid var(--line);background:var(--surface);color:var(--text);cursor:pointer}
.empty{color:var(--muted);padding:18px;text-align:center}
</style>'''

JS = '''<script>
const D=DATA_JSON, IDX=D.idx;
/*TEMAJS*/
const TYPES={ZO:['Zastupitelstvo','#d97706'],ZAK:['Zakázka','#0d9488'],DOT:['Dotace','#db2777'],ROZ:['Rozpočet','#16a34a']};
const ORDER=['ZO','ZAK','DOT','ROZ'];
const fold=s=>(s||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const FT=IDX.map(it=>fold(it[1]+' '+it[2]+' '+(it[6]||'')));
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const nf=new Intl.NumberFormat('cs-CZ');
function kc(v){if(v==null)return '';return v>=1e6?(v/1e6).toLocaleString('cs-CZ',{maximumFractionDigits:1})+' mil. Kč':nf.format(Math.round(v))+' Kč';}
function fd(iso){if(!iso)return '';const p=iso.split('-');return (+p[2])+'. '+(+p[1])+'. '+p[0];}
// zvýraznění: výskyty tokenů ve fold(textu) → obalit originál (délky se po NFD-fold u češtiny nemění)
function hl(text,toks){
  if(!toks.length)return esc(text);
  const f=fold(text); const marks=new Array(text.length).fill(false);
  for(const t of toks){let i=0;while((i=f.indexOf(t,i))>=0){for(let k=i;k<i+t.length;k++)marks[k]=true;i+=t.length;}}
  let out='',on=false;
  for(let i=0;i<text.length;i++){if(marks[i]&&!on){out+='<mark>';on=true;}if(!marks[i]&&on){out+='</mark>';on=false;}out+=esc(text[i]);}
  return out+(on?'</mark>':'');
}
function snippet(text,toks,len){
  len=len||260; if(text.length<=len)return text;
  const f=fold(text); let p=-1; for(const t of toks){const i=f.indexOf(t);if(i>=0&&(p<0||i<p))p=i;}
  if(p<0)return text.slice(0,len)+'…';
  const s=Math.max(0,p-80); return (s>0?'…':'')+text.slice(s,s+len)+(s+len<text.length?'…':'');
}
function card(i,toks){
  const it=IDX[i], ty=TYPES[it[0]], ext=/^https?:/.test(it[4]);
  const title=it[0]!=='ZO'?'<b>'+hl(it[1],toks)+'</b> — ':'';
  return `<a class="hres" href="${esc(it[4])}"${ext?' target="_blank" rel="noopener"':''}><div class="hh"><span class="htype" style="background:${ty[1]}">${ty[0]}</span>`+
    `<span>${it[0]==='ZO'?esc(it[1])+' · '+fd(it[3]):esc(it[6])}${ext?' ↗':''}</span>`+
    `${it[0]==='ZO'&&it[6]?'<span class="htema"><i style="background:'+temaVar(it[6])+'"></i>'+temaIco(it[6])+esc(it[6])+'</span>':''}`+
    `${it[5]!=null?'<span class="hamt">'+kc(it[5])+'</span>':''}</div>`+
    `<div class="ht">${title}${hl(snippet(it[2],toks),toks)}</div></a>`;
}
let cur=[], curType='all', shown=0; const PAGE=25;
function search(q){
  const raw=q.trim().split(/\\s+/).filter(Boolean);
  // jednoduché „kmenování" kvůli českému skloňování: školní → škol (najde i školou, školy…)
  const stem=t=>t.length>=7?t.slice(0,-2):t.length>=5?t.slice(0,-1):t;
  const toks=raw.map(fold).filter(t=>t.length>=2).map(stem);
  const res=document.getElementById('res'), tabs=document.getElementById('htabs');
  if(!toks.length){res.hidden=true;tabs.innerHTML='';cur=[];return;}
  cur=[];
  for(let i=0;i<IDX.length;i++){const f=FT[i];if(toks.every(t=>f.includes(t)))cur.push(i);}
  // řazení: shoda v názvu (zakázka/příjemce/oblast) napřed, pak novější
  const inTitle=i=>IDX[i][0]!=='ZO'&&toks.some(t=>fold(IDX[i][1]).includes(t));
  cur.sort((a,b)=>{const ta=inTitle(a),tb=inTitle(b);if(ta!==tb)return ta?-1:1;return (IDX[b][3]||'').localeCompare(IDX[a][3]||'');});
  const cnt={};cur.forEach(i=>cnt[IDX[i][0]]=(cnt[IDX[i][0]]||0)+1);
  if(curType!=='all'&&!cnt[curType])curType='all';
  tabs.innerHTML=`<button data-t="all" class="${curType==='all'?'on':''}">Vše<b>${nf.format(cur.length)}</b></button>`+
    ORDER.filter(t=>cnt[t]).map(t=>`<button data-t="${t}" class="${curType===t?'on':''}">${TYPES[t][0]}<b>${nf.format(cnt[t])}</b></button>`).join('');
  tabs.querySelectorAll('button').forEach(b=>b.onclick=()=>{curType=b.dataset.t;search(document.getElementById('hq').value);});
  shown=PAGE; draw(toks);
  res.hidden=false;
  try{history.replaceState(null,'','?q='+encodeURIComponent(q.trim()));}catch(e){}
}
function draw(toks){
  const list=curType==='all'?cur:cur.filter(i=>IDX[i][0]===curType);
  document.getElementById('resH').textContent=list.length?('Nalezeno '+nf.format(list.length)+' výsledků'):'Nic nenalezeno';
  document.getElementById('resHint').textContent=list.length?'klikněte pro detail v příslušné sekci':'';
  document.getElementById('resList').innerHTML=list.length?list.slice(0,shown).map(i=>card(i,toks)).join(''):
    '<div class="empty">Zkuste jiné nebo méně slov — třeba jen kořen slova („kanalizace" → „kanaliz").</div>';
  const m=document.getElementById('resMore'); m.hidden=list.length<=shown;
  m.onclick=()=>{shown+=PAGE;draw(toks);};
}
let tmr; const hq=document.getElementById('hq');
hq.addEventListener('input',()=>{clearTimeout(tmr);tmr=setTimeout(()=>search(hq.value),180);});
document.getElementById('hsamples').innerHTML='Zkuste: '+['škola','kanalizace','Sokol','úvěr','územní plán','pozemek'].map(s=>`<button>${s}</button>`).join('');
document.querySelectorAll('#hsamples button').forEach(b=>b.onclick=()=>{hq.value=b.textContent;search(hq.value);document.getElementById('res').scrollIntoView({behavior:'smooth'});});
(function(){const u=new URLSearchParams(location.search);
  if(u.get('q')){hq.value=u.get('q');search(hq.value);} else hq.focus();})();
bindTheme();
</script>'''.replace("DATA_JSON", data_json).replace("/*TEMAJS*/", pc.TEMA_JS)

html = pc.page("Hledat", "Hledat — Jak žijí Ostopovice", body, head_scripts=CSS, body_scripts=JS)
open("hledat.html", "w", encoding="utf-8").write(html)
print(f"HOTOVO: hledat.html — {len(IDX)} položek indexu, {len(html)//1024} kB")
