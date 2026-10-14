# -*- coding: utf-8 -*-
"""
토스 Ads BDR — 온디맨드 발굴 수집 API (Vercel 서버리스).
GET /api/collect?company=<회사명>[&industry=<업종>&target=<타깃>&hp=<홈페이지>]
브라우저가 직접 호출 → 서버사이드에서 뉴스·채용 즉시 수집·스코어링 → JSON 반환(CORS 허용).
어떤 기업명이든 실시간 조회 가능. 업종/홈페이지가 주어지면 계절성·핏 시그널도 산정.
"""
import os
import sys
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tossbdr", "scripts"))
from collector_lib import collect_company, CATALOG, KST  # noqa: E402
from datetime import datetime  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        name = (q.get("company", [""])[0] or "").strip()
        industry = (q.get("industry", [""])[0] or "").strip() or None
        target = (q.get("target", [""])[0] or "").strip()
        hp = (q.get("hp", [""])[0] or "").strip()

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()

        if not name:
            self.wfile.write(json.dumps({"error": "company 파라미터가 필요합니다"}, ensure_ascii=False).encode("utf-8"))
            return
        try:
            company = collect_company(name, industry, hp, target)
            out = {
                "generated": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
                "mode": "live-ondemand",
                "catalog": CATALOG,
                "company": company,
            }
        except Exception as e:  # 수집 실패해도 500 대신 에러 메시지 반환
            out = {"error": str(e), "company": None}
        self.wfile.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))
