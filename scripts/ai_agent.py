import json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AI=ROOT/'ai'; GEN=AI/'generated'; GEN.mkdir(parents=True,exist_ok=True)
KEY=os.environ.get('DASHSCOPE_API_KEY','').strip()
MODEL=os.environ.get('QWEN_MODEL','qwen-turbo')
ENDPOINT=os.environ.get('QWEN_ENDPOINT','https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def call_model(topic):
    if not KEY: return {'status':'skipped','reason':'DASHSCOPE_API_KEY 未配置'}
    system='你是洪盛集藏AI收藏智能体。只整理可核验的收藏知识。严禁编造。价格、真伪、评级必须注明来源和日期，并明确不确定性。输出JSON：title,summary,facts,questions,sources_needed。'
    payload={'model':MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':f'请整理研究主题：{topic}'}],'temperature':0.2,'response_format':{'type':'json_object'}}
    req=urllib.request.Request(ENDPOINT,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=45) as r: data=json.loads(r.read().decode())
        return {'status':'ok','model':MODEL,'result':json.loads(data['choices'][0]['message']['content'])}
    except Exception as e: return {'status':'error','error':str(e)[:500]}

def main():
    topics=['中国钱币收藏基础知识','银元基础研究','古钱币基础研究','福建钱币文化']
    topic=os.environ.get('AGENT_TOPIC','').strip() or topics[datetime.now(timezone.utc).day%len(topics)]
    out={'agent':'洪盛集藏 AI 收藏智能体','generatedAt':now,'topic':topic,**call_model(topic)}
    (GEN/'latest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
