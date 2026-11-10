# -*- coding: utf-8 -*-
"""
AI 소재 A/B 스튜디오 — 데이원컴퍼니 지원용 데모 (교육 콘텐츠 소재 운영)
윤지욱 · AI 마케터
① 성과 분석  ② 소재 A/B 기록  ③ 과거 데이터 조회  ④ 소재 기획 리뷰  ⑤ 컷별 프롬프트 생성(→엑셀)
- 디자인: 포트폴리오 네온 퍼플 테마 · 데이터: SQLite · 수치는 전부 가상(샘플)
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
  background-attachment:fixed; }}
#MainMenu {{ visibility:hidden; }}
[data-testid="stHeader"], [data-testid="stToolbar"] {{ display:none !important; }}
.block-container {{ padding-top:1.4rem; max-width:1300px; }}
.block-container h1 {{ font-size:1.95rem; font-weight:800; letter-spacing:-.025em;
  background:linear-gradient(120deg,#9D7BFF,#C06BFF,#FF6BD6,#9D7BFF);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
  filter:drop-shadow(0 0 26px rgba(170,110,255,.35)); }}
h2,h3,h4,h5 {{ color:{TEXT}; letter-spacing:-.01em; }}
p, label, span, .stMarkdown {{ color:{TEXT}; }}
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
/* 상단 탭 네비 (텍스트 + 하단 바, 선택 시 마젠타) */
[class*="st-key-navbtn_"] button {{ background:transparent !important; border:none !important;
  border-bottom:2px solid rgba(124,92,255,.14) !important; border-radius:0 !important;
  color:{MUTED} !important; font-weight:700 !important; font-size:14.5px !important;
  padding:8px 4px 12px !important; box-shadow:none !important; transition:color .15s, border-color .15s; }}
[class*="st-key-navbtn_"] button:hover {{ color:{TEXT} !important; transform:none !important; box-shadow:none !important; border-color:rgba(124,92,255,.4) !important; }}
[class*="st-key-navbtn_"] button[kind="primary"] {{ color:#fff !important; border-bottom:2px solid {ACCENT2} !important; background:transparent !important; box-shadow:none !important; }}
/* 입력 */
div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stDateInput input {{
  border:1px solid {BORDER} !important; border-radius:10px !important; background:rgba(18,18,30,.6) !important; color:{TEXT} !important; }}
div[data-testid="stExpander"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:14px; }}
.stButton>button, .stDownloadButton>button {{ border-radius:11px; font-weight:800; border:1px solid rgba(124,92,255,.42);
  background:rgba(124,92,255,.08); color:{TEXT}; transition:transform .2s, box-shadow .2s, border-color .2s; }}
.stButton>button:hover, .stDownloadButton>button:hover {{ transform:translateY(-2px); border-color:rgba(170,120,255,.85); box-shadow:0 0 26px -6px rgba(124,92,255,.55); }}
.stButton>button[kind="primary"] {{ background:linear-gradient(135deg,#7C5CFF,#C06BFF) !important; border:0 !important; color:#fff !important; box-shadow:0 12px 32px -10px rgba(124,92,255,.7); }}
div[data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; }}
.stAlert {{ border-radius:12px; }}
/* 운영기간 달력 — 월 이동 헤더/화살표 선명하게 (다크) */
div[data-baseweb="calendar"] {{ background:#15151f !important; border:1px solid rgba(124,92,255,.35) !important; border-radius:12px !important; padding:6px !important; }}
div[data-baseweb="calendar"] header, div[data-baseweb="calendar"] [role="presentation"] {{ visibility:visible !important; display:flex !important; align-items:center !important; justify-content:space-between !important; }}
div[data-baseweb="calendar"] *, div[data-baseweb="calendar"] [role="gridcell"] {{ color:{TEXT} !important; }}
div[data-baseweb="calendar"] button {{ background:transparent !important; opacity:1 !important; visibility:visible !important; border:none !important; box-shadow:none !important; }}
div[data-baseweb="calendar"] button:hover {{ background:rgba(124,92,255,.25) !important; border-radius:8px !important; }}
div[data-baseweb="calendar"] svg {{ fill:{TEXT} !important; color:{TEXT} !important; width:22px !important; height:22px !important; }}
div[data-baseweb="calendar"] [aria-selected="true"] {{ background:linear-gradient(135deg,#7C5CFF,#C06BFF) !important; color:#fff !important; border-radius:8px !important; }}
.sec-title {{ font-size:15px; font-weight:800; color:{TEXT}; margin:8px 0 2px; }}
.sec-sub {{ font-size:12px; color:{MUTED}; margin-bottom:10px; }}
::selection {{ background:rgba(192,107,255,.4); color:#fff; }}
</style>
""", unsafe_allow_html=True)


def sget(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def check_password():
    pw = sget("APP_PASSWORD")
    if not pw or st.session_state.get("authed"):
        return
    st.markdown("### 🔒 내부 전용 — 접근 비밀번호")
    e = st.text_input("비밀번호", type="password", label_visibility="collapsed")
    if e == pw:
        st.session_state["authed"] = True; st.rerun()
    elif e:
        st.error("비밀번호가 올바르지 않습니다.")
    st.stop()


check_password()

# ── 데이터 (교육 콘텐츠 소재 · 가상 샘플 · 6개 카테고리 × 5) ──
DB_PATH = "ab_studio.db"
HOOKS = ["공감", "자극", "숫자", "권위", "사회적증거", "호기심"]
FORMATS = ["세로 숏폼", "가로 영상", "이미지", "카드뉴스"]
CATS = ["데이터", "AI", "개발", "영상/디자인", "마케팅", "기타"]

def _gen_seed(per=10):
    import random, datetime
    rnd = random.Random(42)
    courses = [("데이터", "데이터 분석 올인원"), ("AI", "AI 실무 부트캠프"), ("개발", "백엔드 개발 입문"),
               ("영상/디자인", "영상편집 마스터"), ("마케팅", "그로스 마케팅"), ("기타", "직무 영어 스피킹")]
    angles = ["커리어 전환", "연봉 상승", "부업·수익화", "실무 즉시적용", "비전공 접근성", "포트폴리오 완성"]
    cvr_base = {"공감": 4.7, "권위": 4.5, "사회적증거": 4.2, "호기심": 3.4, "숫자": 3.6, "자극": 2.0}
    ctr_base = {"세로 숏폼": 2.3, "가로 영상": 1.7, "이미지": 1.1, "카드뉴스": 1.0}
    dur_base = {"세로 숏폼": (15, 18), "가로 영상": (20, 23), "이미지": (0, 0), "카드뉴스": (0, 0)}
    rows = []
    for ci, (cat, course) in enumerate(courses):
        d0 = datetime.date(2026, 1, 5) + datetime.timedelta(days=ci * 30)
        for j in range(per):
            hook = HOOKS[j % len(HOOKS)] if j < len(HOOKS) else rnd.choice(HOOKS)
            fmt = rnd.choice(["가로 영상", "세로 숏폼"]) if hook == "자극" else rnd.choice(FORMATS)
            angle = rnd.choice(angles)
            cvr = round(max(1.4, cvr_base[hook] + rnd.uniform(-0.5, 0.5)), 1)
            ctr = round(max(0.8, ctr_base[fmt] + (0.8 if hook == "자극" else 0) + rnd.uniform(-0.3, 0.3)), 1)
            cpa = max(55000, int(round((155000 - cvr * 16000 + rnd.uniform(-16000, 16000)) / 1000) * 1000))
            lo, hi = dur_base[fmt]
            dur = rnd.randint(lo, hi) if hi else 0
            cuts = rnd.randint(4, 6) if fmt == "세로 숏폼" else (rnd.randint(3, 5) if fmt == "가로 영상" else 1)
            grade = "A" if (cvr >= 4.5 and cpa <= 80000) else ("B" if (cvr >= 3.5 and cpa <= 120000) else "C")
            rows.append(((d0 + datetime.timedelta(days=j * 3)).isoformat(), cat, course,
                         f"{angle} · {hook}형", angle, hook, fmt, cuts, dur, ctr, cvr, cpa, grade, "", ""))
    return rows


SEED = _gen_seed(10)

COLS = ["date", "카테고리", "강의", "소재명", "소구포인트", "후킹", "포맷", "컷수", "길이초", "CTR", "CVR", "CPA", "등급", "링크", "메모"]


def conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS ab (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, 카테고리 TEXT, 강의 TEXT, 소재명 TEXT,
        소구포인트 TEXT, 후킹 TEXT, 포맷 TEXT, 컷수 INTEGER, 길이초 INTEGER,
        CTR REAL, CVR REAL, CPA REAL, 등급 TEXT, 링크 TEXT, 메모 TEXT )""")
    c.commit()
    if c.execute("SELECT COUNT(*) FROM ab").fetchone()[0] == 0:
        c.executemany("INSERT INTO ab (" + ",".join(COLS) + ") VALUES (" + ",".join(["?"] * len(COLS)) + ")", SEED)
        c.commit()
    c.close()


def load_df():
    c = conn()
    df = pd.read_sql_query("SELECT * FROM ab ORDER BY date DESC, id DESC", c)
    c.close()
    return df


def add_row(r):
    c = conn()
    c.execute("INSERT INTO ab (" + ",".join(COLS) + ") VALUES (" + ",".join(["?"] * len(COLS)) + ")",
              tuple(r[k] for k in COLS))
    c.commit(); c.close()


def auto_grade(cvr, cpa):
    if cvr >= 4.5 and cpa <= 80000:
        return "A"
    if cvr >= 3.5 and cpa <= 120000:
        return "B"
    return "C"


def won(v):
    return f"₩{int(v):,}"


def num_comma(col, label, default):
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


def date_range(container, df, key):
    """운영기간: 시작일/종료일 달력 2개 → (시작, 종료) 'YYYY-MM-DD'."""
    dts = pd.to_datetime(df["date"], errors="coerce")
    dmin, dmax = dts.min().date(), dts.max().date()
    cc = container.columns(2)
    s = cc[0].date_input("운영 시작일", dmin, min_value=dmin, max_value=dmax, key=key + "_s", format="YYYY-MM-DD")
    e = cc[1].date_input("운영 종료일", dmax, min_value=dmin, max_value=dmax, key=key + "_e", format="YYYY-MM-DD")
    return str(min(s, e)), str(max(s, e))


def apply_dates(df, s, e):
    return df[(df["date"] >= s) & (df["date"] <= e)]


def fmt_display(d):
    """표시용: date→운영기간, CPA 천단위 콤마."""
    d = d.copy()
    if "date" in d.columns:
        d = d.rename(columns={"date": "운영기간"})
    if "CPA" in d.columns:
        d["CPA"] = d["CPA"].map(lambda x: f"{int(x):,}" if pd.notna(x) and str(x) != "" else x)
    return d


def bar(series, color=ACCENT, suffix="", h=300):
    s = series.sort_values(ascending=False)
    fig = go.Figure(go.Bar(x=[str(i) for i in s.index], y=list(s.values), marker_color=color,
                           text=[f"{v:.1f}{suffix}" for v in s.values], textposition="outside"))
    fig.update_layout(font_color=TEXT, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      height=h, margin=dict(l=10, r=10, t=22, b=10), showlegend=False)
    fig.update_xaxes(showgrid=False, linecolor="rgba(124,92,255,.25)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(124,92,255,.13)", zeroline=False)
    return fig


init_db()

# ── Claude(컷별 프롬프트 생성용) ──
_client = None
CLAUDE_MODEL = sget("CLAUDE_MODEL", "claude-opus-4-8")  # 비용 민감 시 claude-haiku-4-5
if sget("ANTHROPIC_API_KEY"):
    try:
        import anthropic
        _client = anthropic.Anthropic(api_key=sget("ANTHROPIC_API_KEY"))
    except Exception as e:  # noqa
        st.sidebar.error(f"Claude 초기화 실패: {e}")

# ── 사이드바 ──
with st.sidebar:
    st.markdown(f"<div style='font-size:17px;font-weight:800;color:{TEXT}'>🎬 AI 소재 A/B 스튜디오</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:12px;color:{MUTED};margin-top:2px'>윤지욱 · AI 마케터</div>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"<div style='font-size:12px;color:{MUTED};line-height:1.7'>"
                "교육 콘텐츠(패스트캠퍼스·콜로소) 광고 소재의<br>"
                f"A/B 결과를 <b style='color:{LILAC}'>기록·분석</b>하고, 다음 소재의<br>"
                f"<b style='color:{LILAC}'>이기는 공통점</b>을 리뷰하는 운영 툴.</div>", unsafe_allow_html=True)
    st.divider()
    st.caption("🟢 Claude 연결됨 · " + CLAUDE_MODEL if _client else "⚪ 데모 모드 (생성은 API 키 필요)")

# ── 페이지 정의 (텍스트 탭) ──
P1 = "성과 분석"; P2 = "소재 A/B 기록"; P3 = "과거 데이터 조회"; P4 = "소재 기획 리뷰"; P5 = "컷별 프롬프트 생성"
PAGES = [P1, P2, P3, P4, P5]

st.markdown("# AI 소재 A/B 스튜디오")
st.markdown("<div class='demo-banner'>📘 데이원컴퍼니 지원용 데모 · 표시되는 모든 수치는 가상(샘플) 데이터입니다 (교육 콘텐츠 소재 운영 예시)</div>", unsafe_allow_html=True)

if "nav" not in st.session_state:
    st.session_state["nav"] = P1
if st.session_state.pop("_goto_gen", False):
    st.session_state["nav"] = P5


def _nav_to(p):
    st.session_state["nav"] = p


_nc = st.columns(len(PAGES))
for _i, _pg in enumerate(PAGES):
    _nc[_i].button(_pg, key=f"navbtn_{_i}", use_container_width=True,
                   type=("primary" if st.session_state["nav"] == _pg else "secondary"),
                   on_click=_nav_to, args=(_pg,))
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
PAGE = st.session_state["nav"]


# ════════════════ 1) 성과 분석 ════════════════
if PAGE == P1:
    df = load_df()
    fc = st.columns([1.2, 1.8])
    cat_sel = fc[0].selectbox("📚 강의 카테고리", ["전체 카테고리"] + sorted(df["카테고리"].unique()))
    s, e = date_range(fc[1], df, "perf_range")
    v = df if cat_sel.startswith("전체") else df[df["카테고리"] == cat_sel]
    v = apply_dates(v, s, e)
    st.caption(f"📚 포함 강의 — {' · '.join(sorted(v['강의'].unique())) or '없음'}  ·  운영기간 {s} ~ {e}")

    if v.empty:
        st.info("선택한 운영기간/카테고리에 데이터가 없습니다.")
        st.stop()

    if len(v):
        av = v[v["등급"] == "A"]
        wh = (av["후킹"].mode().iloc[0] if len(av) and len(av["후킹"].mode()) else v.groupby("후킹")["CVR"].mean().idxmax())
        wf = (av["포맷"].mode().iloc[0] if len(av) and len(av["포맷"].mode()) else v.groupby("포맷")["CTR"].mean().idxmax())
        n_bad = int((v["등급"] == "C").sum())
        st.markdown("<div class='demo-banner' style='background:rgba(123,224,163,.08);border-color:rgba(123,224,163,.3);color:#bdeccf'>"
                    f"💡 <b>한눈에</b> — 지금 이기는 공식: <b>{wh} 후킹 × {wf}</b>. "
                    f"교체 후보: 등급 C 소재 <b>{n_bad}건</b>(CTR만 높고 전환 낮음) → 공감·신뢰형으로 교체 권장.</div>", unsafe_allow_html=True)

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
    top = v.sort_values("CVR", ascending=False).head(8)[
        ["date", "카테고리", "강의", "소재명", "소구포인트", "후킹", "포맷", "CTR", "CVR", "CPA", "등급"]]
    st.dataframe(fmt_display(top), use_container_width=True, hide_index=True)
    st.info("핵심 패턴: 자극형은 CTR↑·CVR↓(클릭만), **공감·권위·사회적증거형이 수강 전환**을 만든다. 세로 숏폼=CTR 우위, 이미지/카드뉴스=이탈 낮아 CVR 안정.")


# ════════════════ 2) 소재 A/B 기록 ════════════════
elif PAGE == P2:
    st.markdown("<div class='sec-title'>소재 A/B 결과 기록</div><div class='sec-sub'>지표를 직접 입력하거나, 노출·클릭·수강신청·비용으로 자동 계산</div>", unsafe_allow_html=True)
    mode = st.radio("입력 방식", ["지표 직접 입력", "원시값으로 자동 계산"], horizontal=True, key="recmode")
    with st.form("rec"):
        c = st.columns(3)
        d = c[0].date_input("운영 시작일", value=date.today())
        cat = c[1].selectbox("강의 카테고리", CATS)
        course = c[2].text_input("강의/클래스명", "데이터 분석 올인원")
        name = st.text_input("소재명", "")
        c = st.columns(4)
        angle = c[0].text_input("소구포인트", "커리어 전환")
        hook = c[1].selectbox("후킹 유형", HOOKS)
        fmt = c[2].selectbox("포맷", FORMATS)
        cuts = c[3].number_input("컷 수", 0, 100, 5)
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
                add_row({k2: r.get(k2, "") for k2 in COLS})
            st.success(f"{len(u)}건 추가 완료")
        except Exception as e:  # noqa
            st.error(f"업로드 실패: {e}")


# ════════════════ 3) 과거 데이터 조회 ════════════════
elif PAGE == P3:
    df = load_df()
    c = st.columns(4)
    f_cat = c[0].multiselect("강의 카테고리", sorted(df["카테고리"].unique()))
    f_hook = c[1].multiselect("후킹", sorted(df["후킹"].unique()))
    f_fmt = c[2].multiselect("포맷", sorted(df["포맷"].unique()))
    f_grade = c[3].multiselect("등급", ["A", "B", "C"])
    sc = st.columns([2, 2])
    kw = sc[0].text_input("강의/소재명 검색", "")
    s, e = date_range(sc[1], df, "hist_range")
    v = apply_dates(df.copy(), s, e)
    if f_cat: v = v[v["카테고리"].isin(f_cat)]
    if f_hook: v = v[v["후킹"].isin(f_hook)]
    if f_fmt: v = v[v["포맷"].isin(f_fmt)]
    if f_grade: v = v[v["등급"].isin(f_grade)]
    if kw.strip():
        v = v[v["강의"].str.contains(kw, case=False, na=False) | v["소재명"].str.contains(kw, case=False, na=False)]
    st.caption(f"{len(v)}건")
    raw = v.drop(columns=["id"])
    st.dataframe(fmt_display(raw), use_container_width=True, hide_index=True)
    c = st.columns(2)
    c[0].download_button("⬇ CSV 다운로드", raw.to_csv(index=False).encode("utf-8-sig"), "ab_records.csv", "text/csv")
    c[1].download_button("⬇ 엑셀 다운로드", to_excel_bytes(raw, "AB기록"), "ab_records.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ════════════════ 4) 소재 기획 리뷰 ════════════════
elif PAGE == P4:
    st.markdown("<div class='sec-title'>소재 기획 리뷰</div><div class='sec-sub'>다음 소재를 기획하기 전, 과거 이긴 소재의 공통점을 확인하세요</div>", unsafe_allow_html=True)
    df = load_df()
    c = st.columns([1.2, 1.3, 1, 1.6])
    cat = c[0].selectbox("강의 카테고리", sorted(df["카테고리"].unique()))
    goal = c[1].selectbox("목표", ["전환 최대화 (CVR)", "효율 최대화 (CPA 최소)"])
    topk = c[2].slider("우수 소재 기준 상위 N", 2, 10, 4)
    s, e = date_range(c[3], df, "review_range")
    sub = apply_dates(df[df["카테고리"] == cat], s, e).copy()
    if len(sub) == 0:
        st.warning("해당 카테고리 데이터가 없습니다.")
    else:
        asc = not goal.startswith("전환")
        winners = sub.sort_values("CPA" if asc else "CVR", ascending=asc).head(topk).reset_index(drop=True)
        w1 = winners.iloc[0]
        goal_short = "효율(CPA)" if asc else "전환(CVR)"
        st.markdown(f"<div class='sec-title' style='color:{GREEN}'>✅ '{cat}' · {goal_short} 기준 1위 소재 & 추천 방향</div>", unsafe_allow_html=True)
        c = st.columns(5)
        c[0].metric("1위 소재", w1["소재명"])
        c[1].metric("소구포인트", w1["소구포인트"])
        c[2].metric("후킹", w1["후킹"])
        c[3].metric("포맷", w1["포맷"])
        c[4].metric("최저 CPA" if asc else "최고 CVR", won(w1["CPA"]) if asc else f"{w1['CVR']}%")
        st.success(f"💡 다음 소재 기획 가이드 — **{w1['소구포인트']}** 소구를 **{w1['후킹']}** 후킹으로, "
                   f"**{w1['포맷']}** 포맷 · 약 **{int(w1['길이초'])}초 / {int(w1['컷수'])}컷** 구성 추천. "
                   f"(이 목표 기준 1위 소재: CTR {w1['CTR']}% · CVR {w1['CVR']}% · CPA {int(w1['CPA']):,}원)")
        st.markdown(f"<div class='sec-sub' style='margin-top:14px'>상위 소재 ({goal_short} 순 정렬)</div>", unsafe_allow_html=True)
        st.dataframe(fmt_display(winners[["date", "강의", "소재명", "소구포인트", "후킹", "포맷", "컷수", "길이초", "CTR", "CVR", "CPA", "등급"]]),
                     use_container_width=True, hide_index=True)
        if st.button("✨ 이 방향으로 컷별 프롬프트 만들기 →", type="primary"):
            st.session_state["plan"] = {"카테고리": cat, "강의": w1["강의"], "소구": w1["소구포인트"],
                                        "후킹": w1["후킹"], "포맷": w1["포맷"], "길이": int(w1["길이초"]), "컷수": max(3, int(w1["컷수"]))}
            st.session_state["_goto_gen"] = True
            st.rerun()


# ════════════════ 5) 컷별 프롬프트 생성 ════════════════
elif PAGE == P5:
    df = load_df()
    plan = st.session_state.get("plan", {})

    # ── 1단계 · 성과 조회 (옵션별 1~N위) ──
    st.markdown("<div class='sec-title'>1단계 · 성과 조회 — 어떤 소재가 얼마나 잘 됐나</div><div class='sec-sub'>카테고리·기준을 고르면 상위 소재 순위를 먼저 확인합니다</div>", unsafe_allow_html=True)
    cat_opts = ["전체 카테고리"] + sorted(df["카테고리"].unique())
    c = st.columns([1.3, 1.3, 1])
    _ci = cat_opts.index(plan["카테고리"]) if plan.get("카테고리") in cat_opts else 0
    g_cat = c[0].selectbox("강의 카테고리", cat_opts, index=_ci)
    g_goal = c[1].selectbox("정렬 기준", ["전환율(CVR) 높은 순", "효율(CPA) 좋은 순", "클릭률(CTR) 높은 순"])
    topn = c[2].slider("상위 N위", 3, 10, 5)
    sub = df if g_cat.startswith("전체") else df[df["카테고리"] == g_cat]
    key = {"전환율(CVR) 높은 순": ("CVR", False), "효율(CPA) 좋은 순": ("CPA", True), "클릭률(CTR) 높은 순": ("CTR", False)}[g_goal]
    rank = sub.sort_values(key[0], ascending=key[1]).head(topn).reset_index(drop=True)
    avg_cvr = sub["CVR"].mean() if len(sub) else 0
    show = rank.copy()
    show.insert(0, "순위", [f"{i+1}위" for i in range(len(show))])
    show["CVR 평균대비"] = show["CVR"].map(lambda x: f"{'+' if (x-avg_cvr) >= 0 else ''}{(x/avg_cvr-1)*100:.0f}%" if avg_cvr else "-")
    cols_show = ["순위", "date", "강의", "소재명", "소구포인트", "후킹", "포맷", "CTR", "CVR", "CVR 평균대비", "CPA", "등급"]
    st.dataframe(fmt_display(show[cols_show]), use_container_width=True, hide_index=True)

    # ── 2단계 · 방향 선택 → 생성 ──
    st.markdown("<div class='sec-title' style='margin-top:12px'>2단계 · 방향 선택 → 최종 프롬프트 생성</div><div class='sec-sub'>위 순위를 참고해 원하는 방향 옵션을 고르세요 (기본값=1위 소재)</div>", unsafe_allow_html=True)
    top1 = rank.iloc[0] if len(rank) else None
    ang_opts = sorted(sub["소구포인트"].unique()) if len(sub) else ["커리어 전환"]
    def _idx(lst, val, d=0):
        return lst.index(val) if val in lst else d
    c = st.columns(3)
    product = c[0].text_input("강의/상품", plan.get("강의") or (top1["강의"] if top1 is not None else "패스트캠퍼스 · 데이터 분석 올인원"))
    angle = c[1].selectbox("소구포인트(방향)", ang_opts, index=_idx(ang_opts, plan.get("소구") or (top1["소구포인트"] if top1 is not None else "")))
    hook = c[2].selectbox("후킹 유형", HOOKS, index=_idx(HOOKS, plan.get("후킹") or (top1["후킹"] if top1 is not None else "공감")))
    c = st.columns(3)
    tone = c[0].selectbox("톤", ["공감 드라마", "다큐/뉴스", "경쾌/밈", "프리미엄"])
    _dl = int(plan.get("길이") or (top1["길이초"] if top1 is not None else 16))
    dur = c[1].slider("길이(초)", 8, 60, max(8, _dl))
    cuts = c[2].slider("컷/프롬프트 수 (최대 100)", 3, 100, max(3, int(plan.get("컷수", 5))))

    if st.button("✨ 최종 컷별 프롬프트 생성", type="primary"):
        rows = None
        if _client:
            try:
                prompt = ("너는 온라인 교육(강의) 광고의 AI 영상 디렉터다. 아래 조건으로 컷(씬)별 스토리보드를 만들어라.\n"
                          f"[강의] {product} / [소구] {angle} / [후킹] {hook} / [톤] {tone} / [길이] {dur}초 / [컷수] {cuts}\n"
                          "각 컷마다: scene(장면설명 한국어), video_prompt(영문 영상생성 프롬프트, 끝에 반드시 \"No text, no letters.\" 포함), "
                          f"subtitle(한국어 자막), narration(한국어 나레이션). 정확히 {cuts}개의 컷을 만들어라.\n"
                          "반드시 JSON으로만 응답(설명·코드펜스 금지): "
                          '{"cuts":[{"scene":"","video_prompt":"","subtitle":"","narration":""}]}')
                mt = min(16000, 700 + cuts * 150)
                with st.spinner(f"Claude({CLAUDE_MODEL})가 {cuts}개 컷을 생성 중..."):
                    resp = _client.messages.create(model=CLAUDE_MODEL, max_tokens=mt,
                                                   messages=[{"role": "user", "content": prompt}])
                rawt = next((b.text for b in resp.content if b.type == "text"), "").strip()
                if rawt.startswith("```"):
                    rawt = rawt.strip("`"); rawt = rawt[rawt.find("{"): rawt.rfind("}") + 1]
                rows = json.loads(rawt).get("cuts", [])
            except Exception as e:  # noqa
                st.error(f"생성 실패(템플릿으로 대체): {e}")
        if rows is None:
            rows = [{"scene": f"{angle} 관련 장면 {i+1} ({hook} 후킹, {tone} 톤)",
                     "video_prompt": f"Cinematic {tone} scene for an online course about {product}, photorealistic, highly detailed. No text, no letters.",
                     "subtitle": f"[{i+1}컷 자막] {angle} 메시지",
                     "narration": f"[{i+1}컷 나레이션] {angle}을(를) {hook}으로 전달"} for i in range(cuts)]
            if not _client:
                st.warning("데모 모드(템플릿)입니다. Secrets에 ANTHROPIC_API_KEY를 넣으면 실제 생성됩니다.")
        seg = max(1, round(dur / max(1, cuts)))
        out = pd.DataFrame([{"컷": i + 1, "시간(초)": f"{i*seg}-{min(dur, (i+1)*seg)}",
                             "장면": r.get("scene", ""), "영상 프롬프트(영문)": r.get("video_prompt", ""),
                             "자막": r.get("subtitle", ""), "나레이션": r.get("narration", "")} for i, r in enumerate(rows)])
        st.session_state["cuts_out"] = out

    if "cuts_out" in st.session_state:
        out = st.session_state["cuts_out"]
        st.caption(f"{len(out)}개 컷")
        st.dataframe(out, use_container_width=True, hide_index=True)
        c = st.columns(2)
        c[0].download_button("⬇ 엑셀(.xlsx) 다운로드", to_excel_bytes(out, "컷별프롬프트"), "cut_prompts.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        c[1].download_button("⬇ CSV 다운로드", out.to_csv(index=False).encode("utf-8-sig"), "cut_prompts.csv", "text/csv")
