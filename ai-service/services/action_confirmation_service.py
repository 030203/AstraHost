from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class PendingAction:
    token: str
    tool_name: str
    arguments: dict
    user_fingerprint: str
    created_at: datetime
    expires_at: datetime
    summary: dict | None = None

    def to_response(self):
        summary = dict(self.summary or {})
        return {
            "token": self.token,
            "tool": self.tool_name,
            "arguments": self.arguments,
            "expires_at": self.expires_at.isoformat().replace("+00:00", "Z"),
            "confirmation_text": summary.get("confirmation_text") or f"确认执行动作 {self.token}",
            "summary": summary,
        }


class ActionConfirmationService:
    def __init__(self, ttl_seconds=300, token_factory=None, clock=None):
        self.ttl_seconds = int(ttl_seconds or 300)
        self.token_factory = token_factory or self._default_token
        self.clock = clock or self._now
        self._pending_actions = {}

    def create(self, tool_name, arguments, user_context=None, summary=None):
        self._remove_expired()
        now = self.clock()
        pending_action = PendingAction(
            token=self.token_factory(),
            tool_name=tool_name,
            arguments=self._normalize_arguments(arguments),
            user_fingerprint=self._user_fingerprint(user_context),
            created_at=now,
            expires_at=now + timedelta(seconds=self.ttl_seconds),
            summary=self._normalize_summary(summary),
        )
        self._pending_actions[pending_action.token] = pending_action
        return pending_action

    def consume(self, token, tool_name, arguments, user_context=None):
        self._remove_expired()
        pending_action = self._pending_actions.get(str(token or "").strip())
        if pending_action is None:
            raise ValueError("确认令牌无效或已过期。")

        if pending_action.tool_name != tool_name:
            raise ValueError("确认令牌与当前工具不匹配。")

        normalized_arguments = self._normalize_arguments(arguments)
        if normalized_arguments and pending_action.arguments != normalized_arguments:
            raise ValueError("确认令牌与当前操作参数不匹配。")
        if pending_action.user_fingerprint != self._user_fingerprint(user_context):
            raise ValueError("确认令牌与当前用户不匹配。")

        self._pending_actions.pop(pending_action.token, None)
        return pending_action

    def _remove_expired(self):
        now = self.clock()
        expired_tokens = [
            token
            for token, pending_action in self._pending_actions.items()
            if pending_action.expires_at <= now
        ]
        for token in expired_tokens:
            self._pending_actions.pop(token, None)

    def _normalize_arguments(self, arguments):
        if not isinstance(arguments, dict):
            return {}
        return json.loads(json.dumps(arguments, sort_keys=True, ensure_ascii=False))

    def _normalize_summary(self, summary):
        if not isinstance(summary, dict):
            return {}
        return json.loads(json.dumps(summary, sort_keys=True, ensure_ascii=False))

    def _user_fingerprint(self, user_context):
        payload = user_context or {}
        parts = [
            str(payload.get("id") or ""),
            str(payload.get("role") or "").upper(),
            str(payload.get("merchantId") or ""),
        ]
        return "|".join(parts)

    @staticmethod
    def _default_token():
        return f"act_{secrets.token_urlsafe(16)}"

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)
