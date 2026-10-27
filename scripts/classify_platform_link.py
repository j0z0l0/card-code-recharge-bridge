#!/usr/bin/env python3
"""Classify a card-platform URL without making network requests."""
from __future__ import annotations

import argparse
import json
import re
from urllib.parse import parse_qs, urlparse

PRODUCT_MARKERS = ("item", "product", "goods", "sku", "shop/item")
PAY_MARKERS = ("pay", "cashier", "checkout", "order/result", "order/query", "trade")
STORE_MARKERS = ("shop", "store", "mall", "home", "index")
KEY_PARAMS = ("goods_key", "goodskey", "goods_id", "goodsId", "product_id", "productId", "sku", "id")
ORDER_PARAMS = ("trade_no", "tradeno", "order_no", "orderno", "out_trade_no", "token")


def classify(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"ok": False, "error": "链接必须是完整的 http/https URL"}
    path = parsed.path.lower()
    query = parse_qs(parsed.query)
    score = {"product": 0, "payment": 0, "store": 0}
    for marker in PRODUCT_MARKERS:
        if marker in path:
            score["product"] += 2
    for marker in PAY_MARKERS:
        if marker in path:
            score["payment"] += 2
    for marker in STORE_MARKERS:
        if marker in path:
            score["store"] += 1
    if any(k in query for k in KEY_PARAMS):
        score["product"] += 3
    if any(k in query for k in ORDER_PARAMS):
        score["payment"] += 3

    if score["product"] >= max(score["payment"], 3):
        kind = "product"
    elif score["payment"] >= 3:
        kind = "payment"
    elif score["store"] > 0:
        kind = "store"
    else:
        kind = "unknown"

    candidate_keys = {}
    for key, values in query.items():
        if key in KEY_PARAMS or key in ORDER_PARAMS:
            candidate_keys[key] = values[0] if values else ""
    path_segments = [seg for seg in parsed.path.split("/") if seg]
    candidates = [seg for seg in path_segments if re.fullmatch(r"[A-Za-z0-9_-]{4,48}", seg)]
    guidance = {
        "product": "优先使用：可用于识别平台、商品与价格；继续读取商品元数据并建立应用商品映射。",
        "payment": "用于识别支付/查单协议和 iframe 能力；临时订单号不能用于商品映射，仍需具体商品页。",
        "store": "通常只能识别平台或店铺；如无平台适配器，需要具体商品页或商品后台截图。",
        "unknown": "无法确认链接类型；请提供具体商品页，或同时提供商品后台截图。",
    }[kind]
    return {
        "ok": True,
        "url": url,
        "host": parsed.hostname,
        "kind": kind,
        "guidance": guidance,
        "candidate_keys": candidate_keys,
        "path_candidates": candidates[-4:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a card-platform product or payment URL")
    parser.add_argument("url")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = classify(args.url)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not result["ok"]:
        print(f"ERROR: {result['error']}")
    else:
        print(f"平台域名：{result['host']}")
        print(f"链接类型：{result['kind']}")
        print(f"用途判断：{result['guidance']}")
        if result["candidate_keys"]:
            print("候选字段：", ", ".join(result["candidate_keys"]))
        if result["path_candidates"]:
            print("路径候选：", ", ".join(result["path_candidates"]))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

