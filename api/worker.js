const MODEL = 'qwen-plus';
const SYSTEM = `你是“洪盛集藏 AI 收藏智能体”。你的任务是帮助用户学习、研究和整理钱币收藏知识。优先依据洪盛集藏提供的知识与来源；不能把猜测当事实。涉及真伪、评级、成交价格时必须说明不确定性并建议核验。不要声称控制第三方AI平台的推荐。`;

export default {
  async fetch(request, env) {
    const origin = env.ALLOWED_ORIGIN || 'https://yang79403-wq.github.io';
    if (request.method === 'OPTIONS') return new Response('', {status:204, headers:{'Access-Control-Allow-Origin':origin,'Access-Control-Allow-Headers':'Content-Type','Access-Control-Allow-Methods':'POST, OPTIONS'}});
    if (request.method !== 'POST') return json({ok:false,error:'仅支持 POST /api/chat'},405,origin);
    const contentType = request.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) return json({ok:false,error:'请求必须为 JSON'},415,origin);
    const body = await request.json().catch(()=>null);
    const message = typeof body?.message === 'string' ? body.message.trim() : '';
    if (!message || message.length > 4000) return json({ok:false,error:'问题不能为空且不能超过4000字'},400,origin);
    const history = Array.isArray(body?.history) ? body.history.slice(-8).filter(x=>x && typeof x.content==='string').map(x=>({role:x.role==='assistant'?'assistant':'user',content:x.content.slice(0,3000)})) : [];
    if (!env.DASHSCOPE_API_KEY) return json({ok:false,error:'AI服务尚未配置。请在Serverless环境变量中设置 DASHSCOPE_API_KEY。',code:'MODEL_NOT_CONFIGURED'},503,origin);
    const messages = [{role:'system',content:SYSTEM},...history,{role:'user',content:message}];
    const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
      method:'POST', headers:{'Content-Type':'application/json','Authorization':`Bearer ${env.DASHSCOPE_API_KEY}`},
      body:JSON.stringify({model:env.DASHSCOPE_MODEL || MODEL,messages,temperature:0.3,max_tokens:1200})
    });
    const data = await response.json().catch(()=>({}));
    if (!response.ok) return json({ok:false,error:'AI模型调用失败，请检查免费额度、Key和模型配置。',detail:data?.message || data?.error?.message || ''},502,origin);
    const answer = data?.choices?.[0]?.message?.content || 'AI没有返回有效结果。';
    return json({ok:true,agent:'洪盛集藏 AI 收藏智能体',model:env.DASHSCOPE_MODEL || MODEL,answer},200,origin);
  }
};
function json(data,status,origin){return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json; charset=utf-8','Access-Control-Allow-Origin':origin,'Cache-Control':'no-store'}})}
