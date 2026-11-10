# 🎬 AI 소재 A/B 스튜디오 (내부 공유용)

광고 소재 **A/B 테스트 운영 대시보드** — 퍼포먼스 마케팅 대시보드를 소재 A/B에 맞춘 버전.
윤지욱 · AI 마케터

## 메뉴 (사이드바 분리 — 화면 좁아도 버튼 안 사라짐)
| 메뉴 | 하는 일 |
|---|---|
| **📊 성과 분석** | 기록된 A/B 데이터로 KPI·후킹별 CVR·포맷별 CTR·업종별 최적 소재·이기는 소재 공통점 |
| **📝 A/B 데이터 기록** | 집행 소재 결과 입력(지표 직접 or 노출·클릭·전환·비용 자동계산), 등급 자동 산정, CSV 일괄 업로드 |
| **🔍 과거 데이터 조회** | 업종·후킹·포맷·등급 필터 + 검색, CSV/엑셀 다운로드 |
| **🧭 소재 기획 리뷰** | 업종·목표 선택 → **과거 이긴 소재의 공통점(소구·후킹·포맷·컷수·길이) 리뷰 + 다음 소재 가이드** |
| **🎬 컷별 프롬프트 생성** | 방향 입력 → 컷(씬)별 영상 프롬프트·자막·나레이션 생성 → **엑셀(.xlsx) 다운로드** |

- 데이터: **SQLite**(`ab_studio.db`) · 첫 실행 시 샘플 자동 시드
- 컷별 생성: **Claude**(Anthropic API, 키 있을 때) / 키 없으면 템플릿 데모
- 생성 결과·조회 결과 모두 **엑셀·CSV 다운로드**

> 공개 포폴 데모(정적): https://jiuk-bot.github.io/day1/tool.html · /insights.html
> 이 레포는 **팀이 실제로 쓰는 라이브 버전**.

---

## 로컬 실행
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # 값 채우기(선택)
streamlit run app.py        # 또는: python3 -m streamlit run app.py
```
> 키 없이도 **데모 모드**로 실행됨(기록·조회·분석·리뷰 모두 작동, 컷 생성만 템플릿).

## 팀에 공유 — Streamlit Community Cloud
1. 이 폴더를 **GitHub(private) 레포로 push**
2. https://share.streamlit.io → New app → `app.py` → Deploy
3. **Settings → Secrets** 에 붙여넣기 (키는 코드에 안 넣음)
   ```toml
   ANTHROPIC_API_KEY = "실제_Claude_키"
   CLAUDE_MODEL      = "claude-opus-4-8"   # 비용 아끼려면 claude-haiku-4-5
   APP_PASSWORD   = "팀_공유_비밀번호"
   ```
4. **접근 제어**: Settings → Sharing → "Only specific people" → **팀원 구글 이메일 추가** (+ 비밀번호 이중 잠금)
5. URL 공유 → 끝. push 하면 자동 재배포.

### ⚠️ 데이터 영속성
Streamlit Cloud는 재시작 시 파일이 초기화됩니다(SQLite 휘발). 팀 공용 영구 저장이 필요하면
**Google Sheet / Supabase / 외부 DB**로 교체하세요(함수 `load_df`·`add_row`만 바꾸면 됨). 로컬·단일세션은 그대로 OK.

## 핵심 원칙
- **API 키는 정적 페이지에 두지 않는다** → Streamlit **Secrets(서버)** 에만. `secrets.toml`은 `.gitignore`로 깃 제외.
- 사내 전용 = **이메일 허용목록 + 비밀번호** 이중 제어.

## 파일
```
app.py                          # 5개 메뉴 (기록·조회·분석·기획리뷰·컷생성)
requirements.txt                # streamlit, google-generativeai, pandas, openpyxl
.streamlit/secrets.toml.example
.gitignore                      # secrets.toml, *.db 제외
```
