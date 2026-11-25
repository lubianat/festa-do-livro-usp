"""Baixa o PDF da lista de preços de cada editora para cache/<ano>/pdf/ (só baixa de novo se o endereço mudou)."""
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
import json,urllib.request,concurrent.futures as cf
pubs=json.load(open(os.path.join(CACHE,'pubs.json')))
seen_f=os.path.join(CACHE,'pdf_urls.json')
seen=json.load(open(seen_f)) if os.path.exists(seen_f) else {}
def get(p):
    u=p.get('price_list')
    if not u: return None
    f=os.path.join(CACHE,'pdf',p['url']+'.pdf')
    if os.path.exists(f) and seen.get(p['url'])==u: return None
    try: urllib.request.urlretrieve(u,f);return p['url'],u
    except Exception as e: print('falhou',p['name'],e);return None
with cf.ThreadPoolExecutor(8) as ex:
    new=[r for r in ex.map(get,pubs) if r]
for k,u in new: seen[k]=u
json.dump(seen,open(seen_f,'w'),indent=0)
print(f'{len(new)} listas novas/alteradas · {sum(1 for p in pubs if p.get("price_list"))} editoras com lista')
