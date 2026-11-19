# 토스 BDR 발굴 대시보드 — 백엔드 배포 (실시간 기업 조회)

정적 사이트(GitHub Pages)는 CORS 때문에 뉴스·채용 사이트를 직접 크롤링할 수 없습니다.
그래서 **어떤 기업이든 실시간 조회**가 되려면 아주 작은 서버리스 API 하나를 올려야 합니다.
무료(Vercel Hobby), 신용카드 불필요, 약 2분.

## 구조
- 정적 사이트: GitHub Pages (`jiuk-bot.github.io/tossbdr`) — 그대로 유지
- 수집 로직: `tossbdr/scripts/collector_lib.py` (배치·API 공용)
- 배치(일일 큐 20곳): GitHub Actions `tossbdr-discovery.yml` → `data/*.json`
- **온디맨드 API**: `api/collect.py` (Vercel 서버리스) — 브라우저가 호출하면 즉시 수집

## Vercel 배포 (2분)
1. https://vercel.com → GitHub로 로그인
2. **Add New → Project → `jiuk-bot/jiuk-bot.github.io` import**
3. Framework Preset: **Other** (빌드 설정 불필요), **Deploy**
4. 배포되면 URL이 생깁니다 — 예: `https://jiuk-bot.vercel.app`
5. 동작 확인: 브라우저에서
   `https://<배포URL>/api/collect?company=쿠팡` → JSON이 나오면 성공
6. `tossbdr/discovery.html` 상단 스크립트의
   `var API_BASE = '';` → `var API_BASE = 'https://<배포URL>';` 로 바꿔 커밋

→ 이제 기업 조회 탭에서 **아무 회사명**이나 검색하면 로딩 후 실시간 스코어링·뉴스·채용이 뜹니다.

## 참고
- 업종/홈페이지를 모르는 임의 기업은 뉴스·채용 기반으로 스코어링합니다
  (계절성·타깃 핏은 업종을 알 때만). `?industry=&target=&hp=` 파라미터로 보강 가능.
- 광고 집행 여부(메타/구글)는 헤드리스 브라우저가 필요해 이 API에는 미포함 —
  컨테이너 호스트(Render/Fly) + Playwright로 확장하면 추가할 수 있습니다.
