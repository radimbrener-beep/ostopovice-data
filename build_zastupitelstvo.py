#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Zastupitelstvo (zastupitelstvo.html) — usnesení ZO Ostopovic.
Fulltext, filtr podle roku/tématu/hodnoty, rozbalovací zasedání, hlasování,
odkaz na originální PDF. Data z dataset_ZO.json (parser parse_zo_osto)."""
import sys, json, os
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

zo = json.load(open("dataset_ZO.json", encoding="utf-8"))
# nejnovější nahoru (rok, pak číslo)
zo.sort(key=lambda m: m["datum"], reverse=True)

pocet_zas = len(zo)
pocet_usn = sum(m["pocet_bodu"] for m in zo)
roky = sorted({m["rok"] for m in zo}, reverse=True)
temata = sorted({b["tema"] for m in zo for b in m["body"] if b.get("tema")})

# krátká shrnutí zasedání (psaná jazykovým modelem dle pravidel portálu Střelic, data/shrnuti/zo.json)
SHRNUTI = json.load(open("data/shrnuti/zo.json", encoding="utf-8")) if os.path.exists("data/shrnuti/zo.json") else {}
for m in zo:
    m["shrnuti"] = SHRNUTI.get(f'{m["rok"]}-{m["cislo_zasedani"]}', "")
    m.pop("raw_text", None)

# polohy parcel (k.ú. Ostopovice) pro prokliky do katastrální mapy — cache z geocode_parcely.py
GEO_PATH = os.path.join("data", "parcely_geo.json")
parcely_geo = json.load(open(GEO_PATH, encoding="utf-8")) if os.path.exists(GEO_PATH) else {}

DATA = {"obec": "Ostopovice", "zasedani": zo, "roky": roky, "temata": temata, "pgeo": parcely_geo}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

body = f'''<header class="hero">
  <h1>Usnesení zastupitelstva</h1>
  <p>Procházejte usnesení Zastupitelstva obce Ostopovice. U každého usnesení najdete výsledek hlasování, téma i případnou částku, a otevřete si originální zápis v PDF.</p>
  <div class="chips"><span class="chip">obec Ostopovice · okres Brno-venkov</span><span class="chip">{roky[-1]}–{roky[0]}</span><span class="chip">zdroj: ostopovice.cz</span></div>
</header>

<div class="cards" id="kpis"></div>

<section>
  <div class="sec-h"><h2>Procházení usnesení</h2><span class="hint">klikni na zasedání pro rozbalení · hledání ignoruje diakritiku</span></div>
  <div class="panel">
    <div class="tbar" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:12px">
      <span class="search" style="flex:1;min-width:200px;position:relative">
        <input type="text" id="q" placeholder="hledat v usneseních…" style="width:100%">
      </span>
      <span><span class="lbl">Rok</span>
        <select id="fRok"><option value="">Vše</option>{''.join(f'<option>{r}</option>' for r in roky)}</select></span>
      <span><span class="lbl">Téma</span>
        <select id="fTema"><option value="">Vše</option>{''.join(f'<option>{t}</option>' for t in temata)}</select></span>
      <span><span class="lbl">Řadit</span>
        <select id="fSort"><option value="new">Nejnovější</option><option value="old">Nejstarší</option></select></span>
    </div>
    <div id="pocet" class="note" style="margin:0 0 10px"></div>
    <div id="list">''' + pc.skel(7) + '''</div>
  </div>
  <p class="note">U každého usnesení je uveden výsledek hlasování (pro · proti · zdržel se), je-li v zápise k dispozici; zvýrazněná jsou usnesení, kde někdo hlasoval proti nebo se zdržel. Témata i částky jsou přiřazeny automaticky; shrnutí „V kostce" napsal jazykový model (AI) z textu usnesení — rozhoduje vždy text usnesení a originální PDF. Čísla parcel v k. ú. Ostopovice jsou proklikávací do katastrální mapy (iKatastr). Jména soukromých osob jsou zkrácena na iniciály, adresy a data narození vynechány.</p>
</section>'''

scripts = '''<script>
const D=DATA_JSON, Z=D.zasedani;
// čísla parcel → odkaz do katastrální mapy (souřadnice z data/parcely_geo.json; jen k.ú. Ostopovice)
const PGEO=D.pgeo||{};
const PARC_RE=/((?:p(?:arc)?\\.?\\s*č\\.?|parcel\\w*\\s*č\\.?)\\s*)(\\d{1,5}(?:\\/\\d{1,4})?)/gi;
const OTHER_KU=/k\\.?\\s*ú\\.?\\s*(Střelic|Troubsk|Nebovid|Moravan|Bohunic|Lískov|Želešic|Modřic|Popůvk|Bosonoh|Brno)/i;
function linkifyParc(html, allow){
  if(!allow) return html;
  return html.replace(PARC_RE,(m,pre,num)=>{
    const g=PGEO[num]; if(!g) return m;
    const u=`https://www.ikatastr.cz/#kde=${g[0]},${g[1]},18&mapa=zakladni&vrstvy=parcelybudovy&info=${g[0]},${g[1]}`;
    return pre+`<a class="parc" href="${u}" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="Parcela č. ${num} v katastrální mapě (k.ú. Ostopovice)">${num}</a>`;
  });
}
const nf=new Intl.NumberFormat('cs-CZ');
const norm=s=>(s||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const KAT_COL={'schvaluje':'var(--pos)','neschvaluje':'var(--neg)','bere na vědomí':'var(--c5)',
  'pověřuje':'var(--c0)','ukládá':'var(--c4)','souhlasí':'var(--c2)','nesouhlasí':'var(--neg)',
  'vydává':'var(--c3)','volí':'var(--c6)','zřizuje':'var(--c1)','jiné':'var(--faint)'};
function katCol(k){return KAT_COL[k]||'var(--faint)';}
/*TEMAJS*/
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const zLab=m=>m.cislo_zasedani===0?'ustavující '+m.rok:'ZO '+m.cislo_zasedani+'/'+m.rok;
const money=v=> v==null?'':(v>=1e6?(v/1e6).toLocaleString('cs-CZ',{maximumFractionDigits:2})+' mil. Kč':nf.format(v)+' Kč');

function kpis(){
  const usn=Z.reduce((a,m)=>a+m.pocet_bodu,0);
  const temCount=new Set(); Z.forEach(m=>m.body.forEach(b=>b.tema&&temCount.add(b.tema)));
  const C=[
    ['Zasedání', nf.format(Z.length), D.roky[D.roky.length-1]+'–'+D.roky[0],'var(--c0)'],
    ['Usnesení celkem', nf.format(usn), 'napříč zasedáními','var(--c1)'],
    ['Tematických oblastí', String(temCount.size), 'klasifikace usnesení','var(--c2)'],
    ['Zdroj', 'ostopovice.cz', 'zápisy ZO (PDF)','var(--c3)'],
  ];
  document.getElementById('kpis').innerHTML=C.map(c=>`<div class="kpi" style="--bar:${c[3]}"><div class="lab">${c[0]}</div><div class="val" style="font-size:23px">${c[1]}</div><div class="delta" style="color:var(--muted)">${c[2]}</div></div>`).join('');
}

let openSet=new Set();
function render(){
  const q=norm(document.getElementById('q').value.trim());
  const fr=document.getElementById('fRok').value;
  const ft=document.getElementById('fTema').value;
  const sort=document.getElementById('fSort').value;
  let list=Z.slice().sort((a,b)=> sort==='old' ? a.datum.localeCompare(b.datum) : b.datum.localeCompare(a.datum));
  if(fr) list=list.filter(m=>String(m.rok)===fr);

  let shownUsn=0, html='';
  list.forEach(m=>{
    let bodies=m.body;
    if(ft) bodies=bodies.filter(b=>b.tema===ft);
    if(q) bodies=bodies.filter(b=>norm(b.text).includes(q));
    if((ft||q) && bodies.length===0) return;
    shownUsn+=bodies.length;
    const id=m.rok+'-'+m.cislo_zasedani;
    const open=openSet.has(id) || !!(q||ft);
    const rows=bodies.map(b=>{
      const hl=b.hlasovani||[]; const hlTxt=(hl[0]!=null)?`pro ${hl[0]} · proti ${hl[1]} · zdržel se ${hl[2]}`:'';
      const split=hl[0]!=null&&(hl[1]>0||hl[2]>0);
      const cast=b.castka?`<span class="pill" style="background:var(--inset);color:var(--text)">${money(b.castka)}</span>`:'';
      return `<div class="usn${split?' split':''}">
        <div class="usn-h">
          <span class="katpill" style="background:${katCol(b.kategorie)}">${b.kategorie}</span>
          <span class="usn-id">${b.usneseni_id||''}</span>
          ${b.tema?`<span class="tema"><i style="background:${temaVar(b.tema)}"></i>${temaIco(b.tema)}${esc(b.tema)}</span>`:''}
          ${cast}
        </div>
        <div class="usn-t">${linkifyParc(esc(b.text), !OTHER_KU.test(b.text))}</div>
        ${hlTxt?`<div class="usn-hl">${hlTxt}${split?' · <b>nejednomyslně</b>':''}</div>`:''}
      </div>`;}).join('');
    html+=`<div class="zas ${open?'open':''}" data-id="${id}">
      <div class="zas-h" onclick="toggle('${id}')">
        <span class="zas-c">${zLab(m)}</span>
        <span class="zas-d">${m.datum_text}</span>
        <span class="zas-n">${bodies.length} ${(q||ft)?'nalezeno':'bodů'}</span>
        ${m.url?`<a class="zas-pdf" href="${m.url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">PDF ↗</a>`:''}
        <span class="zas-ar">${open?'▾':'▸'}</span>
      </div>
      ${m.shrnuti&&!(q||ft)?`<div class="zsum" onclick="toggle('${id}')"><span><b>V kostce:</b> ${esc(m.shrnuti)}</span></div>`:''}
      <div class="zas-b" ${open?'':'hidden'}>${rows}</div>
    </div>`;
  });
  document.getElementById('list').innerHTML=html||'<p class="note">Nic nenalezeno.</p>';
  document.getElementById('pocet').innerHTML=`Zobrazeno <b>${list.length}</b> zasedání · <b>${shownUsn}</b> usnesení`;
}
function toggle(id){ if(openSet.has(id))openSet.delete(id); else openSet.add(id); render(); }

// přímý odkaz na zasedání: zastupitelstvo.html?zo=2025-5 (z Hledat, Bilance, rozcestníku)
(function(){const z=new URLSearchParams(location.search).get('zo');if(z){openSet.add(z);}})();
kpis(); render(); bindTheme();
(function(){const z=new URLSearchParams(location.search).get('zo');if(!z)return;
  const go=()=>{const el=document.querySelector('.zas[data-id="'+z+'"]');if(el)el.scrollIntoView({block:'start'});};
  go(); window.addEventListener('load',()=>setTimeout(go,60));})();
['q','fRok','fTema','fSort'].forEach(id=>document.getElementById(id).addEventListener('input',render));
</script>'''.replace("DATA_JSON", data_json).replace("/*TEMAJS*/", pc.TEMA_JS)

CSS = '''<style>
.zsum{padding:0 16px 12px;margin-top:-4px;font-size:13.5px;line-height:1.55;color:var(--muted);cursor:pointer}
.zsum b{color:var(--text);font-weight:600}
.zas:not(.open) .zsum span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.zas.open .zsum{padding-top:10px}
.usn.split{border-left:3px solid var(--vydaje);padding-left:10px;margin-left:-13px}
.tema i{width:8px;height:8px;border-radius:2px;display:inline-block;margin-right:5px;vertical-align:0}
.zas{border:1px solid var(--line);border-radius:var(--radius-sm);margin-bottom:10px;overflow:hidden;background:var(--surface)}
.zas-h{display:flex;align-items:center;gap:14px;padding:13px 16px;cursor:pointer;transition:.15s}
.zas-h:hover{background:var(--inset)}
.zas-c{font-weight:680;color:var(--accent);min-width:92px}
.zas-d{color:var(--muted);font-size:13.5px;min-width:100px}
.zas-n{color:var(--muted);font-size:12.5px;margin-left:auto}
.zas-pdf{font-size:12px;font-weight:600;color:var(--accent);text-decoration:none;border:1px solid var(--line);padding:3px 9px;border-radius:8px}
.zas-pdf:hover{background:var(--accent-soft)}
.zas-ar{color:var(--faint);width:14px;text-align:center}
.zas-b{border-top:1px solid var(--line);padding:6px 16px 12px}
.usn{padding:11px 0;border-bottom:1px dashed var(--line)}
.usn:last-child{border-bottom:0}
.usn-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:5px}
.katpill{font-size:11px;font-weight:700;color:#fff;padding:2px 9px;border-radius:999px;text-transform:lowercase}
.usn-id{font-size:11.5px;color:var(--faint);font-variant-numeric:tabular-nums}
.tema{font-size:11px;color:var(--muted);background:var(--inset);border:1px solid var(--line);padding:2px 8px;border-radius:999px}
.pill{font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px}
.usn-t{font-size:13.5px;line-height:1.55}
.parc{color:var(--accent);text-decoration:none;border-bottom:1px dashed var(--accent);white-space:nowrap}
.parc:hover{background:var(--accent-soft);border-bottom-style:solid}
.parc::after{content:"";display:inline-block;width:.72em;height:.72em;margin-left:2px;vertical-align:.25em;background:currentColor;opacity:.75;-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z'/%3E%3Ccircle cx='12' cy='10' r='2'/%3E%3C/svg%3E") center/contain no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z'/%3E%3Ccircle cx='12' cy='10' r='2'/%3E%3C/svg%3E") center/contain no-repeat}
.usn-hl{font-size:12px;color:var(--muted);margin-top:4px;font-variant-numeric:tabular-nums}
select,input[type=text]{font:inherit;font-size:13.5px;padding:7px 11px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--text);outline:none}
select:focus,input[type=text]:focus{border-color:var(--accent)}
@media(max-width:560px){.zas-h{flex-wrap:wrap;gap:6px 10px}.zas-n{margin-left:0}}
</style>'''

open("zastupitelstvo.html", "w", encoding="utf-8").write(
    pc.page("Zastupitelstvo", "Usnesení zastupitelstva — Jak žijí Ostopovice", body,
            head_scripts=CSS, body_scripts=scripts))
print(f"HOTOVO -> zastupitelstvo.html ({pocet_zas} zasedání, {pocet_usn} usnesení, roky {roky[-1]}-{roky[0]})")
