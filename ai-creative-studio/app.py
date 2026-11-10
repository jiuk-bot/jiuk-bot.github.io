# -*- coding: utf-8 -*-
"""
AI 소재 A/B 스튜디오 — 소재 A/B 테스트 운영 대시보드 (내부 공유용)
윤지욱 · AI 마케터

① A/B 데이터 기록  ② 과거 데이터 조회  ③ 성과 분석(이기는 소재 공통점)
④ 소재 기획 리뷰(옵션 선택 → 과거 우수 소재 공통점 리뷰 + 추천)
⑤ 컷별 프롬프트 생성 → 엑셀 다운로드

데이터: SQLite(ab_studio.db). API 키·비밀번호는 Streamlit Secrets에 저장(코드에 두지 않음).
"""
import io
import json
import sqlite3
import sys
from datetime import date

import pandas as pd
import streamlit as st

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

st.set_page_config(page_title="AI 소재 A/B 스튜디오", page_icon="🎬", layout="wide")


def sget(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


# ── 접근 제어(내부 전용) ────────────────────────────────────────
def check_password():
    pw = sget("APP_PASSWORD")
    if not pw or st.session_state.get("authed"):
        return
    st.markdown("### 🔒 내부 전용 — 접근 비밀번호")
    entered = st.text_input("비밀번호", type="password", label_visibility="collapsed")
    if entered == pw:
        st.session_state["authed"] = True
        st.rerun()
    elif entered:
        st.error("비밀번호가 올바르지 않습니다.")
    st.stop()


check_password()

# ── DB ─────────────────────────────────────────────────────────
DB_PATH = "ab_studio.db"
HOOKS = ["공감", "자극", "숫자", "권위", "사회적증거", "호기심"]
FORMATS = ["세로 숏폼", "가로 영상", "이미지"]
BIZES = ["교육", "의료", "생활서비스", "커머스", "금융", "기타"]

SEED = [
    ("2025-02-10", "교육", "데이터분석 강의", "데이터강의·커리어 공감", "커리어 전환", "공감", "세로 숏폼", 5, 18, 2.1, 4.8, 72000, "A", "", "커리어 전환 공감형이 전환 리드"),
    ("2025-02-18", "교육", "데이터분석 강의", "데이터강의·연봉 숫자", "커리어 전환", "숫자", "가로 영상", 4, 22, 1.6, 3.9, 91000, "B", "", ""),
    ("2025-03-05", "교육", "영상편집 클래스", "영상편집·부업 수익", "부업·수익화", "공감", "세로 숏폼", 6, 15, 2.4, 4.2, 80000, "A", "", ""),
    ("2025-03-12", "교육", "영상편집 클래스", "영상편집·자극 인트로", "부업·수익화", "자극", "가로 영상", 3, 20, 2.8, 2.1, 142000, "C", "", "CTR 최고지만 CVR 급락"),
    ("2025-04-02", "의료", "임플란트", "임플란트·가격 문제제기", "가격 신뢰", "공감", "가로 영상", 5, 20, 1.2, 5.6, 61000, "A", "", "신뢰형 전환 최강"),
    ("2025-04-15", "의료", "임플란트", "임플란트·자녀 관여", "가격 신뢰", "공감", "세로 숏폼", 6, 16, 1.4, 4.9, 69000, "A", "", ""),
    ("2025-04-22", "의료", "임플란트", "임플란트·공포 자극", "가격 신뢰", "자극", "가로 영상", 3, 24, 1.9, 2.3, 133000, "C", "", "자극형 함정"),
    ("2025-05-03", "의료", "임플란트", "임플란트·원장 권위", "전문성", "권위", "이미지", 1, 0, 1.0, 4.4, 74000, "B", "", "이미지=이탈 낮음"),
    ("2025-05-10", "생활서비스", "공유창고", "공유창고·직장인 공감", "문제 해결", "공감", "세로 숏폼", 5, 17, 1.5, 3.8, 83000, "A", "", ""),
    ("2025-05-18", "생활서비스", "공유창고", "공유창고·가격 자극", "가격", "자극", "가로 영상", 3, 20, 2.2, 1.9, 151000, "C", "", "가격 자극 CVR 최저"),
    ("2025-05-25", "생활서비스", "공유창고", "공유창고·리뷰 신뢰", "신뢰", "사회적증거", "이미지", 1, 0, 1.1, 4.1, 78000, "B", "", "리뷰 기반 신뢰"),
    ("2025-06-01", "생활서비스", "공유창고", "공유창고·문제 해결", "문제 해결", "공감", "세로 숏폼", 6, 14, 1.7, 3.6, 86000, "B", "", "12초로 줄여 CTR 개선"),
]


def conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    c = conn()
    c.execute(
        """CREATE TABLE IF NOT EXISTS ab (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, 업종 TEXT, 상품 TEXT, 소재명 TEXT,
        소구포인트 TEXT, 후킹유형 TEXT, 포맷 TEXT, 컷수 INTEGER, 길이초 INTEGER,
        CTR REAL, CVR REAL, CPA REAL, 등급 TEXT, 영상링크 TEXT, 메모 TEXT )"""
    )
    c.commit()
    if c.execute("SELECT COUNT(*) FROM ab").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO ab (date,업종,상품,소재명,소구포인트,후킹유형,포맷,컷수,길이초,CTR,CVR,CPA,등급,영상링크,메모) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            SEED,
        )
        c.commit()
    c.close()


def load_df():
    c = conn()
    df = pd.read_sql_query("SELECT * FROM ab ORDER BY date DESC, id DESC", c)
    c.close()
    return df


def add_row(r):
    c = conn()
    c.execute(
        "INSERT INTO ab (date,업종,상품,소재명,소구포인트,후킹유형,포맷,컷수,길이초,CTR,CVR,CPA,등급,영상링크,메모) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (r["date"], r["업종"], r["상품"], r["소재명"], r["소구포인트"], r["후킹유형"], r["포맷"],
         r["컷수"], r["길이초"], r["CTR"], r["CVR"], r["CPA"], r["등급"], r["영상링크"], r["메모"]),
    )
    c.commit()
    c.close()


def auto_grade(cvr, cpa):
    if cvr >= 4.5 and cpa <= 85000:
        return "A"
    if cvr >= 3.5 and cpa <= 110000:
        return "B"
    return "C"


def to_excel_bytes(df, sheet="sheet1"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    return buf.getvalue()


init_db()

# ── Claude(컷별 프롬프트 생성용) ──────────────────────────────
_client = None
CLAUDE_MODEL = sget("CLAUDE_MODEL", "claude-opus-4-8")  # 비용 민감 시 claude-haiku-4-5 로 교체
if sget("ANTHROPIC_API_KEY"):
    try:
        import anthropic

        _client = anthropic.Anthropic(api_key=sget("ANTHROPIC_API_KEY"))
    except Exception as e:  # noqa
        st.sidebar.error(f"Claude 초기화 실패: {e}")

# ── 사이드바 네비게이션(탭 대신 분리 버튼) ──────────────────────
st.sidebar.title("🎬 AI 소재 A/B 스튜디오")
st.sidebar.caption("윤지욱 · AI 마케터")
PAGE = st.sidebar.radio(
    "메뉴",
    ["📊 성과 분석", "📝 A/B 데이터 기록", "🔍 과거 데이터 조회", "🧭 소재 기획 리뷰", "🎬 컷별 프롬프트 생성"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption(("🟢 Claude 연결됨 · " + CLAUDE_MODEL if _client else "⚪ 데모 모드(생성 기능은 API 키 필요)"))


# ════════════════════════════════════════════════════════════════
# 1) 성과 분석
# ════════════════════════════════════════════════════════════════
if PAGE == "📊 성과 분석":
    st.header("📊 성과 분석 — 이기는 소재의 공통점")
    df = load_df()
    biz = st.multiselect("업종 필터", sorted(df["업종"].unique()), default=sorted(df["업종"].unique()))
    v = df[df["업종"].isin(biz)] if biz else df

    c = st.columns(4)
    c[0].metric("소재 수", f"{len(v)}")
    c[1].metric("평균 CTR", f"{v['CTR'].mean():.2f}%")
    c[2].metric("평균 CVR", f"{v['CVR'].mean():.2f}%")
    c[3].metric("평균 CPA", f"{v['CPA'].mean():,.0f}원")

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**후킹 유형별 평균 CVR** — 공감·신뢰형이 전환을 만든다")
        st.bar_chart(v.groupby("후킹유형")["CVR"].mean())
    with g2:
        st.markdown("**포맷별 평균 CTR** — 세로 숏폼이 클릭을 끈다")
        st.bar_chart(v.groupby("포맷")["CTR"].mean())

    st.markdown("**업종별 최적 소재 (등급 A)**")
    a = df[df["등급"] == "A"]
    if len(a):
        best = a.groupby("업종").agg(
            이기는_소구=("소구포인트", lambda s: ", ".join(sorted(set(s)))),
            이기는_후킹=("후킹유형", lambda s: ", ".join(sorted(set(s)))),
            최적_포맷=("포맷", lambda s: ", ".join(sorted(set(s)))),
            평균CVR=("CVR", "mean"),
        ).round(2).reset_index()
        st.dataframe(best, use_container_width=True, hide_index=True)

    st.markdown("**상위 소재 TOP (CVR 기준)**")
    st.dataframe(v.sort_values("CVR", ascending=False).head(8)[
        ["date", "업종", "소재명", "소구포인트", "후킹유형", "포맷", "CTR", "CVR", "CPA", "등급"]],
        use_container_width=True, hide_index=True)
    st.info("핵심 패턴: 자극형은 CTR↑·CVR↓(클릭만), **공감·신뢰형이 전환**. 세로 숏폼=CTR 우위, 이미지=이탈 낮아 CVR 안정.")


# ════════════════════════════════════════════════════════════════
# 2) A/B 데이터 기록
# ════════════════════════════════════════════════════════════════
elif PAGE == "📝 A/B 데이터 기록":
    st.header("📝 A/B 데이터 기록")
    st.caption("집행한 소재의 A/B 결과를 기록합니다. CTR/CVR/CPA는 직접 입력하거나 노출·클릭·전환·비용으로 자동 계산할 수 있습니다.")

    mode = st.radio("입력 방식", ["지표 직접 입력", "원시값으로 자동 계산"], horizontal=True)
    with st.form("rec"):
        c = st.columns(3)
        d = c[0].date_input("집행일", value=date.today())
        bz = c[1].selectbox("업종", BIZES)
        prod = c[2].text_input("상품/서비스", "")
        name = st.text_input("소재명", "")
        c = st.columns(4)
        angle = c[0].text_input("소구포인트", "")
        hook = c[1].selectbox("후킹 유형", HOOKS)
        fmt = c[2].selectbox("포맷", FORMATS)
        cuts = c[3].number_input("컷 수", 0, 50, 5)
        dur = st.slider("영상 길이(초)", 0, 60, 15)

        if mode == "지표 직접 입력":
            c = st.columns(3)
            ctr = c[0].number_input("CTR(%)", 0.0, 100.0, 1.5, 0.01)
            cvr = c[1].number_input("CVR(%)", 0.0, 100.0, 3.5, 0.01)
            cpa = c[2].number_input("CPA(원)", 0, 1000000, 80000, 1000)
        else:
            c = st.columns(4)
            imp = c[0].number_input("노출", 0, 100000000, 100000)
            clk = c[1].number_input("클릭", 0, 10000000, 1500)
            cv = c[2].number_input("전환", 0, 1000000, 52)
            spend = c[3].number_input("비용(원)", 0, 1000000000, 4000000)
            ctr = round(100 * clk / imp, 2) if imp else 0.0
            cvr = round(100 * cv / clk, 2) if clk else 0.0
            cpa = round(spend / cv) if cv else 0
            st.caption(f"→ 자동 계산: CTR {ctr}% · CVR {cvr}% · CPA {cpa:,}원")

        link = st.text_input("영상/소재 링크(선택)", "")
        memo = st.text_input("메모(선택)", "")
        auto_g = auto_grade(cvr, cpa)
        gr = st.selectbox("등급", ["자동(" + auto_g + ")", "A", "B", "C"])
        submitted = st.form_submit_button("💾 기록 저장", type="primary")

    if submitted:
        if not name.strip():
            st.error("소재명을 입력하세요.")
        else:
            add_row({
                "date": str(d), "업종": bz, "상품": prod, "소재명": name, "소구포인트": angle,
                "후킹유형": hook, "포맷": fmt, "컷수": int(cuts), "길이초": int(dur),
                "CTR": float(ctr), "CVR": float(cvr), "CPA": int(cpa),
                "등급": auto_g if gr.startswith("자동") else gr, "영상링크": link, "메모": memo,
            })
            st.success(f"저장 완료 · '{name}' (등급 {auto_g if gr.startswith('자동') else gr})")

    st.divider()
    st.markdown("**CSV 일괄 업로드** (열: date,업종,상품,소재명,소구포인트,후킹유형,포맷,컷수,길이초,CTR,CVR,CPA,등급,영상링크,메모)")
    up = st.file_uploader("CSV", type="csv", label_visibility="collapsed")
    if up and st.button("일괄 추가"):
        try:
            u = pd.read_csv(up)
            for _, r in u.iterrows():
                add_row({k: r.get(k, "") for k in
                         ["date", "업종", "상품", "소재명", "소구포인트", "후킹유형", "포맷", "컷수", "길이초", "CTR", "CVR", "CPA", "등급", "영상링크", "메모"]})
            st.success(f"{len(u)}건 추가 완료")
        except Exception as e:  # noqa
            st.error(f"업로드 실패: {e}")


# ════════════════════════════════════════════════════════════════
# 3) 과거 데이터 조회
# ════════════════════════════════════════════════════════════════
elif PAGE == "🔍 과거 데이터 조회":
    st.header("🔍 과거 데이터 조회")
    df = load_df()
    c = st.columns(4)
    f_biz = c[0].multiselect("업종", sorted(df["업종"].unique()))
    f_hook = c[1].multiselect("후킹", sorted(df["후킹유형"].unique()))
    f_fmt = c[2].multiselect("포맷", sorted(df["포맷"].unique()))
    f_grade = c[3].multiselect("등급", ["A", "B", "C"])
    kw = st.text_input("상품/소재명 검색", "")

    v = df.copy()
    if f_biz: v = v[v["업종"].isin(f_biz)]
    if f_hook: v = v[v["후킹유형"].isin(f_hook)]
    if f_fmt: v = v[v["포맷"].isin(f_fmt)]
    if f_grade: v = v[v["등급"].isin(f_grade)]
    if kw.strip():
        v = v[v["상품"].str.contains(kw, case=False, na=False) | v["소재명"].str.contains(kw, case=False, na=False)]

    st.caption(f"{len(v)}건")
    st.dataframe(v.drop(columns=["id"]), use_container_width=True, hide_index=True)
    c = st.columns(2)
    c[0].download_button("⬇ CSV 다운로드", v.drop(columns=["id"]).to_csv(index=False).encode("utf-8-sig"),
                         "ab_records.csv", "text/csv")
    c[1].download_button("⬇ 엑셀 다운로드", to_excel_bytes(v.drop(columns=["id"]), "AB기록"),
                         "ab_records.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ════════════════════════════════════════════════════════════════
# 4) 소재 기획 리뷰 — 옵션 선택 → 과거 우수 소재 공통점 리뷰
# ════════════════════════════════════════════════════════════════
elif PAGE == "🧭 소재 기획 리뷰":
    st.header("🧭 소재 기획 리뷰")
    st.caption("다음 소재를 기획하기 전, **과거 효율이 좋았던 소재들의 공통점**을 리뷰합니다. 옵션을 선택하세요.")
    df = load_df()

    c = st.columns(3)
    bz = c[0].selectbox("업종", sorted(df["업종"].unique()))
    goal = c[1].selectbox("목표", ["전환 최대화 (CVR)", "효율 최대화 (CPA 최소)"])
    topk = c[2].slider("우수 소재 기준 상위 N", 2, 10, 4)

    sub = df[df["업종"] == bz].copy()
    if len(sub) == 0:
        st.warning("해당 업종 데이터가 없습니다.")
    else:
        winners = sub.sort_values("CVR", ascending=False).head(topk) if goal.startswith("전환") \
            else sub.sort_values("CPA", ascending=True).head(topk)

        def common(col):
            m = winners[col].mode()
            return m.iloc[0] if len(m) else "-"

        st.subheader(f"✅ '{bz}' 이기는 소재의 공통점")
        c = st.columns(5)
        c[0].metric("이기는 소구", common("소구포인트"))
        c[1].metric("이기는 후킹", common("후킹유형"))
        c[2].metric("최적 포맷", common("포맷"))
        c[3].metric("권장 컷 수", f"{int(winners['컷수'].median())}컷")
        c[4].metric("권장 길이", f"{int(winners['길이초'].median())}초")

        st.success(
            f"💡 다음 소재 기획 가이드 — **{common('소구포인트')}** 소구를 **{common('후킹유형')}** 후킹으로, "
            f"**{common('포맷')}** 포맷 · 약 **{int(winners['길이초'].median())}초 / {int(winners['컷수'].median())}컷** 구성 추천. "
            f"(과거 상위 {topk}개 소재 공통 패턴)"
        )
        st.markdown("**근거가 된 우수 소재**")
        st.dataframe(winners[["date", "소재명", "소구포인트", "후킹유형", "포맷", "컷수", "길이초", "CTR", "CVR", "CPA", "등급"]],
                     use_container_width=True, hide_index=True)

        if st.button("🎬 이 방향으로 컷별 프롬프트 만들기 →"):
            st.session_state["plan"] = {
                "상품": winners.iloc[0]["상품"], "소구": common("소구포인트"),
                "후킹": common("후킹유형"), "길이": int(winners["길이초"].median()),
                "컷수": int(winners["컷수"].median()),
            }
            st.info("상단 사이드바에서 **🎬 컷별 프롬프트 생성**으로 이동하면 이 방향이 자동 입력됩니다.")


# ════════════════════════════════════════════════════════════════
# 5) 컷별 프롬프트 생성 → 엑셀 다운로드
# ════════════════════════════════════════════════════════════════
elif PAGE == "🎬 컷별 프롬프트 생성":
    st.header("🎬 컷별 프롬프트 생성")
    st.caption("기획 방향을 입력하면 컷(씬)별로 영상 프롬프트·자막·나레이션을 만들고, **엑셀로 다운로드**합니다.")
    p = st.session_state.get("plan", {})

    c = st.columns(3)
    product = c[0].text_input("상품/서비스", p.get("상품", "패스트캠퍼스 · 데이터 분석 강의"))
    angle = c[1].text_input("소구포인트", p.get("소구", "커리어 전환"))
    hook = c[2].selectbox("후킹 유형", HOOKS, index=HOOKS.index(p.get("후킹", "공감")) if p.get("후킹") in HOOKS else 0)
    c = st.columns(3)
    tone = c[0].selectbox("톤", ["다큐/뉴스", "공감 드라마", "경쾌/밈", "프리미엄"])
    dur = c[1].slider("길이(초)", 8, 40, int(p.get("길이", 15)))
    cuts = c[2].slider("컷 수", 3, 10, int(p.get("컷수", 5)))

    if st.button("⚡ 컷별 프롬프트 생성", type="primary"):
        rows = None
        if _client:
            try:
                prompt = (
                    "너는 AI 영상 광고 디렉터다. 아래 조건으로 컷(씬)별 스토리보드를 만들어라.\n"
                    f"[상품] {product} / [소구] {angle} / [후킹] {hook} / [톤] {tone} / [길이] {dur}초 / [컷수] {cuts}\n"
                    "각 컷마다: scene(장면설명 한국어), video_prompt(영문 영상생성 프롬프트, 끝에 반드시 \"No text, no letters.\" 포함), "
                    f"subtitle(한국어 자막), narration(한국어 나레이션). 정확히 {cuts}개의 컷을 만들어라.\n"
                    "반드시 JSON으로만 응답(설명·코드펜스 금지): "
                    '{"cuts":[{"scene":"","video_prompt":"","subtitle":"","narration":""}]}'
                )
                with st.spinner(f"Claude({CLAUDE_MODEL})가 컷별 스토리보드를 생성 중..."):
                    resp = _client.messages.create(
                        model=CLAUDE_MODEL,
                        max_tokens=4000,
                        messages=[{"role": "user", "content": prompt}],
                    )
                raw = next((b.text for b in resp.content if b.type == "text"), "").strip()
                if raw.startswith("```"):
                    raw = raw.strip("`"); raw = raw[raw.find("{"): raw.rfind("}") + 1]
                rows = json.loads(raw).get("cuts", [])
            except Exception as e:  # noqa
                st.error(f"생성 실패(템플릿으로 대체): {e}")
        if rows is None:  # 데모/템플릿
            seg = max(1, dur // cuts)
            rows = [{
                "scene": f"{angle} 관련 장면 {i+1} ({hook} 후킹, {tone} 톤)",
                "video_prompt": f"Cinematic {tone} scene about {product}, photorealistic, highly detailed. No text, no letters.",
                "subtitle": f"[{i+1}컷 자막] {angle} 메시지",
                "narration": f"[{i+1}컷 나레이션] {angle}을(를) {hook}으로 전달",
            } for i in range(cuts)]
            if not _client:
                st.warning("데모 모드(템플릿)입니다. Secrets에 ANTHROPIC_API_KEY를 넣으면 실제 생성됩니다.")

        out = pd.DataFrame([{
            "컷": i + 1,
            "시간(초)": f"{i*(dur//cuts)}-{(i+1)*(dur//cuts)}",
            "장면": r.get("scene", ""),
            "영상 프롬프트(영문)": r.get("video_prompt", ""),
            "자막": r.get("subtitle", ""),
            "나레이션": r.get("narration", ""),
        } for i, r in enumerate(rows)])
        st.session_state["cuts_out"] = out

    if "cuts_out" in st.session_state:
        out = st.session_state["cuts_out"]
        st.dataframe(out, use_container_width=True, hide_index=True)
        c = st.columns(2)
        c[0].download_button("⬇ 엑셀(.xlsx) 다운로드", to_excel_bytes(out, "컷별프롬프트"),
                             "cut_prompts.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        c[1].download_button("⬇ CSV 다운로드", out.to_csv(index=False).encode("utf-8-sig"),
                             "cut_prompts.csv", "text/csv")
