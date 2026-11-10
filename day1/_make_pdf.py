"""
day1/portfolio.html → A4 PDF (데이원 제출용)
- 페이지 분리/축소/인쇄 보정은 전부 portfolio.html 의 <style>@media print 에 내장되어 있음.
  (브라우저 Cmd+P, Claude Design 인쇄, 이 스크립트 모두 같은 결과가 나오도록 단일 소스로 통일)
- 따라서 여기서는 등장 애니메이션만 강제 해제하고, 인쇄 미디어로 그대로 PDF 출력.
"""
import sys, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
SRC = (HERE / "portfolio.html").as_uri()
OUT = "/Users/jiuk/마케팅 개발/포트폴리오/데이원/윤지욱_포트폴리오_데이원.pdf"

# 스크롤 등장(IntersectionObserver) 요소가 headless 캡처 시 숨지 않도록 js-motion 해제.
# (인쇄 CSS에도 opacity:1 !important 가 있어 이중 안전장치)
FORCE_SHOW = """
  document.documentElement.classList.remove('js-motion');
  document.documentElement.classList.add('loaded');
  document.querySelectorAll('.reveal,.hero-anim,.grow-x,.grow-y').forEach(function(e){ e.classList.add('in'); });
"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1600}, device_scale_factor=2)
        page.goto(SRC, wait_until="networkidle", timeout=120000)
        page.evaluate(FORCE_SHOW)
        page.evaluate("document.fonts && document.fonts.ready")
        try:
            page.wait_for_function("document.fonts.status === 'loaded'", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        page.emulate_media(media="print")
        # scale/페이지크기/break 는 HTML @media print 가 전담 → 여기선 건드리지 않음
        page.pdf(path=OUT, print_background=True, prefer_css_page_size=True)
        browser.close()
    print("PDF OK ->", OUT)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("PDF FAIL:", e)
        sys.exit(1)
