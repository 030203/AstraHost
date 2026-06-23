import json
import logging
from types import SimpleNamespace

import requests
from anthropic import Anthropic

from services.request_context import get_request_id


logger = logging.getLogger(__name__)


class AnthropicClient:
    def __init__(self, config, system_prompt=""):
        self.config = config
        self.system_prompt = system_prompt
        self.api_key = self.config.anthropic_api_key()
        self.base_url = self.config.anthropic_base_url()
        self.client = self._build_sdk_client() if self.api_key else None

    def create_message(self, messages, tools, system_prompt=None):
        resolved_system_prompt = system_prompt if system_prompt is not None else self.system_prompt
        if self.client is not None:
            try:
                return self.client.messages.create(
                    model=self.config.anthropic_model(),
                    max_tokens=self.config.anthropic_max_tokens(),
                    system=resolved_system_prompt,
                    messages=messages,
                    tools=tools,
                )
            except Exception as exc:
                logger.exception(
                    "anthropic_sdk_request_failed model=%s request_id=%s",
                    self.config.anthropic_model(),
                    get_request_id() or "-",
                )
                raise ValueError(f"Model request failed: {exc.__class__.__name__}") from exc
        return self._create_message_via_http(messages, tools, resolved_system_prompt)

    def stream_message(self, messages, tools, system_prompt=None):
        resolved_system_prompt = system_prompt if system_prompt is not None else self.system_prompt
        if self.client is not None and hasattr(self.client.messages, "stream"):
            yield from self._stream_message_via_sdk(messages, tools, resolved_system_prompt)
            return
        yield from self._stream_message_via_http(messages, tools, resolved_system_prompt)

    def _build_sdk_client(self):
        client_kwargs = {
            "base_url": self.base_url,
            "timeout": self.config.anthropic_timeout(),
        }
        if self.api_key:
            client_kwargs["api_key"] = self.api_key
        return Anthropic(**client_kwargs)

    def _create_message_via_http(self, messages, tools, system_prompt):
        request_id = get_request_id()
        try:
            response = requests.post(
                self._messages_url(),
                headers=self._http_headers(request_id=request_id),
                json={
                    "model": self.config.anthropic_model(),
                    "max_tokens": self.config.anthropic_max_tokens(),
                    "system": system_prompt,
                    "messages": messages,
                    "tools": tools,
                },
                timeout=self.config.anthropic_timeout(),
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "anthropic_http_request_failed model=%s request_id=%s",
                self.config.anthropic_model(),
                request_id or "-",
            )
            raise ValueError(f"Model request failed: {exc.__class__.__name__}") from exc
        return self._normalize_response(self._parse_json_response(response))

    def _stream_message_via_sdk(self, messages, tools, system_prompt):
        request_id = get_request_id()
        try:
            with self.client.messages.stream(
                model=self.config.anthropic_model(),
                max_tokens=self.config.anthropic_max_tokens(),
                system=system_prompt,
                messages=messages,
                tools=tools,
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        yield {"type": "text_delta", "text": text}
                final_message = stream.get_final_message()
        except Exception as exc:
            logger.exception(
                "anthropic_sdk_stream_failed model=%s request_id=%s",
                self.config.anthropic_model(),
                request_id or "-",
            )
            raise ValueError(f"Model stream failed: {exc.__class__.__name__}") from exc

        yield {
            "type": "final_response",
            "response": self._normalize_sdk_response(final_message),
        }

    def _stream_message_via_http(self, messages, tools, system_prompt):
        request_id = get_request_id()
        try:
            response = requests.post(
                self._messages_url(),
                headers=self._http_headers(request_id=request_id),
                json={
                    "model": self.config.anthropic_model(),
                    "max_tokens": self.config.anthropic_max_tokens(),
                    "system": system_prompt,
                    "messages": messages,
                    "tools": tools,
                    "stream": True,
                },
                stream=True,
                timeout=self.config.anthropic_timeout(),
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception(
                "anthropic_http_stream_failed model=%s request_id=%s",
                self.config.anthropic_model(),
                request_id or "-",
            )
            raise ValueError(f"Model stream failed: {exc.__class__.__name__}") from exc

        content_type = (response.headers.get("Content-Type") or "").lower()
        if "text/event-stream" not in content_type:
            normalized = self._normalize_response(self._parse_json_response(response))
            for block in normalized.content:
                if getattr(block, "type", "") == "text" and getattr(block, "text", ""):
                    yield {"type": "text_delta", "text": block.text}
            yield {"type": "final_response", "response": normalized}
            return

        yield from self._iter_anthropic_sse(response)

    def _iter_anthropic_sse(self, response):
        blocks = {}
        stop_reason = None
        event_name = None
        data_lines = []

        def flush_event():
            nonlocal event_name, data_lines, stop_reason
            if not data_lines:
                event_name = None
                return None
            payload_text = "\n".join(data_lines).strip()
            data_lines = []
            if not payload_text:
                event_name = None
                return None
            if payload_text == "[DONE]":
                event_name = None
                return "done"
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError:
                event_name = None
                return None

            payload_type = payload.get("type") or event_name
            event_name = None

            if payload_type == "content_block_start":
                index = payload.get("index")
                block = payload.get("content_block") or {}
                blocks[index] = {
                    "type": block.get("type"),
                    "text": block.get("text") or "",
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input_json_chunks": [],
                    "input": block.get("input"),
                }
                return None

            if payload_type == "content_block_delta":
                index = payload.get("index")
                delta = payload.get("delta") or {}
                block_state = blocks.setdefault(
                    index,
                    {
                        "type": None,
                        "text": "",
                        "id": None,
                        "name": None,
                        "input_json_chunks": [],
                        "input": None,
                    },
                )
                delta_type = delta.get("type")
                if delta_type == "text_delta":
                    text = delta.get("text") or ""
                    block_state["text"] += text
                    if text:
                        return {"type": "text_delta", "text": text}
                elif delta_type == "input_json_delta":
                    block_state["input_json_chunks"].append(delta.get("partial_json") or "")
                return None

            if payload_type == "message_delta":
                stop_reason = (payload.get("delta") or {}).get("stop_reason", stop_reason)
                return None

            if payload_type == "message_stop":
                return "done"

            if payload_type == "error":
                err = payload.get("error") or {}
                message = err.get("message") or payload_text
                raise ValueError(f"Model stream error: {message}")

            return None

        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.rstrip("\r")
            if not line:
                flushed = flush_event()
                if flushed == "done":
                    break
                if isinstance(flushed, dict):
                    yield flushed
                continue
            if line.startswith("event:"):
                event_name = line[6:].strip()
                continue
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())

        if data_lines:
            flushed = flush_event()
            if isinstance(flushed, dict):
                yield flushed

        content_blocks = []
        for index in sorted(blocks.keys()):
            block = blocks[index]
            normalized_input = block.get("input")
            if normalized_input is None and block.get("input_json_chunks"):
                joined = "".join(block["input_json_chunks"]).strip()
                if joined:
                    try:
                        normalized_input = json.loads(joined)
                    except json.JSONDecodeError:
                        normalized_input = {}
            content_blocks.append(
                SimpleNamespace(
                    type=block.get("type"),
                    text=block.get("text") or "",
                    id=block.get("id"),
                    name=block.get("name"),
                    input=normalized_input,
                )
            )

        yield {
            "type": "final_response",
            "response": SimpleNamespace(content=content_blocks, stop_reason=stop_reason),
        }

    def _messages_url(self):
        normalized = (self.base_url or "").rstrip("/")
        if normalized.endswith("/messages"):
            return normalized
        if normalized:
            return f"{normalized}/messages"
        return "https://api.anthropic.com/v1/messages"

    def _http_headers(self, request_id=None):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        if request_id:
            headers[self.config.request_id_header()] = request_id
        return headers

    def _parse_json_response(self, response):
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            content_type = response.headers.get("Content-Type", "")
            body_preview = response.text[:500].strip()
            raise ValueError(
                "Model endpoint did not return valid JSON. "
                f"status={response.status_code}, "
                f"content_type={content_type or 'unknown'}, "
                f"body_preview={body_preview or '<empty>'}"
            ) from exc

    def _normalize_response(self, payload):
        content = []
        for block in payload.get("content", []):
            content.append(
                SimpleNamespace(
                    type=block.get("type"),
                    text=block.get("text"),
                    id=block.get("id"),
                    name=block.get("name"),
                    input=block.get("input"),
                )
            )
        return SimpleNamespace(
            content=content,
            stop_reason=payload.get("stop_reason"),
        )

    def _normalize_sdk_response(self, message):
        content = []
        for block in getattr(message, "content", []) or []:
            content.append(
                SimpleNamespace(
                    type=getattr(block, "type", None),
                    text=getattr(block, "text", None),
                    id=getattr(block, "id", None),
                    name=getattr(block, "name", None),
                    input=getattr(block, "input", None),
                )
            )
        return SimpleNamespace(
            content=content,
            stop_reason=getattr(message, "stop_reason", None),
        )
