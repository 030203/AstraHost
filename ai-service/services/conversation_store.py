from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ConversationState:
    conversation_id: str
    messages: list[dict]
    updated_at: datetime
    expires_at: datetime


class ConversationStore:
    _STORAGE_VERSION = 1

    def __init__(self, ttl_seconds=86400, max_messages=20, clock=None, file_path=None):
        self.ttl_seconds = int(ttl_seconds or 86400)
        self.max_messages = max(1, int(max_messages or 20))
        self.clock = clock or self._now
        self.file_path = file_path or os.getenv("CONVERSATION_STORE_PATH", "")
        self._store = {}
        self._lock = threading.Lock()
        self._load_from_file()

    # ── public API ──────────────────────────────────────────────

    def get_messages(self, conversation_id):
        self._remove_expired()
        state = self._store.get(str(conversation_id or "").strip())
        if state is None:
            return []
        return [self._clone_message(message) for message in state.messages]

    def append_messages(self, conversation_id, new_messages):
        normalized_id = str(conversation_id or "").strip()
        if not normalized_id:
            return

        self._remove_expired()
        now = self.clock()
        existing = self._store.get(normalized_id)
        messages = existing.messages[:] if existing is not None else []
        messages.extend(
            self._normalize_message(message)
            for message in (new_messages or [])
            if self._normalize_message(message) is not None
        )
        messages = messages[-self.max_messages :]
        self._store[normalized_id] = ConversationState(
            conversation_id=normalized_id,
            messages=messages,
            updated_at=now,
            expires_at=now + timedelta(seconds=self.ttl_seconds),
        )
        self._save_to_file()

    def list_ids(self):
        """Return list of active conversation IDs, most recently updated first."""
        self._remove_expired()
        return sorted(
            self._store.keys(),
            key=lambda cid: self._store[cid].updated_at,
            reverse=True,
        )

    def clear(self, conversation_id):
        self._store.pop(str(conversation_id or "").strip(), None)
        self._save_to_file()

    # ── file persistence ────────────────────────────────────────

    def _resolve_file_path(self):
        path = (self.file_path or "").strip()
        if path:
            return path
        return os.path.join(os.path.dirname(__file__), "..", "data", "conversations.json")

    def _load_from_file(self):
        path = self._resolve_file_path()
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except Exception:
            return

        if not isinstance(payload, dict):
            return
        records = payload.get("conversations")
        if not isinstance(records, list):
            return

        now = self.clock()
        loaded = 0
        for record in records:
            try:
                conv_id = str(record.get("conversation_id") or "").strip()
                if not conv_id:
                    continue
                messages = record.get("messages")
                if not isinstance(messages, list):
                    continue
                normalized = [
                    msg
                    for msg in (self._normalize_message(m) for m in messages)
                    if msg is not None
                ]
                if not normalized:
                    continue
                updated_at = self._parse_datetime(record.get("updated_at")) or now
                expires_at = self._parse_datetime(record.get("expires_at")) or (
                    updated_at + timedelta(seconds=self.ttl_seconds)
                )
                # skip already-expired records
                if expires_at <= now:
                    continue
                self._store[conv_id] = ConversationState(
                    conversation_id=conv_id,
                    messages=normalized[-self.max_messages :],
                    updated_at=updated_at,
                    expires_at=expires_at,
                )
                loaded += 1
            except Exception:
                continue

    def _save_to_file(self):
        path = self._resolve_file_path()
        if not path:
            return

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except OSError:
            pass

        records = []
        for state in self._store.values():
            records.append(
                {
                    "conversation_id": state.conversation_id,
                    "messages": [
                        self._clone_message(m) for m in state.messages
                    ],
                    "updated_at": self._format_datetime(state.updated_at),
                    "expires_at": self._format_datetime(state.expires_at),
                }
            )

        payload = {
            "version": self._STORAGE_VERSION,
            "updated_at": self._format_datetime(self.clock()),
            "conversations": records,
        }

        # thread-safe atomic write
        with self._lock:
            tmp_path = path + ".tmp"
            try:
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
                os.replace(tmp_path, path)
            except Exception:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    # ── internal helpers ────────────────────────────────────────

    def _remove_expired(self):
        now = self.clock()
        expired = [
            conversation_id
            for conversation_id, state in self._store.items()
            if state.expires_at <= now
        ]
        if not expired:
            return
        for conversation_id in expired:
            self._store.pop(conversation_id, None)
        self._save_to_file()

    @staticmethod
    def _normalize_message(message):
        if not isinstance(message, dict):
            return None
        role = str(message.get("role") or "").strip()
        if not role:
            return None
        content = message.get("content")
        if content is None:
            return None
        if isinstance(content, (dict, list)):
            normalized_content = content
        else:
            normalized_content = str(content)
        return {
            "role": role,
            "content": normalized_content,
        }

    @staticmethod
    def _clone_message(message):
        return {
            "role": message.get("role"),
            "content": message.get("content"),
        }

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    @staticmethod
    def _format_datetime(dt):
        return dt.isoformat()

    @staticmethod
    def _parse_datetime(value):
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
