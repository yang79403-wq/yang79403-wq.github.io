# 洪盛集藏 AI 后端 V11

本目录提供洪盛集藏 AI 钱币知识研究 API。前端密钥永不写入 GitHub Pages。

## API
- GET `/health`
- POST `/api/ai/chat`
- POST `/api/ai/research`
- POST `/api/ai/vision`
- GET `/api/coins/search?q=`
- GET `/api/news`
- GET `/api/market/summary`

## 当前能力
- AI研究：问题分类、研究路径、事实/推断/争议提示。
- Vision AI：上传钱币图片后提取研究线索，不输出确定性真伪、估值或交易结论。
- 知识搜索：优先读取 D1；D1 未绑定时自动使用内置知识种子，避免前端出现“空知识库”。
- 收藏防诈：支持来源核查、诱导话术识别、报价与成交区分、证据不足提示。

## D1 接入
`schema.sql` 提供 coins、evidence、market_records、research 四类基础表。

在 Cloudflare 创建 D1 后，将数据库绑定到 Worker 环境变量名 `DB`，再执行 schema.sql。不要把数据库 ID 或任何 AI 密钥写进前端页面。

## AI 配置
在 Cloudflare Worker 中设置：
- `AI_BASE_URL`：兼容 Chat Completions 的模型服务地址
- `AI_MODEL`：模型名称
- Secret：`AI_API_KEY`

## 生产原则
- AI 结果仅作知识学习和研究辅助。
- 图片分析不能替代实物鉴定。
- 不提供确定性鉴定、估值、买卖撮合或投资建议。
- 报价、成交、流拍、撤拍、参考数据必须分层保存。
- 每条证据尽量保存来源、URL、日期和可信度。
- 只接入公开或获得授权的数据。
