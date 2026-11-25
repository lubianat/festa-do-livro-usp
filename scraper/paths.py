"""Caminhos e configurações compartilhados pelo pipeline.

A edição é escolhida pela variável de ambiente EDICAO (padrão: 2026).
Cada edição tem:
  scraper/edicoes/<ano>/config.json   – nome do evento no site da Festa, número da edição
  scraper/edicoes/<ano>/editora_ilha.json, islands.json – tabelas do mapa (feitas à mão)
  site/<ano>/                         – o site publicado daquela edição
  scraper/cache/<ano>/                – PDFs, JSON intermediários (não vai para o git)
"""
import os,json
HERE=os.path.dirname(os.path.abspath(__file__))
ANO=os.environ.get('EDICAO','2026')
MAPS=os.path.join(HERE,'edicoes',ANO)
CFG=json.load(open(os.path.join(MAPS,'config.json')))
CACHE=os.environ.get('FESTA_CACHE',os.path.join(HERE,'cache',ANO))
VEC_CACHE=os.path.join(HERE,'cache','vetores')                     # vetores de palavras, compartilhados entre edições
SITE_ROOT=os.path.join(os.path.dirname(HERE),'site')
SITE=os.path.join(SITE_ROOT,ANO)
OUT_DATA=os.path.join(SITE,'data.json')
EVENT=CFG['evento']
BASE='https://festadolivro.edusp.com.br'
SITE_URL=os.environ.get('SITE_URL','https://lubianat.github.io/festa-do-livro-usp/')
os.makedirs(os.path.join(CACHE,'pdf'),exist_ok=True)
