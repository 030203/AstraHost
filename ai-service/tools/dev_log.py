from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "dev-logs"

SECTIONS = {
    "goal": "今日目标",
    "done": "已完成",
    "todo": "待办",
    "decision": "决策记录",
    "block": "风险与阻塞",
    "verify": "验证记录",
    "file": "关联文件",
    "next": "下一步",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update the daily development log."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=tuple(SECTIONS),
        help="Log section to update. Omit to only ensure today's log exists.",
    )
    parser.add_argument(
        "--date",
        dest="log_date",
        help="Date in YYYY-MM-DD format. Defaults to local today.",
    )

    for command in SECTIONS:
        parser.add_argument(
            f"--{command}",
            dest=command,
            help=f"Text to append to section: {SECTIONS[command]}",
        )

    return parser.parse_args()


def resolve_date(raw: str | None) -> date:
    if not raw:
        return date.today()
    return date.fromisoformat(raw)


def log_path(log_date: date) -> Path:
    return LOG_DIR / f"{log_date.isoformat()}.md"


def template(log_date: date) -> str:
    return f"""# {log_date.isoformat()} 开发日志

## 今日目标

- 待补充。

## 已完成

- 待补充。

## 待办

- 待补充。

## 决策记录

- 待补充。

## 风险与阻塞

- 待补充。

## 验证记录

- 待补充。

## 关联文件

- 待补充。

## 下一步

- 待补充。
"""


def ensure_log(log_date: date) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = log_path(log_date)
    if not path.exists():
        path.write_text(template(log_date), encoding="utf-8")
    return path


def normalize_item(text: str) -> str:
    cleaned = " ".join(str(text).strip().split())
    if not cleaned:
        raise ValueError("Log item cannot be empty.")
    return f"- {cleaned}"


def append_to_section(path: Path, section_title: str, item: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    heading = f"## {section_title}"
    bullet = normalize_item(item)

    if bullet in lines:
        return

    try:
        heading_index = lines.index(heading)
    except ValueError:
        lines.extend(["", heading, "", bullet])
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return

    insert_at = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            insert_at = index
            break

    section_lines = lines[heading_index + 1:insert_at]
    cleaned_section = [
        line for line in section_lines if line.strip() != "- 待补充。"
    ]
    lines = (
        lines[:heading_index + 1]
        + cleaned_section
        + [bullet]
        + lines[insert_at:]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    current_date = resolve_date(args.log_date)
    path = ensure_log(current_date)

    if args.command:
        value = getattr(args, args.command) or ""
        append_to_section(path, SECTIONS[args.command], value)
        print(f"updated={path}")
    else:
        print(f"exists={path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

