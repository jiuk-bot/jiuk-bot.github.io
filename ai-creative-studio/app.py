# -*- coding: utf-8 -*-
"""
AI 소재 A/B 스튜디오 — 데이원컴퍼니 지원용 데모 (교육 콘텐츠 소재 운영)
윤지욱 · AI 마케터

① 성과 분석  ② 소재 A/B 기록  ③ 과거 데이터 조회  ④ 소재 기획 리뷰  ⑤ 컷별 프롬프트 생성(→엑셀)
- 디자인: shadcn zinc 다크 테마(실제 광고주 대시보드와 동일)
- 데이터: SQLite · 표시 수치는 전부 가상(샘플) 데이터
- 생성: Claude(Anthropic). 키 없으면 템플릿 데모.
"""
import io
import json
import sqlite3
import sys
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

st.set_page_config(page_title="데이원 · AI 소재 A/B 스튜디오", page_icon="🎬", layout="wide",
                   initial_sidebar_state="expanded")

# ── 네온 퍼플 팔레트 (포트폴리오와 동일 톤) ──
BG = "#07070E"; CARD = "rgba(22,22,34,.55)"; BORDER = "rgba(124,92,255,.18)"
TEXT = "#EDEBFA"; MUTED = "#9E99BC"
ACCENT = "#7C5CFF"; ACCENT2 = "#C06BFF"; PINK = "#FF6BD6"; LILAC = "#C9A6FF"
GREEN = "#7BE0A3"; AMBER = "#f59e0b"

st.markdown(f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@latest/dist/web/static/pretendard.css');
html, body, [class*="css"], .stApp, input, textarea, select, button {{ font-family:'Pretendard',-apple-system,system-ui,sans-serif; }}
.stApp {{
  background:
    radial-gradient(38% 50% at 10% 3%, rgba(124,92,255,.22), transparent 60%),
    radial-gradient(34% 46% at 95% 13%, rgba(255,92,225,.15), transparent 60%),
    radial-gradient(48% 56% at 74% 110%, rgba(92,200,255,.13), transparent 62%),
    {BG};
  background-attachment:fixed;
}}
#MainMenu, header, footer {{ visibility:hidden; }}
.block-container {{ padding-top:1.4rem; max-width:1280px; }}
.block-container h1 {{ font-size:1.95rem; font-weight:800; letter-spacing:-.025em;
  background:linear-gradient(120deg,#9D7BFF,#C06BFF,#FF6BD6,#9D7BFF);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
  filter:drop-shadow(0 0 26px rgba(170,110,255,.35)); }}
h2,h3,h4,h5 {{ color:{TEXT}; letter-spacing:-.01em; }}
p, label, span, .stMarkdown {{ color:{TEXT}; }}
/* glass 메트릭 카드 */
div[data-testid="stMetric"] {{ background:{CARD}; -webkit-backdrop-filter:blur(10px); backdrop-filter:blur(10px);
  border:1px solid {BORDER}; border-radius:16px; padding:18px 20px; min-height:108px;
  display:flex; flex-direction:column; justify-content:center;
  box-shadow:0 24px 60px -36px rgba(0,0,0,.85); transition:transform .35s, border-color .35s, box-shadow .35s; }}
div[data-testid="stMetric"]:hover {{ transform:translateY(-5px); border-color:rgba(160,110,255,.55);
  box-shadow:0 40px 90px -40px rgba(124,92,255,.5); }}
div[data-testid="stMetricLabel"] p {{ color:{MUTED}; font-size:11.5px; font-weight:600; letter-spacing:.3px; }}
div[data-testid="stMetricValue"] {{ font-size:25px; font-weight:800; font-variant-numeric:tabular-nums;
  background:linear-gradient(135deg,#B794F6,#FF6BD6); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
section[data-testid="stSidebar"] {{ background:rgba(10,10,18,.6); -webkit-backdrop-filter:blur(12px); backdrop-filter:blur(12px); border-right:1px solid {BORDER}; }}
section[data-testid="stSidebar"] * {{ color:{TEXT}; }}
.demo-banner {{ background:rgba(124,92,255,.12); color:{LILAC}; border:1px solid rgba(124,92,255,.3);
  border-radius:12px; padding:10px 16px; font-size:12.5px; font-weight:600; margin:2px 0 18px;
  -webkit-backdrop-filter:blur(8px); backdrop-filter:blur(8px); }}
/* 가로 탭 네비 (글로우 언더라인) */
div[role="radiogroup"] {{ gap:4px 26px; flex-wrap:wrap; border-bottom:1px solid {BORDER}; margin-bottom:22px; }}
div[role="radiogroup"] > label {{ margin:0 !important; padding:0 2px 11px 2px; border-bottom:2px solid transparent; white-space:nowrap; flex:0 0 auto; }}
div[role="radiogroup"] > label > div:first-child {{ display:none !important; }}
div[role="radiogroup"] > label p {{ font-size:14.5px; font-weight:700; color:{MUTED}; transition:color .15s; }}
div[role="radiogroup"] > label:hover p {{ color:{TEXT}; }}
div[role="radiogroup"] > label:has(input:checked) {{ border-bottom-color:{ACCENT2}; }}
div[role="radiogroup"] > label:has(input:checked) p {{ color:#fff; text-shadow:0 0 16px rgba(170,110,255,.65); }}
/* 입력 */
div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stDateInput input {{
  border:1px solid {BORDER} !important; border-radius:10px !important; background:rgba(18,18,30,.6) !important; color:{TEXT} !important; }}
div[data-testid="stExpander"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; }}
.stButton>button, .stDownloadButton>button {{ border-radius:11px; font-weight:800; border:1px solid rgba(124,92,255,.42);
  background:rgba(124,92,255,.08); color:{TEXT}; transition:transform .2s, box-shadow .2s, border-color .2s; }}
.stButton>button:hover, .stDownloadButton>button:hover {{ transform:translateY(-2px); border-color:rgba(170,120,255,.85);
  box-shadow:0 0 26px -6px rgba(124,92,255,.55); }}
.stButton>button[kind="primary"] {{ background:linear-gradient(135deg,#7C5CFF,#C06BFF) !important; border:0 !important;
  color:#fff !important; box-shadow:0 12px 32px -10px rgba(124,92,255,.7); }}
div[data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; }}
.stAlert {{ border-radius:12px; }}
.sec-title {{ font-size:14.5px; font-weight:800; color:{TEXT}; margin:6px 0 2px; }}
.sec-sub {{ font-size:12px; color:{MUTED}; margin-bottom:10px; }}
hr {{ border-color:{BORDER}; }}
::selection {{ background:rgba(192,107,255,.4); color:#fff; }}
</style>
""", unsafe_allow_html=True)


def sget(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


# ── 접근 제어(내부 전용, 선택) ───────────────────────────────
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

# ── 데이터 (교육 콘텐츠 소재 · 가상 샘플) ─────────────────────
DB_PATH = "ab_studio.db"
HOOKS = ["공감", "자극", "숫자", "권위", "사회적증거", "호기심"]
FORMATS = ["세로 숏폼", "가로 영상", "이미지", "카드뉴스"]
CATS = ["데이터", "AI", "개발", "영상/디자인", "마케팅", "기타"]

SEED = [
    ("2026-01-10", "데이터", "데이터 분석 올인원", "비전공 커리어전환 공감", "커리어 전환", "공감", "세로 숏폼", 5, 18, 2.3, 5.1, 62000, "A", "", "문과→분석가 공감 스토리"),
    ("2026-01-18", "데이터", "데이터 분석 올인원", "연봉 숫자 후킹", "연봉 상승", "숫자", "가로 영상", 4, 22, 1.7, 3.8, 95000, "B", "", ""),
    ("2026-01-25", "데이터", "데이터 분석 올인원", "자극 인트로", "커리어 전환", "자극", "가로 영상", 3, 20, 2.9, 2.0, 148000, "C", "", "CTR 최고·CVR 급락(자극 함정)"),
    ("2026-02-03", "AI", "AI 실무 부트캠프", "업무 자동화 공감", "실무 즉시적용", "공감", "세로 숏폼", 6, 16, 2.1, 4.6, 70000, "A", "", "엑셀 야근→자동화"),
    ("2026-02-12", "AI", "AI 실무 부트캠프", "현직자 권위", "실무 즉시적용", "권위", "이미지", 1, 0, 1.2, 4.9, 66000, "A", "", "현직자 신뢰형(이탈 낮음)"),
    ("2026-02-20", "AI", "AI 실무 부트캠프", "FOMO 호기심", "커리어 전환", "호기심", "세로 숏폼", 5, 15, 2.5, 3.2, 102000, "B", "", ""),
    ("2026-03-02", "영상/디자인", "영상편집 마스터", "부업 수익 인증", "부업·수익화", "사회적증거", "세로 숏폼", 6, 17, 2.6, 4.4, 72000, "A", "", "수익 인증형"),
    ("2026-03-10", "영상/디자인", "영상편집 마스터", "가격 자극", "부업·수익화", "자극", "가로 영상", 3, 20, 2.4, 1.8, 158000, "C", "", "가격 자극 CVR 최저"),
    ("2026-03-18", "영상/디자인", "영상편집 마스터", "포폴 완성 공감", "포트폴리오 완성", "공감", "카드뉴스", 1, 0, 1.0, 4.0, 80000, "B", "", "카드뉴스=이탈 낮음"),
    ("2026-04-01", "마케팅", "그로스 마케팅", "실무 즉시적용 공감", "실무 즉시적용", "공감", "세로 숏폼", 5, 16, 1.9, 3.9, 84000, "B", "", ""),
    ("2026-04-09", "마케팅", "그로스 마케팅", "수강생 후기", "커리어 전환", "사회적증거", "이미지", 1, 0, 1.1, 4.3, 76000, "B", "", "후기 기반 신뢰"),
    ("2026-04-17", "마케팅", "그로스 마케팅", "성과 숫자 강조", "연봉 상승", "숫자", "가로 영상", 4, 21, 1.6, 3.5, 99000, "B", "", ""),
    ("2026-05-02", "개발", "백엔드 개발 입문", "비전공 가능 공감", "비전공 접근성", "공감", "세로 숏폼", 6, 15, 2.2, 4.7, 68000, "A", "", "비전공 불안 해소"),
    ("2026-05-10", "개발", "백엔드 개발 입문", "취업 자극", "커리어 전환", "자극", "가로 영상", 3, 22, 2.7, 2.2, 140000, "C", "", "자극형 함정"),
]


def conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    c = conn()
    c.execute(
        """CREATE TABLE IF NOT EXISTS ab (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, 카테고리 TEXT, 강의 TEXT, 소재명 TEXT,
        소구포인트 TEXT, 후킹 TEXT, 포맷 TEXT, 컷수 INTEGER, 길이초 INTEGER,
        CTR REAL, CVR REAL, CPA REAL, 등급 TEXT, 링크 TEXT, 메모 TEXT )"""
    )
    c.commit()
    if c.execute("SELECT COUNT(*) FROM ab").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO ab (date,카테고리,강의,소재명,소구포인트,후킹,포맷,컷수,길이초,CTR,CVR,CPA,등급,링크,메모) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", SEED)
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
        "INSERT INTO ab (date,카테고리,강의,소재명,소구포인트,후킹,포맷,컷수,길이초,CTR,CVR,CPA,등급,링크,메모) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (r["date"], r["카테고리"], r["강의"], r["소재명"], r["소구포인트"], r["후킹"], r["포맷"],
         r["컷수"], r["길이초"], r["CTR"], r["CVR"], r["CPA"], r["등급"], r["링크"], r["메모"]))
    c.commit()
    c.close()


def auto_grade(cvr, cpa):
    if cvr >= 4.5 and cpa <= 80000:
        return "A"
    if cvr >= 3.5 and cpa <= 120000:
        return "B"
    return "C"


def won(v):
    return f"₩{int(v):,}"


def num_comma(col, label, default):
    """천 단위 콤마가 보이는 숫자 입력(폼 안에서 사용). 콤마/공백 제거 후 int 반환."""
    raw = col.text_input(label, f"{int(default):,}")
    try:
        return int(str(raw).replace(",", "").replace(" ", "").strip() or 0)
    except ValueError:
        return 0


def to_excel_bytes(df, sheet="sheet1"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sheet)
    return buf.getvalue()


def bar(series, color=ACCENT, suffix="", h=300):
    s = series.sort_values(ascending=False)
    fig = go.Figure(go.Bar(
        x=[str(i) for i in s.index], y=list(s.values), marker_color=color,
        text=[f"{v:.1f}{suffix}" for v in s.values], textposition="outside"))
    fig.update_layout(font_color=TEXT, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      height=h, margin=dict(l=10, r=10, t=22, b=10), showlegend=False)
    fig.update_xaxes(showgrid=False, linecolor="rgba(124,92,255,.25)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(124,92,255,.13)", zeroline=False)
    return fig


init_db()

# ── Claude(컷별 프롬프트 생성용) ──────────────────────────────
_client = None
CLAUDE_MODEL = sget("CLAUDE_MODEL", "claude-opus-4-8")  # 비용 민감 시 claude-haiku-4-5
if sget("ANTHROPIC_API_KEY"):
    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=sget("ANTHROPIC_API_KEY"))
    except Exception as e:  # noqa
        st.sidebar.error(f"Claude 초기화 실패: {e}")

# ── 사이드바(브랜드/상태) ─────────────────────────────────────
with st.sidebar:
    st.markdown(f"<div style='font-size:17px;font-weight:800;color:{TEXT}'>🎬 AI 소재 A/B 스튜디오</div>",
                unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:{MUTED};margin-top:2px'>윤지욱 · AI 마케터</div>",
                unsafe_allow_html=True)
    st.divider()
    st.markdown(f"<div style='font-size:12px;color:{MUTED};line-height:1.7'>"
                "교육 콘텐츠(패스트캠퍼스·콜로소) 광고 소재의<br>"
                "A/B 결과를 <b style='color:#a5b4fc'>기록·분석</b>하고, 다음 소재의<br>"
                "<b style='color:#a5b4fc'>이기는 공통점</b>을 리뷰하는 운영 툴.</div>", unsafe_allow_html=True)
    st.divider()
    st.caption("🟢 Claude 연결됨 · " + CLAUDE_MODEL if _client else "⚪ 데모 모드 (생성은 API 키 필요)")

# ── 헤더 + 가로 탭 네비 ───────────────────────────────────────
st.markdown(f"# AI 소재 A/B 스튜디오")
st.markdown("<div class='demo-banner'>📘 데이원컴퍼니 지원용 데모 · 표시되는 모든 수치는 가상(샘플) 데이터입니다 (교육 콘텐츠 소재 운영 예시)</div>",
            unsafe_allow_html=True)

# 기획 리뷰 → 컷 생성 원클릭 점프 (위젯 생성 전에 상태 설정)
if st.session_state.pop("_goto_gen", False):
    st.session_state["nav"] = "🎬 컷별 프롬프트 생성"
PAGE = st.radio("nav", ["📊 성과 분석", "📝 소재 A/B 기록", "🔍 과거 데이터 조회", "🧭 소재 기획 리뷰", "🎬 컷별 프롬프트 생성"],
                horizontal=True, label_visibility="collapsed", key="nav")


# ════════════════ 1) 성과 분석 ════════════════
if PAGE == "📊 성과 분석":
    df = load_df()
    cat_sel = st.columns([1, 2])[0].selectbox("📚 강의 카테고리", ["전체 카테고리"] + sorted(df["카테고리"].unique()))
    v = df if cat_sel.startswith("전체") else df[df["카테고리"] == cat_sel]
    st.caption("📚 포함 강의 — " + " · ".join(sorted(v["강의"].unique())))

    # 한눈에 액션 요약
    if len(v):
        av = v[v["등급"] == "A"]
        wh = (av["후킹"].mode().iloc[0] if len(av) and len(av["후킹"].mode())
              else v.groupby("후킹")["CVR"].mean().idxmax())
        wf = (av["포맷"].mode().iloc[0] if len(av) and len(av["포맷"].mode())
              else v.groupby("포맷")["CTR"].mean().idxmax())
        n_bad = int((v["등급"] == "C").sum())
        st.markdown(
            "<div class='demo-banner' style='background:rgba(123,224,163,.08);border-color:rgba(123,224,163,.3);color:#bdeccf'>"
            f"💡 <b>한눈에</b> — 지금 이기는 공식: <b>{wh} 후킹 × {wf}</b>. "
            f"교체 후보: 등급 C 소재 <b>{n_bad}건</b>(CTR만 높고 전환 낮음) → 공감·신뢰형으로 교체 권장.</div>",
            unsafe_allow_html=True)

    k = st.columns(4)
    k[0].metric("소재 수", f"{len(v)}개")
    k[1].metric("평균 CTR", f"{v['CTR'].mean():.2f}%")
    k[2].metric("평균 CVR (수강전환)", f"{v['CVR'].mean():.2f}%")
    k[3].metric("평균 CPA", won(v["CPA"].mean()))

    st.markdown("")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("<div class='sec-title'>후킹 유형별 평균 CVR</div><div class='sec-sub'>공감·신뢰형이 전환을 만든다</div>", unsafe_allow_html=True)
        st.plotly_chart(bar(v.groupby("후킹")["CVR"].mean(), ACCENT2, "%"), use_container_width=True)
    with g2:
        st.markdown("<div class='sec-title'>포맷별 평균 CTR</div><div class='sec-sub'>세로 숏폼이 클릭을 끈다</div>", unsafe_allow_html=True)
        st.plotly_chart(bar(v.groupby("포맷")["CTR"].mean(), ACCENT, "%"), use_container_width=True)

    st.markdown("<div class='sec-title'>카테고리별 최적 소재 (등급 A)</div>", unsafe_allow_html=True)
    a = df[df["등급"] == "A"]
    if len(a):
        best = a.groupby("카테고리").agg(
            이기는_소구=("소구포인트", lambda s: ", ".join(sorted(set(s)))),
            이기는_후킹=("후킹", lambda s: ", ".join(sorted(set(s)))),
            최적_포맷=("포맷", lambda s: ", ".join(sorted(set(s)))),
            평균CVR=("CVR", "mean")).round(2).reset_index()
        st.dataframe(best, use_container_width=True, hide_index=True)

    st.markdown("<div class='sec-title'>상위 소재 TOP (CVR 기준)</div>", unsafe_allow_html=True)
    st.dataframe(v.sort_values("CVR", ascending=False).head(8)[
        ["date", "카테고리", "강의", "소재명", "소구포인트", "후킹", "포맷", "CTR", "CVR", "CPA", "등급"]],
        use_container_width=True, hide_index=True)
    st.info("핵심 패턴: 자극형은 CTR↑·CVR↓(클릭만), **공감·권위·사회적증거형이 수강 전환**을 만든다. 세로 숏폼=CTR 우위, 이미지/카드뉴스=이탈 낮아 CVR 안정.")


# ════════════════ 2) 소재 A/B 기록 ════════════════
elif PAGE == "📝 소재 A/B 기록":
    st.markdown("<div class='sec-title'>소재 A/B 결과 기록</div><div class='sec-sub'>지표를 직접 입력하거나, 노출·클릭·수강신청·비용으로 자동 계산</div>", unsafe_allow_html=True)
    mode = st.radio("입력 방식", ["지표 직접 입력", "원시값으로 자동 계산"], horizontal=True, key="recmode")
    with st.form("rec"):
        c = st.columns(3)
        d = c[0].date_input("집행일", value=date.today())
        cat = c[1].selectbox("강의 카테고리", CATS)
        course = c[2].text_input("강의/클래스명", "데이터 분석 올인원")
        name = st.text_input("소재명", "")
        c = st.columns(4)
        angle = c[0].text_input("소구포인트", "커리어 전환")
        hook = c[1].selectbox("후킹 유형", HOOKS)
        fmt = c[2].selectbox("포맷", FORMATS)
        cuts = c[3].number_input("컷 수", 0, 50, 5)
        dur = st.slider("영상 길이(초)", 0, 60, 16)
        if mode == "지표 직접 입력":
            c = st.columns(3)
            ctr = c[0].number_input("CTR(%)", 0.0, 100.0, 2.0, 0.01)
            cvr = c[1].number_input("CVR(%)", 0.0, 100.0, 4.0, 0.01)
            cpa = num_comma(c[2], "CPA(원)", 80000)
        else:
            c = st.columns(4)
            imp = num_comma(c[0], "노출", 200000)
            clk = num_comma(c[1], "클릭", 4000)
            cv = num_comma(c[2], "수강신청(전환)", 160)
            spend = num_comma(c[3], "비용(원)", 12000000)
            ctr = round(100 * clk / imp, 2) if imp else 0.0
            cvr = round(100 * cv / clk, 2) if clk else 0.0
            cpa = round(spend / cv) if cv else 0
            st.caption(f"→ 자동 계산: CTR {ctr}% · CVR {cvr}% · CPA {cpa:,}원")
        link = st.text_input("영상/소재 링크(선택)", "")
        memo = st.text_input("메모(선택)", "")
        ag = auto_grade(cvr, cpa)
        gr = st.selectbox("등급", [f"자동({ag})", "A", "B", "C"])
        ok = st.form_submit_button("💾 기록 저장", type="primary")
    if ok:
        if not name.strip():
            st.error("소재명을 입력하세요.")
        else:
            add_row({"date": str(d), "카테고리": cat, "강의": course, "소재명": name, "소구포인트": angle,
                     "후킹": hook, "포맷": fmt, "컷수": int(cuts), "길이초": int(dur), "CTR": float(ctr),
                     "CVR": float(cvr), "CPA": int(cpa), "등급": ag if gr.startswith("자동") else gr,
                     "링크": link, "메모": memo})
            st.success(f"저장 완료 · '{name}' (등급 {ag if gr.startswith('자동') else gr})")

    st.divider()
    st.markdown("<div class='sec-sub'>CSV 일괄 업로드 (열: date,카테고리,강의,소재명,소구포인트,후킹,포맷,컷수,길이초,CTR,CVR,CPA,등급,링크,메모)</div>", unsafe_allow_html=True)
    up = st.file_uploader("CSV", type="csv", label_visibility="collapsed")
    if up and st.button("일괄 추가"):
        try:
            u = pd.read_csv(up)
            for _, r in u.iterrows():
                add_row({k2: r.get(k2, "") for k2 in
                         ["date", "카테고리", "강의", "소재명", "소구포인트", "후킹", "포맷", "컷수", "길이초", "CTR", "CVR", "CPA", "등급", "링크", "메모"]})
            st.success(f"{len(u)}건 추가 완료")
        except Exception as e:  # noqa
            st.error(f"업로드 실패: {e}")


# ════════════════ 3) 과거 데이터 조회 ════════════════
elif PAGE == "🔍 과거 데이터 조회":
    df = load_df()
    c = st.columns(4)
    f_cat = c[0].multiselect("강의 카테고리", sorted(df["카테고리"].unique()))
    f_hook = c[1].multiselect("후킹", sorted(df["후킹"].unique()))
    f_fmt = c[2].multiselect("포맷", sorted(df["포맷"].unique()))
    f_grade = c[3].multiselect("등급", ["A", "B", "C"])
    kw = st.text_input("강의/소재명 검색", "")
    v = df.copy()
    if f_cat: v = v[v["카테고리"].isin(f_cat)]
    if f_hook: v = v[v["후킹"].isin(f_hook)]
    if f_fmt: v = v[v["포맷"].isin(f_fmt)]
    if f_grade: v = v[v["등급"].isin(f_grade)]
    if kw.strip():
        v = v[v["강의"].str.contains(kw, case=False, na=False) | v["소재명"].str.contains(kw, case=False, na=False)]
    st.caption(f"{len(v)}건")
    st.dataframe(v.drop(columns=["id"]), use_container_width=True, hide_index=True)
    c = st.columns(2)
    c[0].download_button("⬇ CSV 다운로드", v.drop(columns=["id"]).to_csv(index=False).encode("utf-8-sig"),
                         "ab_records.csv", "text/csv")
    c[1].download_button("⬇ 엑셀 다운로드", to_excel_bytes(v.drop(columns=["id"]), "AB기록"),
                         "ab_records.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ════════════════ 4) 소재 기획 리뷰 ════════════════
elif PAGE == "🧭 소재 기획 리뷰":
    st.markdown("<div class='sec-title'>소재 기획 리뷰</div><div class='sec-sub'>다음 소재를 기획하기 전, 과거 이긴 소재의 공통점을 확인하세요</div>", unsafe_allow_html=True)
    df = load_df()
    c = st.columns(3)
    cat = c[0].selectbox("강의 카테고리", sorted(df["카테고리"].unique()))
    goal = c[1].selectbox("목표", ["전환 최대화 (CVR)", "효율 최대화 (CPA 최소)"])
    topk = c[2].slider("우수 소재 기준 상위 N", 2, 10, 4)
    sub = df[df["카테고리"] == cat].copy()
    if len(sub) == 0:
        st.warning("해당 카테고리 데이터가 없습니다.")
    else:
        winners = (sub.sort_values("CVR", ascending=False) if goal.startswith("전환")
                   else sub.sort_values("CPA", ascending=True)).head(topk)

        def mode(col):
            m = winners[col].mode()
            return m.iloc[0] if len(m) else "-"

        st.markdown(f"<div class='sec-title' style='color:{GREEN}'>✅ '{cat}' 이기는 소재의 공통점</div>", unsafe_allow_html=True)
        c = st.columns(5)
        c[0].metric("이기는 소구", mode("소구포인트"))
        c[1].metric("이기는 후킹", mode("후킹"))
        c[2].metric("최적 포맷", mode("포맷"))
        c[3].metric("권장 컷 수", f"{int(winners['컷수'].median())}컷")
        c[4].metric("권장 길이", f"{int(winners['길이초'].median())}초")
        st.success(
            f"💡 다음 소재 기획 가이드 — **{mode('소구포인트')}** 소구를 **{mode('후킹')}** 후킹으로, "
            f"**{mode('포맷')}** 포맷 · 약 **{int(winners['길이초'].median())}초 / {int(winners['컷수'].median())}컷** 구성 추천. "
            f"(과거 상위 {topk}개 소재 공통 패턴)")
        st.markdown("<div class='sec-sub' style='margin-top:14px'>근거가 된 우수 소재</div>", unsafe_allow_html=True)
        st.dataframe(winners[["date", "강의", "소재명", "소구포인트", "후킹", "포맷", "컷수", "길이초", "CTR", "CVR", "CPA", "등급"]],
                     use_container_width=True, hide_index=True)
        if st.button("🎬 이 방향으로 컷별 프롬프트 만들기 →", type="primary"):
            st.session_state["plan"] = {"강의": winners.iloc[0]["강의"], "소구": mode("소구포인트"),
                                        "후킹": mode("후킹"), "길이": int(winners["길이초"].median()),
                                        "컷수": max(3, int(winners["컷수"].median()))}
            st.session_state["_goto_gen"] = True
            st.rerun()


# ════════════════ 5) 컷별 프롬프트 생성 ════════════════
elif PAGE == "🎬 컷별 프롬프트 생성":
    st.markdown("<div class='sec-title'>컷별 프롬프트 생성</div><div class='sec-sub'>기획 방향을 입력하면 컷(씬)별 영상 프롬프트·자막·나레이션을 만들고 엑셀로 다운로드</div>", unsafe_allow_html=True)
    p = st.session_state.get("plan", {})
    c = st.columns(3)
    product = c[0].text_input("강의/상품", p.get("강의", "패스트캠퍼스 · 데이터 분석 올인원"))
    angle = c[1].text_input("소구포인트", p.get("소구", "커리어 전환"))
    hook = c[2].selectbox("후킹 유형", HOOKS, index=HOOKS.index(p.get("후킹")) if p.get("후킹") in HOOKS else 0)
    c = st.columns(3)
    tone = c[0].selectbox("톤", ["공감 드라마", "다큐/뉴스", "경쾌/밈", "프리미엄"])
    dur = c[1].slider("길이(초)", 8, 40, int(p.get("길이", 16)))
    cuts = c[2].slider("컷 수", 3, 10, int(p.get("컷수", 5)))

    if st.button("⚡ 컷별 프롬프트 생성", type="primary"):
        rows = None
        if _client:
            try:
                prompt = (
                    "너는 온라인 교육(강의) 광고의 AI 영상 디렉터다. 아래 조건으로 컷(씬)별 스토리보드를 만들어라.\n"
                    f"[강의] {product} / [소구] {angle} / [후킹] {hook} / [톤] {tone} / [길이] {dur}초 / [컷수] {cuts}\n"
                    "각 컷마다: scene(장면설명 한국어), video_prompt(영문 영상생성 프롬프트, 끝에 반드시 \"No text, no letters.\" 포함), "
                    f"subtitle(한국어 자막), narration(한국어 나레이션). 정확히 {cuts}개의 컷을 만들어라.\n"
                    "반드시 JSON으로만 응답(설명·코드펜스 금지): "
                    '{"cuts":[{"scene":"","video_prompt":"","subtitle":"","narration":""}]}'
                )
                with st.spinner(f"Claude({CLAUDE_MODEL})가 컷별 스토리보드를 생성 중..."):
                    resp = _client.messages.create(model=CLAUDE_MODEL, max_tokens=4000,
                                                   messages=[{"role": "user", "content": prompt}])
                raw = next((b.text for b in resp.content if b.type == "text"), "").strip()
                if raw.startswith("```"):
                    raw = raw.strip("`"); raw = raw[raw.find("{"): raw.rfind("}") + 1]
                rows = json.loads(raw).get("cuts", [])
            except Exception as e:  # noqa
                st.error(f"생성 실패(템플릿으로 대체): {e}")
        if rows is None:
            seg = max(1, dur // cuts)
            rows = [{"scene": f"{angle} 관련 장면 {i+1} ({hook} 후킹, {tone} 톤)",
                     "video_prompt": f"Cinematic {tone} scene for an online course about {product}, photorealistic, highly detailed. No text, no letters.",
                     "subtitle": f"[{i+1}컷 자막] {angle} 메시지",
                     "narration": f"[{i+1}컷 나레이션] {angle}을(를) {hook}으로 전달"} for i in range(cuts)]
            if not _client:
                st.warning("데모 모드(템플릿)입니다. Secrets에 ANTHROPIC_API_KEY를 넣으면 실제 생성됩니다.")
        out = pd.DataFrame([{"컷": i + 1, "시간(초)": f"{i*(dur//cuts)}-{min(dur,(i+1)*(dur//cuts))}",
                             "장면": r.get("scene", ""), "영상 프롬프트(영문)": r.get("video_prompt", ""),
                             "자막": r.get("subtitle", ""), "나레이션": r.get("narration", "")}
                            for i, r in enumerate(rows)])
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
