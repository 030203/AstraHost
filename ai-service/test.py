import os

from anthropic import Anthropic
from dotenv import load_dotenv

SYSTEM_PROMPT = (
    "你是一个民宿客服与导购助手，请始终使用中文回答。"
    "你可以回答民宿推荐、入住准备、出行建议、平台常见问题等普通问题。"
    "如果用户询问实时订单、支付结果、库存、退款进度等需要后台系统的数据，"
    "明确说明你当前无法直接查询实时业务系统，并给出通用建议。"
    "不要编造订单状态、库存或平台内部数据。"
    "回答先给结论，再给简洁理由。"
)
load_dotenv(override=True)

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))

response = client.messages.create(
    model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
    max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000")),
    system=SYSTEM_PROMPT,
    messages=[{"role": "user","content": "你好，请介绍一下你自己",}],
    tools=[]
)
print(response)


