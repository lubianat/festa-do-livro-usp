"""Liga cada editora ao seu número no mapa e inclui as editoras que estão no mapa mas não publicaram lista."""
import json,unicodedata,re,difflib
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
D=json.load(open(OUT_DATA));M=json.load(open(MAPS+'/editora_ilha.json'))
def n(s): s=''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c));s=re.sub(r'\((grupo)\)|\bed\.|\beditora\b|\bedicoes\b|\bgrupo\b','',s);return re.sub(r'[^a-z0-9]+','',s)
FIX={'Casa Marx | Iskra':'Iskra / Casa Marx','DarkSide / Magnética':'DarkSide','IMS':'Instituto Moreira Salles','Movimento Neomarginal':'Neomarginal','Revista IEA':'IEA-USP'}
keys={n(k):k for k in M}
pub2map={}
for i,p in enumerate(D['pubs']):
    if p['n'] in FIX: pub2map[i]=FIX[p['n']];continue
    k=n(p['n'])
    if k in keys: pub2map[i]=keys[k];continue
    c=[kk for kk in keys if k and (k in kk or kk in k) and min(len(k),len(kk))>=3]
    if len(c)==1: pub2map[i]=keys[c[0]];continue
    m=difflib.get_close_matches(k,keys,1,0.75)
    if m: pub2map[i]=keys[m[0]];continue
    print('sem mapa:',p['n'])
used=set(pub2map.values())
# IEA-USP and Revista IEA both map; Revista USP separate. keep.
GROUP={'Civilização Brasileira':'Record (Grupo)','Paz & Terra':'Record (Grupo)','Galerinha Record & Reco-Reco':'Record (Grupo)','Magnética':'DarkSide / Magnética'}
added=0
for name,ilha in sorted(M.items(),key=lambda kv:n(kv[0])):
    if name in used: continue
    D['pubs'].append({'n':name,'logo':'','pdf':'','site':'','c':0,'mo':1,'g':GROUP.get(name,'')});pub2map[len(D['pubs'])-1]=name;added+=1
PI={str(i):M[v] for i,v in pub2map.items()}
for i,v in pub2map.items(): D['pubs'][i]['il']=M[v]
json.dump(D,open(OUT_DATA,'w'),ensure_ascii=False,separators=(',',':'))
json.dump(PI,open(CACHE+'/maps/pub_ilha.json','w'))
print('pubs',len(D['pubs']),'só no mapa',added,'com local',len(PI))
