from datetime import datetime, timedelta, timezone


class TimeTool:
    name = "get_current_time"
    description = "Get current date and time for a timezone, UTC offset, or local server time."
    input_schema = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "IANA timezone name, such as Asia/Shanghai or America/New_York. Optional.",
            },
            "utc_offset": {
                "type": "string",
                "description": "UTC offset like +08:00 or -05:00. Optional when timezone is not provided.",
            },
        },
        "required": [],
    }

    def execute(self, tool_input):
        timezone_name = str(tool_input.get("timezone") or "").strip()
        utc_offset = str(tool_input.get("utc_offset") or "").strip()

        tz = self._resolve_timezone(timezone_name, utc_offset)
        current = datetime.now(tz)
        offset_raw = current.strftime("%z")
        formatted_offset = ""
        if offset_raw:
            formatted_offset = f"{offset_raw[:3]}:{offset_raw[3:]}"

        return {
            "timezone": timezone_name or "",
            "utc_offset": formatted_offset,
            "iso_datetime": current.isoformat(),
            "date": current.strftime("%Y-%m-%d"),
            "time": current.strftime("%H:%M:%S"),
            "weekday": current.strftime("%A"),
        }

    def _resolve_timezone(self, timezone_name, utc_offset):
        if timezone_name:
            try:
                from zoneinfo import ZoneInfo

                return ZoneInfo(timezone_name)
            except Exception as exc:
                raise ValueError(f"无效时区：{timezone_name}") from exc

        if utc_offset:
            return self._parse_utc_offset(utc_offset)

        return datetime.now().astimezone().tzinfo or timezone.utc

    @staticmethod
    def _parse_utc_offset(value):
        normalized = value.strip()
        if len(normalized) != 6 or normalized[0] not in {"+", "-"} or normalized[3] != ":":
            raise ValueError("utc_offset 格式必须为 +08:00 或 -05:00")

        try:
            hours = int(normalized[1:3])
            minutes = int(normalized[4:6])
        except ValueError as exc:
            raise ValueError("utc_offset 包含无效数字") from exc

        if hours > 14 or minutes > 59:
            raise ValueError("utc_offset 超出有效范围")

        total_minutes = hours * 60 + minutes
        if normalized[0] == "-":
            total_minutes = -total_minutes
        return timezone(timedelta(minutes=total_minutes))
