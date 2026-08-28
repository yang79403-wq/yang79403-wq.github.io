import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / 'ai'
GEN = AI / 'generated'
GEN.mkdir(parents=True, exist_ok=True)

now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def read_json(path, default):
    try:
        if path.exists():
            value = json.loads(path.read_text(encoding='utf-8'))
            return value
    except Exception:
        pass
    return default

# Autonomous collector baseline: inspect the site's own structured knowledge and
# produce a machine-readable health/report snapshot. External APIs remain optional.
knowledge_files = []
for folder in (ROOT / 'data' / 'content', ROOT / 'data' / 'market', ROOT / 'knowledge' / 'entities'):
    if folder.exists():
        knowledge_files.extend(sorted(str(p.relative_to(ROOT)) for p in folder.glob('*.json')))

manifest = read_json(AI / 'discovery-manifest.json', {})
model = read_json(AI / 'industry-model.json', {})
report = {
    'generatedAt': now,
    'agent': '洪盛集藏 AI Agent',
    'mode': 'autonomous-safe',
    'site': '洪盛集藏',
    'cycle': 'scheduled',
    'checks': {
        'discoveryManifest': bool(manifest),
        'industryModel': bool(model),
        'knowledgeFileCount': len(knowledge_files),
        'knowledgeFiles': knowledge_files[:200],
        'publicSearch': (ROOT / 'search.html').exists(),
        'archive': (ROOT / 'archive' / 'index.html').exists(),
        'knowledgeBase': (ROOT / 'knowledge' / 'index.html').exists(),
    },
    'nextActions': [
        '发现授权公开内容源',
        '提取新资料并记录来源与日期',
        'AI分类与去重',
        '生成审核队列',
        '审核通过后发布并更新索引'
    ]
}
(AI / 'runtime-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

runtime = read_json(AI / 'runtime.json', {})
runtime.update({
    'brand': '洪盛集藏',
    'mode': 'autonomous-safe',
    'cycle': 'scheduled',
    'lastRun': now,
    'status': 'ok',
    'tasks': [
        '检查公开AI发现资源',
        '检查知识库与数字档案',
        '生成运行健康报告',
        '维护运行日志'
    ],
    'nextLayer': '连接经过授权的公开内容源与AI模型后，生成内容审核队列'
})
(AI / 'runtime.json').write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

log_path = AI / 'activity-log.json'
logs = read_json(log_path, [])
if not isinstance(logs, list):
    logs = []
logs.append({'time': now, 'event': 'agent_cycle_completed', 'status': 'ok', 'mode': 'autonomous-safe', 'knowledgeFiles': len(knowledge_files)})
log_path.write_text(json.dumps(logs[-100:], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

(GEN / 'README.md').write_text('''# 洪盛集藏 AI Agent 输出区\n\nAgent 每轮运行产生运行报告和后续任务状态。\n\n自动发布前必须经过来源、版权、时效性和内容质量检查；AI不单独作出真伪、评级或正式报价结论。\n''', encoding='utf-8')
print(f'洪盛集藏 AI Agent cycle completed: {now}')
