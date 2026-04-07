#!/usr/bin/env python3
"""
카니보어 책 원고 → 출판물 PDF 생성 (WeasyPrint)
신국판 (152 x 225mm), 나눔명조 본문, 나눔고딕 제목
"""

import re
import os
import markdown
from weasyprint import HTML, CSS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
CHART_DIR = os.path.join(BASE_DIR, "_charts")
OUTPUT_PDF = os.path.join(BASE_DIR, "카니보어_출판본.pdf")


# ── 마크다운 전처리 ─────────────────────────────────
def preprocess_markdown(text, chapter_file=""):
    """마크다운을 출판에 맞게 전처리"""
    lines = text.split('\n')
    result = []
    in_reference = False

    for line in lines:
        # 구분선(---) → 페이지 내 시각적 구분
        if line.strip() == '---':
            result.append('<div class="section-divider"></div>\n')
            continue

        # 참고 문헌 섹션 스타일링
        if line.strip().startswith('### 참고 문헌') or line.strip().startswith('## 참고 문헌'):
            in_reference = True
            result.append('<div class="references">\n')
            result.append('#### 참고 문헌\n')
            continue

        if in_reference:
            if line.strip().startswith('#') or (not line.strip() and not any(l.strip().startswith('- ') for l in lines[lines.index(line)+1:lines.index(line)+3] if lines.index(line)+1 < len(lines))):
                result.append('</div>\n')
                in_reference = False
                result.append(line + '\n')
            elif line.strip().startswith('- '):
                result.append(line + '\n')
            else:
                result.append(line + '\n')
            continue

        result.append(line + '\n')

    if in_reference:
        result.append('</div>\n')

    return ''.join(result)


def insert_charts_in_html(html_content):
    """HTML에 차트 이미지를 적절한 위치에 삽입"""
    chart_insertions = [
        {
            'after_text': '우리는 역사상 가장 많이 먹고',
            'chart': 'metabolic_health.png',
            'caption': '미국 성인 대사건강 현황 (Araújo et al., 2018; O\'Hearn et al., 2022)'
        },
        {
            'after_text': '농업의 발명은 인류 역사상 최악의 실수',
            'chart': 'timeline.png',
            'caption': '인류 식단 역사: 250만 년 육식 기반 (99.6%) vs 1만 년 농경 (0.4%) — 농경 시작점(약 1만 년 전) 이후 만성질환 급증'
        },
        {
            'after_text': '역사상 가장 많이 아픈 시대',
            'chart': 'obesity_trend.png',
            'caption': '미국 성인 비만율 변화 1976-2023 (출처: CDC NHANES)'
        },
        {
            'after_text': '당뇨는 폭발했고',
            'chart': 'diabetes_trend.png',
            'caption': '미국 당뇨 유병률 변화 1958-2020 (출처: CDC)'
        },
        {
            'after_text': '50년 만에 채소의 영양밀도가',
            'chart': 'nutrient_decline.png',
            'caption': '채소·과일 영양소 감소 추이 (Davis et al., 2004)'
        },
        {
            'after_text': '실제 흡수량은 소간의',
            'chart': 'iron_absorption.png',
            'caption': '철분: 명목 함량 vs 실제 흡수량 — 소간(헴철) vs 시금치(비헴철)'
        },
        {
            'after_text': 'TG/HDL 비율',
            'chart': 'tg_hdl_ratio.png',
            'caption': 'TG/HDL 비율과 심혈관 위험도'
        },
        {
            'after_text': '95%가 전반적 건강 개선',
            'chart': 'carnivore_improvement.png',
            'caption': '카니보어 실천자 건강 개선 비율 (Lennerz et al., 2021, n=2,029)'
        },
    ]

    chart_used = set()
    for item in chart_insertions:
        chart_path = os.path.join(CHART_DIR, item['chart'])
        if not os.path.exists(chart_path):
            continue
        if item['chart'] in chart_used:
            continue

        # 텍스트 바로 다음 </p> 뒤에 차트 삽입
        search_text = item['after_text']
        pos = html_content.find(search_text)
        if pos >= 0:
            # 해당 문단이 끝나는 </p> 찾기
            end_p = html_content.find('</p>', pos)
            if end_p >= 0:
                insert_pos = end_p + 4
                chart_html = f'''
<figure class="chart-figure">
    <img src="file://{chart_path}" alt="{item['caption']}">
    <figcaption>{item['caption']}</figcaption>
</figure>
'''
                html_content = html_content[:insert_pos] + chart_html + html_content[insert_pos:]
                chart_used.add(item['chart'])

    return html_content


# ── CSS 스타일 (출판물 디자인) ──────────────────────
BOOK_CSS = '''
/* ── 페이지 설정: 신국판 152x225mm ── */
@page {
    size: 152mm 225mm;
    margin: 20mm 18mm 22mm 20mm;  /* 상 우 하 좌 (제본 여백) */

    @bottom-center {
        content: counter(page);
        font-family: "Nanum Gothic", sans-serif;
        font-size: 10pt;
        color: #999;
    }
}

/* 표지: 페이지 번호 없음 */
@page :first {
    @bottom-center { content: none; }
}

/* 부(Part) 타이틀: 페이지 번호 없음 */
@page part-page {
    @bottom-center { content: none; }
}

/* ── 본문 타이포그래피 ── */
body {
    font-family: "Nanum Myeongjo", "AppleMyungjo", serif;
    font-size: 12pt;
    line-height: 1.7;
    color: #1a1a1a;
    text-align: justify;
    word-break: keep-all;
    orphans: 3;
    widows: 3;
}

/* ── 표지 ── */
.cover {
    page-break-after: always;
    text-align: center;
    padding-top: 55mm;
}

.cover h1 {
    font-family: "Nanum Gothic", "Apple SD Gothic Neo", sans-serif;
    font-size: 32pt;
    font-weight: 800;
    color: #1a1a1a;
    margin: 0;
    letter-spacing: 3pt;
}

.cover .subtitle {
    font-family: "Nanum Myeongjo", serif;
    font-size: 15pt;
    color: #666;
    margin-top: 12pt;
}

.cover .divider {
    width: 40mm;
    height: 0.5pt;
    background: #8B0000;
    margin: 25pt auto;
}

.cover .year {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 12pt;
    color: #999;
    margin-top: 30pt;
}

/* ── 목차 ── */
.toc {
    page-break-after: always;
}

.toc h2 {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 18pt;
    color: #1a1a1a;
    border-bottom: 1pt solid #ddd;
    padding-bottom: 8pt;
    margin-bottom: 16pt;
}

.toc .toc-part {
    font-family: "Nanum Gothic", sans-serif;
    font-weight: 700;
    font-size: 12pt;
    color: #8B0000;
    margin-top: 10pt;
    margin-bottom: 2pt;
}

.toc .toc-chapter {
    font-size: 11pt;
    color: #555;
    margin-left: 12pt;
    margin-top: 2pt;
    margin-bottom: 2pt;
}

/* ── 부(Part) 타이틀 ── */
.part-title {
    page: part-page;
    page-break-before: always;
    page-break-after: always;
    text-align: center;
    padding-top: 65mm;
}

.part-title .part-num {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 13pt;
    color: #8B0000;
    letter-spacing: 2pt;
}

.part-title h2 {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 22pt;
    font-weight: 700;
    color: #1a1a1a;
    margin-top: 10pt;
    border: none;
}

.part-title .part-divider {
    width: 30mm;
    height: 0.4pt;
    background: #8B0000;
    margin: 15pt auto;
}

/* ── 제목 ── */
h1 {
    font-family: "Nanum Gothic", "Apple SD Gothic Neo", sans-serif;
    font-size: 20pt;
    font-weight: 700;
    color: #1a1a1a;
    margin-top: 0;
    margin-bottom: 14pt;
    page-break-before: always;
}

h2 {
    font-family: "Nanum Gothic", "Apple SD Gothic Neo", sans-serif;
    font-size: 15pt;
    font-weight: 700;
    color: #333;
    margin-top: 22pt;
    margin-bottom: 10pt;
    border-bottom: 0.5pt solid #ddd;
    padding-bottom: 5pt;
}

h3 {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 13pt;
    font-weight: 700;
    color: #444;
    margin-top: 16pt;
    margin-bottom: 8pt;
}

h4 {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 12pt;
    font-weight: 700;
    color: #555;
    margin-top: 12pt;
    margin-bottom: 6pt;
}

/* ── 본문 ── */
p {
    margin-top: 0;
    margin-bottom: 8pt;
}

/* 볼드 텍스트 (강조) */
strong {
    font-weight: 700;
    color: #1a1a1a;
}

/* ── 인용구 ── */
blockquote {
    margin: 14pt 0 14pt 0;
    padding: 10pt 14pt;
    border-left: 2.5pt solid #8B0000;
    background: #f9f6f1;
    font-style: italic;
    color: #444;
    font-size: 11.5pt;
    line-height: 1.6;
}

blockquote strong {
    color: #8B0000;
    font-style: normal;
}

blockquote p {
    margin-bottom: 4pt;
}

/* ── 리스트 ── */
ul, ol {
    margin: 8pt 0;
    padding-left: 18pt;
}

li {
    margin-bottom: 4pt;
    font-size: 11.5pt;
    line-height: 1.6;
}

/* ── 테이블 ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10.5pt;
    line-height: 1.4;
    page-break-inside: avoid;
}

thead th {
    background: #2C3E50;
    color: white;
    font-family: "Nanum Gothic", sans-serif;
    font-weight: 700;
    padding: 6pt 8pt;
    text-align: center;
    border: 0.5pt solid #2C3E50;
}

tbody td {
    padding: 5pt 8pt;
    border: 0.5pt solid #ddd;
    text-align: center;
    color: #333;
}

tbody tr:nth-child(even) {
    background: #f8f9fa;
}

/* ── 차트/이미지 ── */
figure.chart-figure {
    margin: 16pt 0;
    text-align: center;
    page-break-inside: avoid;
}

figure.chart-figure img {
    max-width: 90%;
    height: auto;
    max-height: 75mm;
}

figure.chart-figure figcaption {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 9.5pt;
    color: #999;
    margin-top: 6pt;
    font-style: italic;
}

/* ── 구분선 ── */
.section-divider {
    width: 25mm;
    height: 0;
    border-top: 0.5pt solid #ccc;
    margin: 16pt auto;
}

hr {
    border: none;
    border-top: 0.5pt solid #ccc;
    width: 25mm;
    margin: 16pt auto;
}

/* ── 참고 문헌 ── */
.references {
    margin-top: 20pt;
    padding-top: 10pt;
    border-top: 0.5pt solid #ddd;
}

.references h4 {
    font-family: "Nanum Gothic", sans-serif;
    font-size: 11pt;
    color: #888;
    margin-bottom: 8pt;
}

.references ul {
    list-style: none;
    padding-left: 0;
}

.references li {
    font-size: 9.5pt;
    color: #888;
    line-height: 1.4;
    margin-bottom: 3pt;
    text-indent: -10pt;
    padding-left: 10pt;
}

/* ── 이미지 일반 ── */
img {
    max-width: 100%;
    height: auto;
}

/* ── 계단형 식재료 스펙트럼 표 ── */
table.spectrum-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16pt 0;
    font-size: 9pt;
    line-height: 1.3;
    page-break-inside: avoid;
}

table.spectrum-table thead th {
    background: #2C3E50;
    color: white;
    font-family: "Nanum Gothic", sans-serif;
    font-weight: 700;
    padding: 5pt 4pt;
    text-align: center;
    border: 0.8pt solid #2C3E50;
    font-size: 8.5pt;
}

table.spectrum-table tbody td {
    padding: 3pt 4pt;
    border: 0.5pt solid #bbb;
    text-align: left;
    color: #333;
    font-size: 8.5pt;
    vertical-align: middle;
}

/* 식단 단계 병합 셀 — 세로 중앙, 볼드, 색상 구분 */
table.spectrum-table td.level-1 {
    background: #8B0000;
    color: white;
    font-weight: 700;
    text-align: center;
    font-family: "Nanum Gothic", sans-serif;
    font-size: 8.5pt;
    writing-mode: horizontal-tb;
}

table.spectrum-table td.level-2 {
    background: #C0392B;
    color: white;
    font-weight: 700;
    text-align: center;
    font-family: "Nanum Gothic", sans-serif;
    font-size: 8.5pt;
}

table.spectrum-table td.level-3 {
    background: #D35400;
    color: white;
    font-weight: 700;
    text-align: center;
    font-family: "Nanum Gothic", sans-serif;
    font-size: 8.5pt;
}

table.spectrum-table td.level-4 {
    background: #F39C12;
    color: white;
    font-weight: 700;
    text-align: center;
    font-family: "Nanum Gothic", sans-serif;
    font-size: 8.5pt;
}

table.spectrum-table td.level-5 {
    background: #27AE60;
    color: white;
    font-weight: 700;
    text-align: center;
    font-family: "Nanum Gothic", sans-serif;
    font-size: 8.5pt;
}

/* 줄무늬 비활성화 (계단형에서는 불필요) */
table.spectrum-table tbody tr:nth-child(even) {
    background: transparent;
}

/* ── 페이지 브레이크 유틸 ── */
.page-break {
    page-break-after: always;
}
'''


# ── HTML 구성 ───────────────────────────────────────
def build_book_html():
    """전체 책 HTML 구성"""

    # 표지
    cover_html = '''
<div class="cover">
    <h1>카니보어</h1>
    <div class="subtitle">인간 본래의 식단으로 돌아가다</div>
    <div class="divider"></div>
    <div class="year">2026</div>
</div>
'''

    # 목차
    toc_html = '''
<div class="toc">
    <h2>목차</h2>
    <div class="toc-part">서문 &mdash; 나는 왜 이 책을 쓰게 되었는가</div>
    <div class="toc-part">제1부 &mdash; 우리는 왜 아플까?</div>
    <div class="toc-chapter">1장. 병든 시대, 건강의 원점을 묻다</div>
    <div class="toc-chapter">2장. 인간의 몸은 무엇을 위해 설계되었는가</div>
    <div class="toc-part">제2부 &mdash; 잃어버린 균형: 식물 문명이 만든 병든 인류</div>
    <div class="toc-chapter">1장. 과학의 탈을 쓴 조작 &mdash; 앤셀 키스와 지방 악마화의 역사</div>
    <div class="toc-chapter">2장. 콜레스테롤의 진실 &mdash; 70년간의 오해를 풀다</div>
    <div class="toc-chapter">3장. 식물식이 만든 인체 파괴 &mdash; 장에서 대사까지</div>
    <div class="toc-part">제3부 &mdash; 회복의 시작: 본래의 식단으로 돌아가다</div>
    <div class="toc-chapter">1장. 왜 육식인가 &mdash; 보충제 없이 완성되는 영양</div>
    <div class="toc-chapter">2장. 인간에게 가장 자연스러운 식단 &mdash; 카니보어의 과학적 근거</div>
    <div class="toc-chapter">3장. 식물식이 만든 오해와 왜곡된 상식</div>
    <div class="toc-part">제4부 &mdash; 잘못된 믿음과 진실의 회복</div>
    <div class="toc-part">제5부 &mdash; 실천 가이드: 카니보어 시작하기</div>
    <div class="toc-chapter">1장. 시작 가이드</div>
    <div class="toc-chapter">2장. 핵심 영양소와 보충 전략</div>
    <div class="toc-chapter">3장. 외식·사회생활 대응법</div>
    <div class="toc-chapter">4장. 부작용 대처법과 모니터링</div>
    <div class="toc-chapter">5장. 장기 유지 전략</div>
    <div class="toc-part">제6부 &mdash; 자주 묻는 질문과 사례</div>
    <div class="toc-chapter">1장. 의사·영양사 Q&amp;A</div>
    <div class="toc-chapter">2장. 실제 사례와 후기</div>
    <div class="toc-part">에필로그 &mdash; 식탁 위의 혁명</div>
    <div class="toc-part">부록</div>
</div>
'''

    # 챕터 순서
    chapters = [
        ("chapters/preface.md", None),
        (None, ("제1부", "우리는 왜 아플까?")),
        ("chapters/part1-chapter01.md", None),
        ("chapters/part1-chapter02.md", None),
        (None, ("제2부", "잃어버린 균형 — 식물 문명이 만든 병든 인류")),
        ("chapters/chapter-02.md", None),
        (None, ("제3부", "회복의 시작 — 본래의 식단으로 돌아가다")),
        ("chapters/chapter-03.md", None),
        (None, ("제4부", "잘못된 믿음과 진실의 회복")),
        ("chapters/chapter-04.md", None),
        (None, ("제5부", "실천 가이드 — 카니보어 시작하기")),
        ("chapters/chapter-05.md", None),
        (None, ("제6부", "자주 묻는 질문과 사례")),
        ("chapters/chapter-06.md", None),
        ("chapters/epilogue.md", None),
        ("chapters/appendix.md", None),
    ]

    body_html = ""

    for filepath, part_info in chapters:
        if part_info:
            # 부(Part) 타이틀 페이지
            part_num, part_title = part_info
            body_html += f'''
<div class="part-title">
    <div class="part-num">{part_num}</div>
    <h2>{part_title}</h2>
    <div class="part-divider"></div>
</div>
'''
        else:
            # 챕터 본문
            full_path = os.path.join(BASE_DIR, filepath)
            if not os.path.exists(full_path):
                print(f"  ⚠️ 파일 없음: {filepath}")
                continue

            print(f"  → {filepath} 처리 중...")
            with open(full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # "# 제X부 — ..." 형태의 중복 h1 제거 (이미 part-title로 생성)
            md_content = re.sub(r'^# 제\d부\s*[—\-].*$', '', md_content, flags=re.MULTILINE)

            # 마크다운 전처리
            md_content = preprocess_markdown(md_content, filepath)

            # 마크다운 → HTML 변환
            html = markdown.markdown(
                md_content,
                extensions=['tables', 'fenced_code', 'attr_list']
            )

            body_html += html + "\n"

    # 차트 삽입
    print("  → 차트 이미지 삽입 중...")
    body_html = insert_charts_in_html(body_html)

    # 전체 HTML
    full_html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>카니보어 — 인간 본래의 식단으로 돌아가다</title>
</head>
<body>
{cover_html}
{toc_html}
{body_html}
</body>
</html>'''

    return full_html


# ── 메인 ─────────────────────────────────────────
def main():
    print("📖 출판물 PDF 생성 시작...")
    print(f"   크기: 신국판 (152 x 225mm)")
    print(f"   본문: 나눔명조 10pt")
    print(f"   제목: 나눔고딕")
    print()

    # HTML 구성
    html_content = build_book_html()

    # HTML 임시 파일 저장 (디버깅용)
    html_path = os.path.join(BASE_DIR, "_book_temp.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  ✅ HTML 생성: {html_path}")

    # WeasyPrint로 PDF 변환
    print("  → PDF 렌더링 중 (1~2분 소요)...")
    html = HTML(string=html_content, base_url=BASE_DIR)
    css = CSS(string=BOOK_CSS)
    html.write_pdf(OUTPUT_PDF, stylesheets=[css])

    file_size = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
    print(f"\n✅ 출판물 PDF 생성 완료!")
    print(f"   파일: {OUTPUT_PDF}")
    print(f"   크기: {file_size:.1f}MB")


if __name__ == "__main__":
    main()
