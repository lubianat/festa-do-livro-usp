"""Baixa a lista de editoras do evento pela API do site da Festa (todas as páginas)."""
import json,urllib.request,sys
import sys,os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from paths import *
out=[];p=1
while True:
    d=json.load(urllib.request.urlopen(f"{BASE}/api/v1/event-publishers?flag={EVENT}&page={p}"))
    out+=d["data"]; m=d["meta"]
    if m["current_page"]>=m["last_page"]: break
    p+=1
json.dump(out,open(sys.argv[1],"w"),ensure_ascii=False)
print(len(out), sum(1 for x in out if x.get("price_list")))
