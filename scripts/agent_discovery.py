import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AI=ROOT/'ai'
QUEUE=AI/'agent-queue.json'
SOURCES=AI/'source-registry.json'
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def load(p, default):
    try:return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
    except Exception:return default

queue=load(QUEUE,{"items":[]})
if not isinstance(queue.get('items'),list): queue['items']=[]
sources=load(SOURCES,{"sources":[]})
# Safe discovery seed: the agent starts with explicitly registered/public source definitions.
# It does not scrape arbitrary sites or bypass access controls.
existing={x.get('fingerprint') for x in queue['items']}
for src in sources.get('sources',[]):
    title=src.get('seedTitle')
    if not title: continue
    fp=hashlib.sha256((src.get('url','')+'|'+title).encode()).hexdigest()[:16]
    if fp in existing: continue
    queue['items'].append({
        'id':'candidate-'+fp,'fingerprint':fp,'title':title,
        'summary':src.get('summary','待AI整理'),'type':src.get('type','research'),
        'source':src.get('url',''),'sourceDate':src.get('sourceDate',''),
        'createdAt':now,'risk':src.get('risk','medium'),'status':'pending'
    })
queue['items']=queue['items'][-500:]
QUEUE.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Agent discovery queue updated: {now}; items={len(queue["items"])}')
