#!/usr/bin/env python3
"""
카니보어 책 원고 → LaTeX → PDF 생성 (XeLaTeX + 한글 폰트)
신국판(152×225mm) 출판 레이아웃
"""

import re
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
OUTPUT_TEX = os.path.join(BASE_DIR, "carnivore_book.tex")
OUTPUT_PDF = os.path.join(BASE_DIR, "carnivore_book.pdf")

# XeLaTeX 경로
XELATEX = r"C:\Users\corea\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"


# ── 마크다운 → LaTeX 변환 ──────────────────────────

def md_to_latex(text):
    """마크다운을 LaTeX로 변환"""
    # 멀티라인 bold 전처리: 문단 내에서만 줄바꿈 합치기 (빈 줄 경계 넘지 않음)
    def _merge_bold(m):
        content = m.group(1)
        # 빈 줄(\n\n)이 포함되면 매칭 무효 — 문단 경계를 넘는 bold는 처리하지 않음
        if '\n\n' in content:
            return m.group(0)
        # > 접두사 제거, 줄바꿈→공백
        content = re.sub(r'\n>\s*', ' ', content)
        content = content.replace('\n', ' ')
        return f'**{content}**'

    for _ in range(10):
        prev = text
        text = re.sub(r'\*\*(.{1,500}?)\*\*', _merge_bold, text, flags=re.DOTALL)
        if text == prev:
            break

    lines = text.split('\n')
    result = []
    in_table = False
    in_blockquote = False
    in_list = False
    table_rows = []
    bq_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # 빈 줄
        if not stripped:
            if in_blockquote:
                result.append(_flush_blockquote(bq_lines))
                bq_lines = []
                in_blockquote = False
            if in_list:
                result.append('\\end{itemize}\n')
                in_list = False
            if in_table:
                result.append(_flush_table(table_rows, table_aligns))
                table_rows = []
                table_aligns = []
                in_table = False
            result.append('')
            continue

        # 구분선
        if stripped == '---':
            if in_blockquote:
                result.append(_flush_blockquote(bq_lines))
                bq_lines = []
                in_blockquote = False
            result.append('\\vspace{12pt}\n')
            continue

        # 테이블
        if '|' in stripped and stripped.startswith('|'):
            # 구분줄에서 정렬 정보 파싱 (|:---:|---| 등)
            if re.match(r'^\|[\s\-:]+\|', stripped):
                if not in_table:
                    continue
                # 정렬 정보 추출
                align_cells = [c.strip() for c in stripped.split('|')[1:-1]]
                table_aligns = []
                for ac in align_cells:
                    if ac.startswith(':') and ac.endswith(':'):
                        table_aligns.append('c')
                    elif ac.endswith(':'):
                        table_aligns.append('r')
                    else:
                        table_aligns.append('l')
                continue
            cols = [c.strip() for c in stripped.split('|')[1:-1]]
            if not in_table:
                in_table = True
                table_rows = []
                table_aligns = []
            table_rows.append(cols)
            continue
        elif in_table:
            result.append(_flush_table(table_rows, table_aligns))
            table_rows = []
            table_aligns = []
            in_table = False

        # 인용구
        if stripped.startswith('>'):
            content = stripped.lstrip('>').strip()
            bq_lines.append(content)
            in_blockquote = True
            continue
        elif in_blockquote:
            result.append(_flush_blockquote(bq_lines))
            bq_lines = []
            in_blockquote = False

        # 리스트
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                result.append('\\begin{itemize}[leftmargin=*, nosep]')
                in_list = True
            item_text = _inline(stripped[2:])
            result.append(f'  \\item {item_text}')
            continue
        # 숫자 리스트
        if re.match(r'^\d+\.\s', stripped):
            if not in_list:
                result.append('\\begin{itemize}[leftmargin=*, nosep]')
                in_list = True
            item_text = _inline(re.sub(r'^\d+\.\s', '', stripped))
            result.append(f'  \\item {item_text}')
            continue
        elif in_list:
            result.append('\\end{itemize}\n')
            in_list = False

        # 제목
        if stripped.startswith('#'):
            if in_list:
                result.append('\\end{itemize}\n')
                in_list = False
            result.append(_heading(stripped))
            continue

        # 일반 문단
        result.append(_inline(stripped))

    # 남은 것 처리
    if in_blockquote:
        result.append(_flush_blockquote(bq_lines))
    if in_list:
        result.append('\\end{itemize}\n')
    if in_table:
        result.append(_flush_table(table_rows, table_aligns))

    return '\n'.join(result)


def _heading(line):
    """마크다운 제목 → LaTeX 제목"""
    match = re.match(r'^(#{1,4})\s+(.*)', line)
    if not match:
        return _inline(line)
    level = len(match.group(1))
    title = _inline(match.group(2))

    # 부 제목 (제N부) → build_part_page에서 이미 처리하므로 스킵
    if re.match(r'제\d부', title):
        return ''

    if level == 1:
        # 장 제목
        return f'\\newpage\n\\section*{{{title}}}\n\\addcontentsline{{toc}}{{section}}{{{title}}}\n\\markboth{{{title}}}{{{title}}}'
    elif level == 2:
        return f'\\subsection*{{{title}}}'
    elif level == 3:
        return f'\\subsubsection*{{{title}}}'
    else:
        return f'\\paragraph{{{title}}}'


def _inline(text):
    """인라인 마크다운 → LaTeX"""
    # 1단계: 마크다운 인라인 변환 (이스케이프 전에 처리)
    # **bold** → 플레이스홀더
    text = re.sub(r'\*\*(.+?)\*\*', r'<<<BOLD>>>\1<<<ENDBOLD>>>', text)
    # *italic* → 플레이스홀더
    text = re.sub(r'\*(.+?)\*', r'<<<ITALIC>>>\1<<<ENDITALIC>>>', text)
    # 링크 제거 (텍스트만 남김)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # 2단계: LaTeX 특수문자 이스케이프
    text = text.replace('\\', '\\textbackslash{}')
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('$', '\\$')
    text = text.replace('#', '\\#')
    text = text.replace('_', '\\_')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    text = text.replace('~', '\\textasciitilde{}')
    text = text.replace('^', '\\textasciicircum{}')

    # 3단계: 플레이스홀더 → LaTeX 명령 복원
    text = text.replace('<<<BOLD>>>', '\\textbf{')
    text = text.replace('<<<ENDBOLD>>>', '}')
    text = text.replace('<<<ITALIC>>>', '\\textit{')
    text = text.replace('<<<ENDITALIC>>>', '}')

    return text


def _flush_blockquote(lines):
    """인용구 처리"""
    # 모든 줄을 합쳐서 하나의 텍스트로
    merged = ' '.join([l for l in lines if l])
    # _inline으로 변환 (한 줄이므로 bold/italic 정상 처리)
    content = _inline(merged)
    return f'\\begin{{quotebox}}\n{content}\n\\end{{quotebox}}\n'


def _text_width(text):
    """텍스트의 시각적 너비 (한글=2, 영문=1)"""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in text)


def _has_url(text):
    """URL 포함 여부"""
    return 'http://' in text or 'https://' in text or 'www.' in text


def _flush_table(rows, aligns=None):
    """테이블 처리 — 자동 전치 + 내용 비례 열 너비 + 중앙 정렬 + 긴 테이블 페이지 넘김"""
    if not rows:
        return ''

    ncols = max(len(r) for r in rows)
    ndata = len(rows) - 1  # 헤더 제외 데이터 행 수

    # ── 자동 전치: 2열 + 4행 이상 + 모든 셀 15자 이하 ──
    if ncols == 2 and ndata >= 4:
        all_short = all(
            _text_width(cell) <= 15
            for row in rows
            for cell in row[:2]
        )
        if all_short:
            # 전치: 헤더 행의 각 셀이 새로운 열의 헤더가 됨
            # rows[0] = [헤더1, 헤더2], rows[1:] = 데이터
            header = rows[0]
            data = rows[1:]
            new_rows = []
            # 첫 행: 데이터의 첫 번째 열 값들
            new_rows.append([header[0]] + [r[0] if len(r) > 0 else '' for r in data])
            # 둘째 행: 데이터의 두 번째 열 값들
            new_rows.append([header[1]] + [r[1] if len(r) > 1 else '' for r in data])
            rows = new_rows
            ncols = max(len(r) for r in rows)
            ndata = len(rows) - 1
            aligns = ['c'] * ncols

    # 정렬 정보 (기본: 중앙 정렬)
    if not aligns or len(aligns) < ncols:
        aligns = ['c'] * ncols

    # 모든 열을 강제 가운데 정렬 (사용자 요청: 전체 표 가운데 정렬 기본)
    aligns = ['c'] * ncols

    # 부족한 컬럼 채우기
    for row in rows:
        while len(row) < ncols:
            row.append('')

    # ── 열 너비 계산: 내용 비례 + 헤더 한 줄 보장 ──
    col_max_len = [0] * ncols
    header_len = [0] * ncols  # 헤더 텍스트 너비 (한 줄 보장용)
    has_url_col = [False] * ncols
    for ri, row in enumerate(rows):
        for ci in range(ncols):
            text = row[ci]
            w = _text_width(text)
            col_max_len[ci] = max(col_max_len[ci], w)
            if ri == 0:
                header_len[ci] = w
            if _has_url(text):
                has_url_col[ci] = True

    # URL 열은 넓게
    for ci in range(ncols):
        if has_url_col[ci]:
            col_max_len[ci] = max(col_max_len[ci], 50)
        # 최소 너비: 헤더 텍스트가 한 줄에 들어가도록 보장 (최소 8자 확보)
        col_max_len[ci] = max(col_max_len[ci], header_len[ci], 8)

    total = sum(col_max_len)
    # 셀 패딩(\tabcolsep=2pt × 2 × ncols) + 테두리
    # 텍스트 영역 약 114mm ≈ 323pt
    padding_frac = (ncols * 4.0 + (ncols + 1) * 0.4) / 323.0
    max_total = 1.0 - padding_frac - 0.02
    total_frac = min(0.90, max_total)
    col_widths = [total_frac * w / total for w in col_max_len]

    # 총합이 max_total을 넘으면 비례 축소 (절대 넘침 방지)
    width_sum = sum(col_widths)
    if width_sum > max_total:
        scale = max_total / width_sum
        col_widths = [w * scale for w in col_widths]

    # 정렬 적용 (모든 열에 명시적 정렬 — p{} 기본 justify로 한글 글자 벌어짐 방지)
    align_prefix = {
        'c': '>{{\\centering\\arraybackslash}}',
        'r': '>{{\\raggedleft\\arraybackslash}}',
        'l': '>{{\\raggedright\\arraybackslash}}',
    }
    col_specs = []
    for i, w in enumerate(col_widths):
        a = aligns[i] if i < len(aligns) else 'c'
        prefix = align_prefix.get(a, '')
        col_specs.append(f'{prefix}p{{{w:.3f}\\textwidth}}')
    col_spec = '|' + '|'.join(col_specs) + '|'

    # URL 셀은 \url{}로 감싸기
    processed_rows = []
    for row in rows:
        processed = []
        for ci, cell in enumerate(row):
            if has_url_col[ci] and _has_url(cell):
                # URL을 \url{}로 감싸기 (줄바꿈 허용)
                url = cell.strip()
                processed.append(f'\\url{{{url}}}')
            else:
                processed.append(_inline(cell))
        processed_rows.append(processed)

    # ── 헤더 행: 볼드 + 강제 중앙 정렬 (열 정렬과 무관하게) ──
    header_cells = ' & '.join([f'\\multicolumn{{1}}{{|c|}}{{\\textbf{{{c}}}}}' for c in processed_rows[0]])
    # 첫 열의 | 중복 방지
    header_cells_list = []
    for ci, c in enumerate(processed_rows[0]):
        if ci == 0:
            header_cells_list.append(f'\\multicolumn{{1}}{{|c|}}{{\\textbf{{{c}}}}}')
        else:
            header_cells_list.append(f'\\multicolumn{{1}}{{c|}}{{\\textbf{{{c}}}}}')
    header_cells = ' & '.join(header_cells_list)

    # 폰트 크기: 5열 이상이면 footnotesize
    font_cmd = '\\footnotesize' if ncols >= 5 else '\\small'

    # ── 긴 테이블(5행 이상): longtable로 페이지 넘김 지원 ──
    use_longtable = ndata >= 5

    # 행 높이 배율 (셀 패딩 확보)
    stretch_cmd = '\\renewcommand{\\arraystretch}{1.35}'

    lines = []
    if use_longtable:
        lines.append('\\vspace{12pt}')
        lines.append(f'{{\\setlength{{\\tabcolsep}}{{3pt}}{font_cmd}')
        lines.append(stretch_cmd)
        lines.append(f'\\begin{{longtable}}{{{col_spec}}}')
        lines.append('\\hline')
        lines.append(f'{header_cells} \\\\')
        lines.append('\\hline')
        lines.append('\\endfirsthead')
        lines.append('\\hline')
        lines.append(f'{header_cells} \\\\')
        lines.append('\\hline')
        lines.append('\\endhead')
        lines.append('\\hline')
        lines.append('\\endfoot')
        for row in processed_rows[1:]:
            cells = ' & '.join(row)
            lines.append(f'{cells} \\\\')
            lines.append('\\hline')
        lines.append('\\end{longtable}')
        lines.append('}\n\\vspace{12pt}')
    else:
        # 짧은 테이블: 최소 공간 확보 (테이블이 다음 페이지로 밀리는 것 방지)
        est_lines = ndata + 2  # 헤더 + 데이터 + 여유
        lines.append(f'\\needspace{{{est_lines}\\baselineskip}}')
        lines.append('\\vspace{12pt}')
        lines.append('{\\centering')
        lines.append(f'\\setlength{{\\tabcolsep}}{{3pt}}')
        lines.append(stretch_cmd)
        lines.append(font_cmd)
        lines.append(f'\\begin{{tabular}}{{{col_spec}}}')
        lines.append('\\hline')
        lines.append(f'{header_cells} \\\\')
        lines.append('\\hline')
        for row in processed_rows[1:]:
            cells = ' & '.join(row)
            lines.append(f'{cells} \\\\')
            lines.append('\\hline')
        lines.append('\\end{tabular}')
        lines.append('\\par}')
        lines.append('\\vspace{8pt}\n')

    return '\n'.join(lines)


# ── LaTeX 문서 템플릿 ──────────────────────────────

LATEX_PREAMBLE = r"""
\documentclass[11pt, openany]{book}

% ── 판형: 신국판 (152×225mm) ──
\usepackage[
  paperwidth=152mm,
  paperheight=225mm,
  top=20mm,
  bottom=22mm,
  left=20mm,
  right=18mm,
  headheight=14pt
]{geometry}

% ── 한글 폰트 (XeLaTeX) ──
\usepackage{fontspec}
\usepackage{kotex}

\setmainfont{NotoSerifKR-VF.ttf}[
  Path=C:/Windows/Fonts/,
  Script=Hangul,
  BoldFeatures={RawFeature={wght=700}}
]
\setsansfont{NotoSansKR-VF.ttf}[
  Path=C:/Windows/Fonts/,
  Script=Hangul,
  BoldFeatures={RawFeature={wght=700}}
]

% ── 패키지 ──
\usepackage{graphicx}
\usepackage{float}
\usepackage{caption}
\usepackage{array}
\usepackage{longtable}
\usepackage{enumitem}
\usepackage{booktabs}
\usepackage{needspace}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{tocloft}
\usepackage[hyphens]{url}
\usepackage{hyperref}
\usepackage{tcolorbox}

% ── 색상 ──
\definecolor{darkred}{RGB}{139, 0, 0}
\definecolor{darkgray}{RGB}{68, 68, 68}
\definecolor{lightbg}{RGB}{249, 246, 241}

% ── 인용구 박스 ──
\newtcolorbox{quotebox}{
  colback=lightbg,
  colframe=darkred,
  boxrule=0pt,
  leftrule=3pt,
  arc=0pt,
  outer arc=0pt,
  left=12pt,
  right=12pt,
  top=8pt,
  bottom=8pt,
  fontupper=\small\itshape\color{darkgray}
}

% ── 제목 스타일 ──
\titleformat{\section}[display]
  {\sffamily\bfseries\Large}
  {}
  {0pt}
  {}
\titlespacing*{\section}{0pt}{0pt}{14pt}

\titleformat{\subsection}
  {\sffamily\bfseries\large\color{darkred}}
  {}
  {0pt}
  {}
\titlespacing*{\subsection}{0pt}{20pt}{8pt}

\titleformat{\subsubsection}
  {\sffamily\bfseries\normalsize\color{black}}
  {}
  {0pt}
  {}
\titlespacing*{\subsubsection}{0pt}{14pt}{6pt}

% ── 머리말/꼬리말 ──
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE]{\small\sffamily\leftmark}
\fancyhead[RO]{\small\sffamily\rightmark}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% ── 본문 스타일 ──
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\linespread{1.75}
\raggedbottom  % 페이지 하단 여백 자연스럽게 (테이블 밀림 시 빈 공간 최소화)

% ── 하이퍼링크 ──
\hypersetup{
  colorlinks=true,
  linkcolor=darkred,
  urlcolor=darkred,
  pdftitle={카니보어 — 인간 본래의 식단으로 돌아가다},
  pdfauthor={혜통}
}
\urlstyle{same}
\Urlmuskip=0mu plus 1mu

\begin{document}

% ══════════════════════════════════════════════════════
% 표지
% ══════════════════════════════════════════════════════
\begin{titlepage}
\centering
\vspace*{60mm}
{\sffamily\fontsize{36pt}{40pt}\selectfont\bfseries 카니보어}\\[12pt]
{\large 인간 본래의 식단으로 돌아가다}\\[25pt]
{\color{darkred}\rule{40mm}{0.5pt}}\\[20pt]
{\sffamily\large 혜통}\\[10pt]
{\sffamily\normalsize\color{gray} 2026}
\vfill
\end{titlepage}

% ══════════════════════════════════════════════════════
% 목차
% ══════════════════════════════════════════════════════
\frontmatter
\tableofcontents
\mainmatter

"""

LATEX_ENDING = r"""

% ══════════════════════════════════════════════════════
% 제작자 표시
% ══════════════════════════════════════════════════════
\vfill
\begin{center}
\small\sffamily\color{gray}
제작: 혜통
\end{center}

\end{document}
"""


def insert_charts_latex(latex_content):
    """LaTeX 본문에 차트 이미지를 삽입"""
    chart_dir = os.path.join(BASE_DIR, "_charts")
    insertions = [
        {
            'after_text': '소비자가 마트에서 만나는 투명하고',
            'chart': 'seed_oil_process.png',
            'caption': '식물성 기름 6단계 정제 공정'
        },
        {
            'after_text': '인슐린이 높은 동안',
            'chart': 'insulin_cycle.png',
            'caption': '인슐린 저항성 악순환 (탄수화물 과잉 섭취의 대사 경로)'
        },
        {
            'after_text': '동맥경화의 근본 경로다',
            'chart': 'atherosclerosis_mechanism.png',
            'caption': '동맥경화의 실제 기전 — 염증 모델'
        },
        {
            'after_text': '제약 시장은 확대되지만',
            'chart': 'threshold_patients.png',
            'caption': '진단 기준치 하향에 따른 환자 수 변화 (미국)'
        },
        {
            'after_text': '지방 적응은 평소는 투자 수익으로',
            'chart': 'energy_systems.png',
            'caption': '탄수화물 vs 지방 에너지 시스템 비교'
        },
        {
            'after_text': '케톤 대사의 항염',
            'chart': 'ketone_pathway.png',
            'caption': '케톤체(BHB)의 다중 생리적 효과'
        },
    ]

    used = set()
    for item in insertions:
        chart_path = os.path.join(chart_dir, item['chart'])
        if not os.path.exists(chart_path) or item['chart'] in used:
            continue
        # Windows 경로를 LaTeX 호환으로
        rel_path = os.path.relpath(chart_path, BASE_DIR).replace('\\', '/')
        pos = latex_content.find(item['after_text'])
        if pos >= 0:
            # 다음 줄바꿈 찾기
            nl = latex_content.find('\n', pos)
            if nl >= 0:
                figure_tex = f"""

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\textwidth]{{{rel_path}}}
\\end{{figure}}
"""
                latex_content = latex_content[:nl] + figure_tex + latex_content[nl:]
                used.add(item['chart'])
                print(f"    삽입: {item['chart']}")

    return latex_content


def build_part_page(part_num, part_title):
    """부(Part) 타이틀 — 목차 등록 + 본문 헤더"""
    return f"""
\\newpage
\\addcontentsline{{toc}}{{part}}{{{part_num} {_inline(part_title)}}}
\\vspace*{{5mm}}
\\begin{{center}}
{{\\sffamily\\small\\color{{darkred}}\\MakeUppercase{{{part_num}}}}}\\\\[6pt]
{{\\sffamily\\Large\\bfseries {_inline(part_title)}}}
\\end{{center}}
\\vspace{{8mm}}
"""


def main():
    print("카니보어 출판용 LaTeX/PDF 생성 시작...")
    print()

    # 챕터 순서
    chapters = [
        ("chapters/preface.md", None),
        (None, ("제1부", "우리는 왜 아플까?")),
        ("chapters/part1-overview.md", None),
        ("chapters/part1-chapter01.md", None),
        ("chapters/part1-chapter02.md", None),
        ("chapters/part1-chapter03a.md", None),
        ("chapters/part1-chapter03b.md", None),
        ("chapters/part1-chapter03c.md", None),
        (None, ("제2부", "회복의 시작 — 본래의 식단으로 돌아가다")),
        ("chapters/part2-intro.md", None),
        ("chapters/part2-chapter01.md", None),
        ("chapters/part2-chapter02.md", None),
        ("chapters/part2-chapter03.md", None),
        (None, ("제3부", "잃어버린 균형 — 식물 문명이 만든 병든 인류")),
        ("chapters/part3-intro.md", None),
        ("chapters/part3-chapter01.md", None),
        ("chapters/part3-chapter02a.md", None),
        ("chapters/part3-chapter02b.md", None),
        ("chapters/part3-chapter02c.md", None),
        (None, ("제4부", "잘못된 믿음과 진실의 회복")),
        ("chapters/part4-intro.md", None),
        ("chapters/part4-chapter01.md", None),
        ("chapters/part4-chapter02.md", None),
        ("chapters/part4-chapter03.md", None),
        (None, ("제5부", "실천 가이드 — 카니보어 시작하기")),
        ("chapters/part5-intro.md", None),
        ("chapters/part5-chapter01.md", None),
        ("chapters/part5-chapter02.md", None),
        ("chapters/part5-chapter03.md", None),
        ("chapters/part5-chapter04.md", None),
        ("chapters/part5-chapter05.md", None),
        (None, ("제6부", "자주 묻는 질문과 사례")),
        ("chapters/part6-intro.md", None),
        ("chapters/part6-chapter01.md", None),
        ("chapters/part6-chapter02a.md", None),
        ("chapters/part6-chapter02b.md", None),
        ("chapters/part6-chapter03.md", None),
        ("chapters/epilogue.md", None),
        ("chapters/appendix-a.md", None),
        ("chapters/appendix-b.md", None),
        ("chapters/appendix-c.md", None),
    ]

    body_latex = ""

    for filepath, part_info in chapters:
        if part_info:
            part_num, part_title = part_info
            body_latex += build_part_page(part_num, part_title)
        else:
            full_path = os.path.join(BASE_DIR, filepath)
            if not os.path.exists(full_path):
                print(f"  경고: 파일 없음 - {filepath}")
                continue

            print(f"  처리: {filepath}")
            with open(full_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # 중복 부 제목 제거 (# 제N부 / # 제N부. 형태 모두)
            md_content = re.sub(r'^# 제\d부\.?\s*.*$', '', md_content, flags=re.MULTILINE)

            # 마크다운 → LaTeX 변환
            latex_content = md_to_latex(md_content)
            body_latex += latex_content + "\n"

    # 차트 이미지 삽입
    print("  차트 이미지 삽입...")
    body_latex = insert_charts_latex(body_latex)

    # 최종 ** 잔존 정리 (멀티라인 bold가 변환기를 빠져나간 경우)
    def _bold_replace(m):
        content = m.group(1).replace('\n', ' ')
        # LaTeX 환경 경계를 넘어가는 경우는 치환하지 않음
        if '\\begin{' in content or '\\end{' in content:
            return m.group(0)  # 원본 유지
        return f'\\textbf{{{content}}}'

    for _ in range(10):
        prev = body_latex
        body_latex = re.sub(r'\*\*(.{1,500}?)\*\*', _bold_replace, body_latex, flags=re.DOTALL)
        if body_latex == prev:
            break

    # 전체 LaTeX 문서
    full_latex = LATEX_PREAMBLE + body_latex + LATEX_ENDING

    # .tex 파일 저장
    with open(OUTPUT_TEX, 'w', encoding='utf-8') as f:
        f.write(full_latex)

    tex_size = os.path.getsize(OUTPUT_TEX) / 1024
    print(f"\n  .tex 생성 완료: {OUTPUT_TEX} ({tex_size:.0f}KB)")

    # XeLaTeX 실행 (2회 — 목차 생성을 위해)
    print("\n  XeLaTeX 컴파일 중 (1/2)...")
    for run in range(1, 3):
        print(f"  XeLaTeX 실행 {run}/2...")
        result = subprocess.run(
            [XELATEX, '-interaction=nonstopmode', '-output-directory', BASE_DIR, OUTPUT_TEX],
            cwd=BASE_DIR,
            capture_output=True,
            timeout=300,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode != 0:
            # 에러 추출
            err_lines = [l for l in result.stdout.split('\n') if l.startswith('!') or 'Error' in l]
            if err_lines:
                print(f"\n  XeLaTeX 에러:")
                for l in err_lines[:10]:
                    print(f"    {l}")
            else:
                # 로그 마지막 30줄
                log_lines = result.stdout.strip().split('\n')
                print(f"\n  XeLaTeX 로그 (마지막 15줄):")
                for l in log_lines[-15:]:
                    print(f"    {l}")

            if run == 1:
                print("\n  첫 번째 실행 에러 - 패키지 자동 설치 후 재시도...")
                continue
            else:
                print("\n  PDF 생성 실패. .tex 파일은 생성되었으므로 수동 컴파일 가능.")
                print(f"  명령어: xelatex \"{OUTPUT_TEX}\"")
                return

    if os.path.exists(OUTPUT_PDF):
        pdf_size = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
        print(f"\n완료: {OUTPUT_PDF} ({pdf_size:.1f}MB)")
    else:
        print("\n  PDF 파일이 생성되지 않았습니다. .tex 파일을 확인해주세요.")

    # 임시 파일 정리
    for ext in ['.aux', '.log', '.toc', '.out']:
        tmp = OUTPUT_TEX.replace('.tex', ext)
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    main()
