# 洪盛集藏 V9 后端

本目录提供可部署的 AI API 后端骨架。前端密钥永不写入 GitHub Pages。

## API
- GET `/health`
- POST `/api/ai/chat`
- POST `/api/ai/research`
- GET `/api/coins/search?q=`
- GET `/api/news`

## 部署
1. 安装 Cloudflare Wrangler。
2. 在本目录执行 `wrangler login`。
3. 执行 `wrangler deploy`。
4. 设置服务端密钥：`wrangler secret put AI_API_KEY`。
5. 可通过 `AI_BASE_URL` 与 `AI_MODEL` 使用兼容 Chat Completions 的模型服务。

## 数据库
`schema.sql` 为 D1/SQLite 初始结构，包含钱币、证据、行情记录、研究记录。

## 生产原则
- AI结果仅作研究辅助。
- 鉴定、估值、交易建议必须避免确定性表述。
- 报价、成交、流拍、撤拍、参考数据分层保存。
- 每条证据尽量保存来源、URL、日期和可信度。
- 只接入公开或获得授权的数据。
