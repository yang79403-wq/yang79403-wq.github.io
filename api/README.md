# 洪盛集藏 AI 安全后端接口层

本目录是实时 AI Agent 后端部署模板。GitHub Pages 不保存 API Key；真实 Key 只放在 Serverless 平台 Secret/Environment Variable。

## 推荐免费起步

使用 Cloudflare Workers / Pages Functions 等 Serverless 免费额度内方案。

环境变量：
- `DASHSCOPE_API_KEY`
- `DASHSCOPE_MODEL`，默认 `qwen-plus`
- `ALLOWED_ORIGIN`，默认 `https://yang79403-wq.github.io`

接口：`POST /api/chat`

请求示例：`{"message":"袁大头三年有哪些版别？","history":[]}`

返回示例：`{"ok":true,"answer":"...","agent":"洪盛集藏 AI 收藏智能体"}`

生产安全要求：限制请求体、校验 Origin、限流、超时处理，不把用户隐私写入公开仓库。

注意：这是部署模板。真正实时 AI 服务需要在 Serverless 账号中部署并配置密钥。