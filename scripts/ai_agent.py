import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / 'ai'
GEN = AI / 'generated'
GEN.mkdir(parents=True, exist_ok=True)

now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

# Safe autonomous baseline: maintain machine-readable runtime state and an audit trail.
# External AI APIs are intentionally optional. Add provider credentials later through
# GitHub Actions Secrets; never hard-code API keys in the repository.
config = {
    'brand': '洪盛集藏',
    'mode': 'autonomous-safe',
    'cycle': 'scheduled',
    'tasks': [
        '检查AI索引资源',
        '检查知识库与数字档案',
        '维护运行日志',
        '为后续AI采集/整理任务准备输出目录'
    ],
    'nextLayer': '连接经过授权的公开内容源与AI模型后，再执行内容发现、整理和审核队列生成',
    'lastRun': now
}
(AI / 'runtime.json').write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

log_path = AI / 'activity-log.json'
try:
    logs = json.loads(log_path.read_text(encoding='utf-8')) if log_path.exists() else []
    if not isinstance(logs, list): logs = []
except Exception:
    logs = []
logs.append({'time': now, 'event': 'agent_cycle_completed', 'status': 'ok', 'mode': 'autonomous-safe'})
logs = logs[-100:]
log_path.write_text(json.dumps(logs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

(GEN / 'README.md').write_text('''# 洪盛集藏 AI Agent 输出区\n\n这里保存经过 Agent 流程生成、准备进入人工审核或公开发布的数据。\n\n## 安全规则\n- 不在代码中保存 API Key。\n- 外部内容需要遵守来源、版权和站点规则。\n- 时效性资讯必须记录日期与来源。\n- AI 不单独作出真伪、评级和正式报价结论。\n- 自动生成内容默认进入审核流程，而不是直接覆盖核心知识档案。\n''', encoding='utf-8')

print(f'AI Agent cycle completed: {now}')
