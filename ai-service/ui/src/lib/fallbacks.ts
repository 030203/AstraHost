export const DEFAULT_GREETING =
  "你好，我是 AstraHost AI 智能管家。告诉我房源、订单、支付或客诉需求，我会先理解，再调用能力处理。";

export const DEFAULT_SUGGESTIONS = [
  "推荐今晚可入住、带厨房的家庭房源",
  "帮我处理延迟入住的订单咨询",
  "整理这笔支付失败可能的原因",
  "写一段安抚客人的客服回复"
];

export const QUICK_ACTIONS = [
  {
    key: "property",
    title: "推荐房源",
    subtitle: "按位置、预算、设施和入住人群筛选推荐",
    prompt: "推荐东京新宿区，适合 4 人家庭入住的酒店，预算每晚 1000-1500 元，带厨房和洗衣机"
  },
  {
    key: "order",
    title: "处理订单",
    subtitle: "查看订单进度、变更影响与下一步处置建议",
    prompt: "帮我处理一笔今晚延迟入住的订单，先说明需要核对哪些信息"
  },
  {
    key: "payment",
    title: "处理支付",
    subtitle: "排查支付失败、待支付与退款相关问题",
    prompt: "有一笔订单支付失败了，帮我先整理客服应该如何排查并回复用户"
  },
  {
    key: "reply",
    title: "客户沟通",
    subtitle: "生成更自然、稳妥的客服回复与安抚话术",
    prompt: "帮我写一段客服回复，安抚因延迟入住而不满的客人，并提供补偿建议"
  }
];

export const AGENT_BASE_STEPS = [
  { key: "understand", label: "理解需求", detail: "解析目标、约束与紧急程度" },
  { key: "preference", label: "整理上下文", detail: "识别身份、偏好与已知业务条件" },
  { key: "search", label: "调用工具", detail: "按需查询订单、支付或房源信息" },
  { key: "sort", label: "核对结果", detail: "汇总工具返回并判断下一步动作" },
  { key: "result", label: "生成回复", detail: "输出结论、建议与可执行操作" }
];

export const FALLBACK_CARD_IMAGE =
  "data:image/svg+xml;charset=UTF-8," +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480">
      <defs>
        <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#fff9f4"/>
          <stop offset="100%" stop-color="#eaded3"/>
        </linearGradient>
      </defs>
      <rect width="640" height="480" fill="url(#bg)"/>
      <g fill="none" stroke="#bc9b88" stroke-width="16" stroke-linecap="round" stroke-linejoin="round">
        <path d="M116 332l104-108 84 84 116-132 104 156"/>
        <circle cx="214" cy="172" r="28"/>
      </g>
    </svg>
  `);
