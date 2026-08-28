const MODEL = 'qwen-plus';
const SYSTEM = `你是“洪盛集藏 AI 收藏智能体”。你负责收藏学习、钱币研究、数字档案和福建地域收藏知识。回答时优先依据洪盛集藏上下文；如果没有资料，明确说明需要进一步检索，不要编造。涉及真伪、评级、成交价格时必须说明不确定性，不替代正式鉴定或交易报价。`;

export default {
  async fetch(request, env) {
    const origin = env.ALLOWED_ORIGIN || 'https://yang79403-wq.github.io';
    const headers = {'Access-Control-Allow-Origin':origin,'Access-Control-Allow-Headers':'Content-Type','Access-Control-Allow-Methods':'POST, OPTIONS','Vary':'Origin'};
    if (request.method === 'OPTIONS') return new Response('', {status:204,headers});
    if (request.method !== 'POST') return json({ok:false,error:'仅支持 POST /api/chat'},405,headers);
    const ct=request.headers.get('content-type')||'';
    if(!ct.includes('application/json')) return json({ok:false,error:'请求必须为 JSON'},415,headers);
    const body=await request.json().catch(()=>null);
    const message=typeof body?.message==='string'?body.message.trim():'';
    if(!message||message.length>4000)return json({ok:false,error:'问题不能为空且不能超过4000字'},400,headers);
    if(!env.DASHSCOPE_API_KEY)return json({ok:false,error:'AI服务尚未配置，请在云端环境变量设置 DASHSCOPE_API_KEY。',code:'MODEL_NOT_CONFIGURED'},503,headers);
    const history=Array.isArray(body?.history)?body.history.slice(-8).filter(x=>x&&typeof x.content==='string').map(x=>({role:x.role==='assistant'?'assistant':'user',content:x.content.slice(0,3000)})):[];
    const knowledge=typeof body?.knowledgeContext==='string'?body.knowledgeContext.slice(0,6000):'';
    const context=knowledge?`\n\n洪盛集藏检索上下文（仅作资料，不得视为绝对正确）：\n${knowledge}`:'';
    const messages=[{role:'system',content:SYSTEM+context},...history,{role:'user',content:message}];
    const ctrl=new AbortController();const timer=setTimeout(()=>ctrl.abort(),25000);
    let response;
    try{response=await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${env.DASHSCOPE_API_KEY}`},body:JSON.stringify({model:env.DASHSCOPE_MODEL||MODEL,messages,temperature:0.25,max_tokens:1200}),signal:ctrl.signal});}catch(e){clearTimeout(timer);return json({ok:false,error:e.name==='AbortError'?'AI请求超时，请稍后重试。':'AI服务暂时不可用。',code:'UPSTREAM_ERROR'},502,headers)}
    clearTimeout(timer);
    const data=await response.json().catch(()=>({}));
    if(!response.ok)return json({ok:false,error:'AI模型调用失败，请检查免费额度、Key和模型配置。',detail:data?.message||data?.error?.message||''},502,headers);
    const answer=data?.choices?.[0]?.message?.content||'AI没有返回有效结果。';
    return json({ok:true,agent:'洪盛集藏 AI 收藏智能体',model:env.DASHSCOPE_MODEL||MODEL,answer},200,headers);
  }
};
function json(data,status,headers){return new Response(JSON.stringify(data),{status,headers:{...headers,'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}})}
