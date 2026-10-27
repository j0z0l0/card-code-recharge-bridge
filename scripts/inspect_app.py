#!/usr/bin/env python3
"""Scan an application workspace and report integration signals.

This script is read-only. It produces evidence-backed hints, not final truth.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".next", ".nuxt", "dist", "build",
    "coverage", "vendor", ".venv", "venv", "env", "__pycache__", ".cache",
    ".pytest_cache", ".mypy_cache", ".turbo", "target", "bin", "obj", ".idea",
    ".vscode", ".DS_Store",
}
TEXT_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".java",
    ".kt", ".kts", ".php", ".rb", ".cs", ".swift", ".dart", ".sql", ".json",
    ".yaml", ".yml", ".toml", ".ini", ".env", ".md", ".html", ".vue", ".svelte",
}
MAX_FILE_BYTES = 768 * 1024
MAX_FILES = 18000

SIGNALS = {
    "auth": ["requireauth", "getuser", "session", "jwt", "login", "signup", "row level security"],
    "payment": ["payment", "checkout", "alipay", "wechatpay", "stripe", "paypal", "pay_url", "payurl"],
    "order": ["order_no", "orderno", "payments", "payment_orders", "createorder", "订单"],
    "redeem": ["redeem", "redemption", "redeem_code", "cdkey", "card_code", "voucher", "兑换码", "卡密"],
    "wallet": ["wallet", "balance", "ledger", "token_transaction", "credit", "quota", "余额", "灵石", "点数"],
    "entitlement": ["entitlement", "subscription", "membership", "user_passes", "pass_count", "权益", "会员", "次卡"],
    "product": ["product", "plan", "pricing", "price", "sku", "package", "goods", "商品", "档位", "套餐"],
    "admin": ["requireadmin", "admin", "audit_log", "role", "后台"],
    "idempotency": ["idempot", "reference_id", "unique", "on conflict", "幂等"],
    "webhook": ["webhook", "callback", "notify", "异步通知", "回调"],
    "iframe": ["iframe", "pay_url", "payurl", "收银台"],
    "rate_limit": ["ratelimit", "rate_limit", "hitlimit", "throttle", "限流"],
}

FRAMEWORK_HINTS = {
    "next": "Next.js",
    "react": "React",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "express": "Express",
    "fastify": "Fastify",
    "nestjs": "NestJS",
    "koa": "Koa",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "laravel": "Laravel",
    "spring": "Spring",
    "rails": "Rails",
    "gin": "Gin",
    "echo": "Echo",
}


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".tmp")]
        for name in names:
            if len(files) >= MAX_FILES:
                return files
            path = Path(current) / name
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            if path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"Dockerfile", "Makefile"}:
                files.append(path)
    return files


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def package_info(root: Path, files: list[Path]) -> dict[str, Any]:
    result: dict[str, Any] = {"manifests": [], "frameworks": set(), "scripts": {}}
    package_paths = [p for p in files if p.name == "package.json"]
    for p in package_paths[:4]:
        try:
            data = json.loads(read_text(p))
        except json.JSONDecodeError:
            continue
        result["manifests"].append(rel(root, p))
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        for dep in deps:
            key = dep.lower()
            for hint, label in FRAMEWORK_HINTS.items():
                if hint in key:
                    result["frameworks"].add(label)
        if p == root / "package.json" and isinstance(data.get("scripts"), dict):
            result["scripts"] = data["scripts"]
    expected = {
        "requirements.txt": "Python",
        "pyproject.toml": "Python",
        "composer.json": "PHP",
        "go.mod": "Go",
        "Cargo.toml": "Rust",
        "pubspec.yaml": "Flutter/Dart",
        "pom.xml": "Java/Maven",
        "build.gradle": "Java/Kotlin Gradle",
        "build.gradle.kts": "Java/Kotlin Gradle",
    }
    for p in files:
        if p.name in expected:
            result["manifests"].append(rel(root, p))
    result["frameworks"] = sorted(result["frameworks"])
    result["manifests"] = sorted(set(result["manifests"]))[:20]
    return result


def sql_tables(files: list[Path]) -> list[str]:
    names: set[str] = set()
    pattern = re.compile(r"CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(?:public\.)?[\"']?([A-Za-z0-9_]+)", re.I)
    for path in files:
        if path.suffix.lower() != ".sql":
            continue
        for match in pattern.finditer(read_text(path)):
            names.add(match.group(1))
    return sorted(names)


def scan_signals(root: Path, files: list[Path]) -> dict[str, Any]:
    evidence: dict[str, Counter[str]] = defaultdict(Counter)
    total: Counter[str] = Counter()
    for path in files:
        text = read_text(path)
        if not text:
            continue
        lower = text.lower()
        rp = rel(root, path)
        for category, terms in SIGNALS.items():
            for term in terms:
                count = lower.count(term.lower())
                if count:
                    total[category] += count
                    evidence[category][rp] += count
    categories: dict[str, Any] = {}
    for category in SIGNALS:
        top = evidence[category].most_common(6)
        categories[category] = {
            "hits": total[category],
            "present": total[category] > 0,
            "evidence": [{"file": f, "hits": c} for f, c in top],
        }
    return categories


def deployment_signals(root: Path, files: list[Path]) -> list[str]:
    names = {p.name for p in files}
    signals = set()
    for name in ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "vercel.json", "render.yaml", "fly.toml"]:
        if name in names:
            signals.add(name)
    if (root / ".github" / "workflows").is_dir():
        signals.add(".github/workflows")
    return sorted(signals)


def choose_mode(categories: dict[str, Any]) -> tuple[str, str]:
    payment = categories["payment"]["present"]
    redeem = categories["redeem"]["present"]
    if payment and redeem:
        return "D", "已有支付和兑换信号：先审计现有链路，只做最小连接改造"
    if redeem:
        return "B", "已有兑换信号、缺少支付信号：补在线支付、查单和自动代兑"
    if payment:
        return "C", "已有支付信号、缺少兑换信号：补卡密消费和权益发放"
    return "A", "未发现完整支付和兑换信号：建立最小打通连接层"


def markdown_report(root: Path, data: dict[str, Any]) -> str:
    lines = [
        "# 应用接入现状扫描",
        "",
        f"- 项目目录：`{root}`",
        f"- 技术栈：{', '.join(data['stack']['frameworks']) or '未自动识别'}",
        f"- 清单文件：{', '.join(data['stack']['manifests']) or '未发现'}",
        f"- 部署信号：{', '.join(data['deployment']) or '未发现'}",
        f"- 建议接入模式：{data['mode']} — {data['mode_reason']}",
        "",
        "## 能力信号",
        "",
        "> 以下为代码关键词与文件扫描结果，只作为线索，必须继续阅读关键文件确认。",
        "",
    ]
    labels = {
        "auth": "账号与鉴权",
        "payment": "支付/收银台",
        "order": "订单",
        "redeem": "兑换码/卡密",
        "wallet": "余额/流水",
        "entitlement": "会员/次卡/权益",
        "product": "商品/价格",
        "admin": "管理后台",
        "idempotency": "幂等",
        "webhook": "回调/通知",
        "iframe": "内嵌收银台",
        "rate_limit": "限流",
    }
    for category, label in labels.items():
        item = data["signals"][category]
        state = "发现" if item["present"] else "未发现"
        lines.append(f"### {label}：{state}")
        if item["evidence"]:
            for e in item["evidence"][:4]:
                lines.append(f"- `{e['file']}`（{e['hits']} 次）")
        else:
            lines.append("- 无可信代码信号")
        lines.append("")
    if data["tables"]:
        lines.extend(["## 数据库表", "", ", ".join(f"`{t}`" for t in data["tables"]), ""])
    lines.extend([
        "## 下一步",
        "",
        "1. 阅读上述高命中文件，确认已有支付、兑换和权益发放入口；",
        "2. 用 `classify_platform_link.py` 判断平台链接；",
        "3. 建立应用商品与平台商品的候选映射；",
        "4. 输出实施方案并按 `references/self-review.md` 复核；",
        "5. 获用户授权后再修改和测试。",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only application integration scan")
    parser.add_argument("path", nargs="?", default=".", help="Application root")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 2
    files = iter_files(root)
    categories = scan_signals(root, files)
    mode, mode_reason = choose_mode(categories)
    data = {
        "root": str(root),
        "files_scanned": len(files),
        "stack": package_info(root, files),
        "deployment": deployment_signals(root, files),
        "tables": sql_tables(files),
        "signals": categories,
        "mode": mode,
        "mode_reason": mode_reason,
    }
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(markdown_report(root, data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

