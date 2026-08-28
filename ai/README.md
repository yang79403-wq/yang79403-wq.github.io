# 洪盛集藏 AI Agent V1.0

## 产品定位
洪盛集藏不是传统收藏网站外挂聊天框，而是以 AI 为入口的收藏知识与用户需求连接平台。

## 前台
- `/ai/collector-assistant.html`：AI收藏智能体
- `/ai/ai-home.html`：AI收藏入口
- `/ai/agent-dashboard.html`：Agent运行控制台
- `/ai/market-revolution.html`：AI行业模式

## Agent链路
用户问题 → 意图识别 → 知识检索 → 钱币实体 → 数字档案 → 关联研究 → 质量控制 → 内容沉淀 → 索引发现

## 自动运行
GitHub Actions 定时执行 `scripts/ai_agent.py` 与 `scripts/agent_discovery.py`。

## 数据原则
1. 来源可追溯。
2. 时效资料标记日期。
3. AI不得虚构事实。
4. 真伪、正式鉴定、价格等高风险判断保留人工审核。
5. 不绕过第三方网站的登录、验证码、付费墙或访问限制。
6. 不承诺控制任何第三方AI的排序或推荐。

## 当前边界
静态 GitHub Pages 可以提供完整前台、知识导航、数据展示和 Agent 状态；真正的大模型推理、图片视觉模型和受控联网采集需要后端服务与相应 API/授权配置。