#!/usr/bin/env python3
"""
카니보어 책 원고 → 인쇄용 HTML 생성 (브라우저에서 Ctrl+P로 PDF 변환)
WeasyPrint 불필요, Python + markdown 모듈만 사용
"""

import re
import os
import markdown

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters_compact")
CHART_DIR = os.path.join(BASE_DIR, "_charts")
OUTPUT_HTML = os.path.join(BASE_DIR, "카니보어_압축본.html")


# ── 마크다운 전처리 ─────────────────────────────────
def preprocess_markdown(text, chapter_file=""):
    """마크다운을 출판에 맞게 전처리"""
    lines = text.split('\n')
    result = []
    in_reference = False

    for line in lines:
        # 구분선(---) → 시각적 구분
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
            'caption': '인류 식단 역사: 250만 년 육식 기반 (99.6%) vs 1만 년 농경 (0.4%)'
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

        search_text = item['after_text']
        pos = html_content.find(search_text)
        if pos >= 0:
            end_p = html_content.find('</p>', pos)
            if end_p >= 0:
                insert_pos = end_p + 4
                # file:// 경로를 상대 경로로 변환
                rel_path = os.path.relpath(chart_path, BASE_DIR).replace('\\', '/')
                chart_html = f'''
<figure class="chart-figure">
    <img src="{rel_path}" alt="{item['caption']}">
    <figcaption>{item['caption']}</figcaption>
</figure>
'''
                html_content = html_content[:insert_pos] + chart_html + html_content[insert_pos:]
                chart_used.add(item['chart'])

    return html_content


# ── CSS (인쇄용 + 화면용) ──────────────────────────
BOOK_CSS = '''
/* ── 인쇄 설정: 신국판 152x225mm ── */
@media print {
    @page {
        size: 182mm 257mm;
        margin: 20mm 18mm 22mm 20mm;
    }
    body { font-size: 10.5pt; }
    .no-print { display: none; }
}

/* ── 화면 표시: 신국판 비율 ── */
@media screen {
    body {
        max-width: 182mm;
        margin: 0 auto;
        padding: 20mm 18mm;
        background: #f5f5f5;
    }
}

/* ── 웹폰트 ── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&family=Noto+Sans+KR:wght@400;700;900&display=swap');

/* ── 본문 타이포그래피 ── */
body {
    font-family: "Noto Serif KR", "Nanum Myeongjo", serif;
    font-size: 12pt;
    line-height: 1.8;
    color: #1a1a1a;
    text-align: justify;
    word-break: keep-all;
    background: white;
}

/* ── 표지 ── */
.cover {
    page-break-after: always;
    text-align: center;
    padding-top: 80mm;
    min-height: 100vh;
}

.cover h1 {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 36pt;
    font-weight: 900;
    color: #1a1a1a;
    margin: 0;
    letter-spacing: 3pt;
}

.cover .subtitle {
    font-family: "Noto Serif KR", serif;
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

.cover .author {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 14pt;
    color: #444;
    margin-top: 20pt;
}

.cover .year {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 12pt;
    color: #999;
    margin-top: 10pt;
}

/* ── 목차 ── */
.toc {
    page-break-after: always;
}

.toc h2 {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 18pt;
    color: #1a1a1a;
    border-bottom: 1pt solid #ddd;
    padding-bottom: 8pt;
    margin-bottom: 16pt;
}

.toc .toc-part {
    font-family: "Noto Sans KR", sans-serif;
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
    page-break-before: always;
    page-break-after: always;
    text-align: center;
    padding-top: 80mm;
    min-height: 100vh;
}

.part-title .part-num {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 13pt;
    color: #8B0000;
    letter-spacing: 2pt;
}

.part-title h2 {
    font-family: "Noto Sans KR", sans-serif;
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
    font-family: "Noto Sans KR", sans-serif;
    font-size: 20pt;
    font-weight: 700;
    color: #1a1a1a;
    margin-top: 0;
    margin-bottom: 14pt;
    page-break-before: always;
}

h2 {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 15pt;
    font-weight: 700;
    color: #333;
    margin-top: 28pt;
    margin-bottom: 10pt;
    border-bottom: 0.5pt solid #ddd;
    padding-bottom: 5pt;
}

h3 {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 13pt;
    font-weight: 700;
    color: #444;
    margin-top: 20pt;
    margin-bottom: 8pt;
}

h4 {
    font-family: "Noto Sans KR", sans-serif;
    font-size: 12pt;
    font-weight: 700;
    color: #555;
    margin-top: 14pt;
    margin-bottom: 6pt;
}

/* ── 본문 ── */
p {
    margin-top: 0;
    margin-bottom: 10pt;
}

strong {
    font-weight: 700;
    color: #1a1a1a;
}

/* ── 인용구 ── */
blockquote {
    margin: 16pt 0;
    padding: 12pt 16pt;
    border-left: 3pt solid #8B0000;
    background: #f9f6f1;
    font-style: italic;
    color: #444;
    font-size: 11.5pt;
    line-height: 1.7;
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
    margin: 10pt 0;
    padding-left: 20pt;
}

li {
    margin-bottom: 5pt;
    font-size: 11.5pt;
    line-height: 1.7;
}

/* ── 테이블 ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 14pt 0;
    font-size: 10.5pt;
    line-height: 1.5;
    page-break-inside: avoid;
}

thead th {
    background: #2C3E50;
    color: white;
    font-family: "Noto Sans KR", sans-serif;
    font-weight: 700;
    padding: 7pt 8pt;
    text-align: center;
    border: 0.5pt solid #2C3E50;
}

tbody td {
    padding: 6pt 8pt;
    border: 0.5pt solid #ddd;
    text-align: center;
    color: #333;
}

tbody tr:nth-child(even) {
    background: #f8f9fa;
}

/* ── 차트/이미지 ── */
figure.chart-figure {
    margin: 18pt 0;
    text-align: center;
    page-break-inside: avoid;
}

figure.chart-figure img {
    max-width: 85%;
    height: auto;
    max-height: 200px;
}

figure.chart-figure figcaption {
    font-family: "Noto Sans KR", sans-serif;
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
    margin: 18pt auto;
}

hr {
    border: none;
    border-top: 0.5pt solid #ccc;
    width: 25mm;
    margin: 18pt auto;
}

/* ── 참고 문헌 ── */
.references {
    margin-top: 24pt;
    padding-top: 12pt;
    border-top: 0.5pt solid #ddd;
}

.references h4 {
    font-family: "Noto Sans KR", sans-serif;
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
    line-height: 1.5;
    margin-bottom: 4pt;
    text-indent: -12pt;
    padding-left: 12pt;
}

img {
    max-width: 100%;
    height: auto;
}

/* ── 인쇄 안내 바 ── */
.print-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: #2C3E50;
    color: white;
    padding: 10px 20px;
    font-family: "Noto Sans KR", sans-serif;
    font-size: 14px;
    text-align: center;
    z-index: 9999;
}

.print-bar button {
    background: #8B0000;
    color: white;
    border: none;
    padding: 8px 24px;
    font-size: 14px;
    cursor: pointer;
    border-radius: 4px;
    margin-left: 16px;
}

.print-bar button:hover {
    background: #a00;
}

/* 제작자 표시 */
.credits {
    text-align: center;
    margin-top: 40pt;
    padding-top: 20pt;
    border-top: 0.5pt solid #ddd;
    font-family: "Noto Sans KR", sans-serif;
    font-size: 10pt;
    color: #999;
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
    <div class="author">혜통</div>
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
    <div class="toc-chapter">2장. 인간의 본래 식단, 지방으로 살아온 역사</div>
    <div class="toc-part">제2부 &mdash; 잃어버린 균형: 식물 문명이 만든 병든 인류</div>
    <div class="toc-chapter">1장. 과학의 탈을 쓴 조작</div>
    <div class="toc-chapter">2장. 콜레스테롤의 진실</div>
    <div class="toc-chapter">3장. 식물식이 만든 인체 파괴</div>
    <div class="toc-part">제3부 &mdash; 회복의 시작: 본래의 식단으로 돌아가다</div>
    <div class="toc-chapter">1장. 왜 육식인가</div>
    <div class="toc-chapter">2장. 카니보어의 과학적 근거</div>
    <div class="toc-chapter">3장. 식물식이 만든 오해와 왜곡된 상식</div>
    <div class="toc-part">제4부 &mdash; 잘못된 믿음과 진실의 회복</div>
    <div class="toc-chapter">1장. 과학의 이름으로 포장된 거짓</div>
    <div class="toc-chapter">2장. 한국의 현실과 세계의 전환</div>
    <div class="toc-chapter">3장. 윤리와 믿음의 함정</div>
    <div class="toc-part">제5부 &mdash; 실천 가이드: 카니보어 시작하기</div>
    <div class="toc-chapter">1장. 카니보어 식단의 단계별 시작법</div>
    <div class="toc-chapter">2장. 식재료 선택과 품질</div>
    <div class="toc-chapter">3장. 치유 식단 비교 &amp; 조리법</div>
    <div class="toc-part">제6부 &mdash; 자주 묻는 질문과 사례</div>
    <div class="toc-chapter">1장. Q&amp;A</div>
    <div class="toc-chapter">2장. 회복 사례 모음</div>
    <div class="toc-part">에필로그 &mdash; 식탁 위의 혁명</div>
    <div class="toc-part">부록</div>
</div>
'''

    # 챕터 순서
    chapters = [
        ("chapters_compact/preface.md", None),
        (None, ("제1부", "우리는 왜 아플까?")),
        ("chapters_compact/part1-chapter01.md", None),
        ("chapters_compact/part1-chapter02.md", None),
        (None, ("제2부", "잃어버린 균형 — 식물 문명이 만든 병든 인류")),
        ("chapters_compact/chapter-02.md", None),
        (None, ("제3부", "회복의 시작 — 본래의 식단으로 돌아가다")),
        ("chapters_compact/chapter-03.md", None),
        (None, ("제4부", "잘못된 믿음과 진실의 회복")),
        ("chapters_compact/chapter-04.md", None),
        (None, ("제5부", "실천 가이드 — 카니보어 시작하기")),
        ("chapters_compact/chapter-05.md", None),
        (None, ("제6부", "자주 묻는 질문과 사례")),
        ("chapters_compact/chapter-06.md", None),
        ("chapters_compact/epilogue.md", None),
        ("chapters_compact/appendix.md", None),
    ]

    body_html = ""

    for filepath, part_info in chapters:
        if part_info:
            part_num, part_title = part_info
            body_html += f'''
<div class="part-title">
    <div class="part-num">{part_num}</div>
    <h2>{part_title}</h2>
    <div class="part-divider"></div>
</div>
'''
        else:
            full_path = os.path.join(BASE_DIR, filepath)
            if not os.path.exists(full_path):
                print(f"  경고: 파일 없음 - {filepath}")
                continue

            print(f"  처리: {filepath}")
            with open(full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # 중복 부 제목 제거
            md_content = re.sub(r'^# 제\d부\s*[—\-].*$', '', md_content, flags=re.MULTILINE)

            # 전처리 + 변환
            md_content = preprocess_markdown(md_content, filepath)
            html = markdown.markdown(
                md_content,
                extensions=['tables', 'fenced_code', 'attr_list']
            )
            body_html += html + "\n"

    # 차트 삽입
    print("  차트 이미지 삽입...")
    body_html = insert_charts_in_html(body_html)

    # 제작자 표시
    credits_html = '<div class="credits">제작: 혜통</div>'

    # 전체 HTML
    full_html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>카니보어 — 인간 본래의 식단으로 돌아가다</title>
    <style>
{BOOK_CSS}
    </style>
</head>
<body>
<div class="print-bar no-print">
    카니보어 — 인간 본래의 식단으로 돌아가다
    <button onclick="window.print()">인쇄 / PDF 저장</button>
</div>
<div style="margin-top: 50px;">
{cover_html}
{toc_html}
{body_html}
{credits_html}
</div>
</body>
</html>'''

    return full_html


def main():
    print("카니보어 인쇄용 HTML 생성 시작...")
    print()

    html_content = build_book_html()

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    file_size = os.path.getsize(OUTPUT_HTML) / 1024
    print(f"\n완료: {OUTPUT_HTML}")
    print(f"크기: {file_size:.0f}KB")
    print(f"\n브라우저에서 열고 상단 [인쇄 / PDF 저장] 버튼을 클릭하세요.")


if __name__ == "__main__":
    main()
