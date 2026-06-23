import logging
import os
import uuid
from pathlib import Path

from flask import Flask, Response, g, jsonify, render_template, request, send_from_directory, stream_with_context
from flask_cors import CORS

from clients.anthropic_client import AnthropicClient
from config import AppConfig
from services.chat_service import ChatService
from services.conversation_store import ConversationStore
from services.dev_reload_service import DevReloadService
from services.intent_router import IntentRouter, KeyPool
from services.request_context import set_auth_header, set_request_id
from services.auth_identity_service import AuthIdentityService
from services.skill_service import SkillService
from services.tool_service import ToolService
from tools.geocode_tool import GeocodeTool
from tools.tavily_search_tool import TavilySearchTool
from tools.time_tool import TimeTool
from tools.weather_tool import WeatherTool


DEFAULT_SUGGESTIONS = [
    "check my booking status",
    "can booking BOOK20250401001 be canceled",
    "top properties in Shenzhen Nanshan",
    "payment status for booking 1024",
    "unread notifications for user 12",
    "available room types for property 23",
]

CUSTOM_SUGGESTIONS = os.getenv("AI_SERVICE_SUGGESTIONS", "")


def get_suggestions():
    if CUSTOM_SUGGESTIONS:
        return [s.strip() for s in CUSTOM_SUGGESTIONS.split("|") if s.strip()]
    return DEFAULT_SUGGESTIONS

SYSTEM_PROMPT = """You are the FindMyBed customer service assistant.
Always answer in Chinese.
You can handle property, room type, booking, payment, review, notification, coupon, merchant and user related questions.
You may also use web search and weather tools for external real-time information.
When a question requires concrete platform data, prefer backend tools and never fabricate results.
Give the conclusion first, then the key evidence."""


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
CORS(app, resources={r"/*": {"origins": "*"}})

config = AppConfig()
logging.basicConfig(level=getattr(logging, config.log_level(), logging.INFO))
logger = logging.getLogger(__name__)
dev_reload_service = DevReloadService(
    [
        Path(__file__),
        Path(app.root_path) / "templates" / "index.html",
    ]
)
search_tool = TavilySearchTool(config)
weather_tool = WeatherTool(config)
time_tool = TimeTool()
geocode_tool = GeocodeTool(config)
tool_service = ToolService(
    config,
    search_tool=search_tool,
    weather_tool=weather_tool,
    time_tool=time_tool,
    geocode_tool=geocode_tool,
)
auth_identity_service = AuthIdentityService(tool_service.backend_api_service)
conversation_store = ConversationStore(
    ttl_seconds=config.conversation_ttl_seconds(),
    max_messages=config.conversation_max_messages(),
    file_path=config.conversation_store_path(),
)
xiaomi_keys = config.xiaomi_api_keys()
intent_router = (
    IntentRouter(
        key_pool=KeyPool(xiaomi_keys),
        base_url=config.xiaomi_base_url(),
        model=config.xiaomi_model(),
    )
    if xiaomi_keys
    else None
)
skill_service = SkillService(tool_service, intent_router=intent_router)
chat_service = ChatService(
    model_client=AnthropicClient(config, SYSTEM_PROMPT),
    tool_service=tool_service,
    skill_service=skill_service,
    default_system_prompt=SYSTEM_PROMPT,
    config=config,
    conversation_store=conversation_store,
)


@app.before_request
def bind_request_id():
    request_id = request.headers.get(config.request_id_header()) or uuid.uuid4().hex
    g.request_id = request_id
    set_request_id(request_id)
    set_auth_header(request.headers.get("Authorization"))


@app.after_request
def attach_request_id(response):
    response.headers[config.request_id_header()] = getattr(g, "request_id", "")
    return response


@app.teardown_request
def clear_request_id(_exc):
    set_request_id(None)
    set_auth_header(None)


@app.get("/")
def index():
    static_copilot_index = Path(app.root_path) / "static" / "copilot" / "index.html"
    if static_copilot_index.exists():
        return send_from_directory(static_copilot_index.parent, "index.html")
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/conversations")
def list_conversations():
    """Return list of active conversation IDs."""
    ids = conversation_store.list_ids()
    return jsonify({"conversationIds": ids, "count": len(ids)})


@app.get("/conversations/<conversation_id>/messages")
def get_conversation_messages(conversation_id):
    """Return stored messages for a specific conversation."""
    messages = conversation_store.get_messages(conversation_id)
    return jsonify(
        {
            "conversationId": conversation_id,
            "messages": messages,
            "count": len(messages),
        }
    )


@app.get("/__dev_reload__")
def dev_reload():
    return jsonify(
        {
            "reloadToken": dev_reload_service.token(),
            "enabled": config.live_reload_enabled(),
        }
    )


@app.get("/suggestions")
def suggestions():
    return jsonify(get_suggestions())


@app.get("/skills")
def skills():
    return jsonify(chat_service.list_skills())


@app.post("/skills/route")
def route_skills():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    user_context = resolve_user_context(payload)

    if not message:
        return jsonify({"error": "message is required"}), 400

    return jsonify(chat_service.route(message, user_context=user_context))


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    user_context = resolve_user_context(payload)
    conversation_id = payload.get("conversationId") or uuid.uuid4().hex
    pending_action = payload.get("pendingAction")

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        result = chat_service.chat(
            message,
            user_context=user_context,
            conversation_id=conversation_id,
            pending_action=pending_action,
        )
        return jsonify(
            {
                "conversationId": conversation_id,
                "answer": result["answer"],
                "source": result["source"],
                "route": result["route"],
                "recommendations": result.get("recommendations"),
                "pendingAction": result.get("pending_action"),
                "requestId": getattr(g, "request_id", None),
            }
        )
    except Exception as exc:
        logger.exception("chat_request_failed request_id=%s", getattr(g, "request_id", "-"))
        return jsonify(
            {
                "conversationId": conversation_id,
                "answer": f"请求失败：{exc}",
                "source": "service-error",
                "recommendations": None,
                "requestId": getattr(g, "request_id", None),
            }
        ), 500


@app.post("/chat/stream")
def chat_stream():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    user_context = resolve_user_context(payload)
    conversation_id = payload.get("conversationId") or uuid.uuid4().hex
    pending_action = payload.get("pendingAction")

    if not message:
        return jsonify({"error": "message is required"}), 400

    @stream_with_context
    def generate():
        try:
            result, events = chat_service.stream_chat(
                message,
                user_context=user_context,
                conversation_id=conversation_id,
                pending_action=pending_action,
            )
            yield f"data: {jsonify_event({'type': 'meta', 'conversationId': conversation_id, 'route': result['route'], 'requestId': getattr(g, 'request_id', None)})}\n\n"
            for event in events:
                if event.get("type") == "chunk":
                    yield f"data: {jsonify_event(event)}\n\n"
                    continue
                if event.get("type") in {"status", "tool_start", "tool_end"}:
                    yield f"data: {jsonify_event(event)}\n\n"
                    continue
                if event.get("type") == "done":
                    yield f"data: {jsonify_event({'type': 'done', 'source': event.get('source'), 'route': event.get('route'), 'answer': event.get('answer'), 'recommendations': event.get('recommendations'), 'pendingAction': event.get('pending_action')})}\n\n"
                    continue
        except Exception as exc:
            logger.exception("chat_stream_failed request_id=%s", getattr(g, "request_id", "-"))
            yield f"data: {jsonify_event({'type': 'error', 'error': str(exc)})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def jsonify_event(payload):
    import json

    return json.dumps(payload, ensure_ascii=False)


def resolve_user_context(payload):
    fallback_user_context = payload.get("userContext") if config.allow_mock_user_context() else None
    return auth_identity_service.resolve_user_context(
        request.headers.get("Authorization"),
        fallback_user_context=fallback_user_context,
    )


if __name__ == "__main__":
    app.run(
        host=config.app_host(),
        port=config.app_port(),
        debug=config.app_debug(),
    )
