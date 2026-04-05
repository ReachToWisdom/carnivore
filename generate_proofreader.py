#!/usr/bin/env python3
"""
카니보어 원고 탈고 리더 생성기
마크다운 원고 → HTML 이북 리더 (코멘트 + 수정 상태 추적)
GitHub Pages 배포용 docs/index.html 출력
"""

import re
import os
import html
import markdown

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
OUTPUT_HTML = os.path.join(DOCS_DIR, "index.html")

# 빌드 순서 (generate_book_latex.py와 동일)
CHAPTERS = [
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


def add_paragraph_ids(html_content, file_id):
    """HTML 블록 요소에 고유 ID 부여 (내용 해시 기반 — 줄 이동에 안정적)"""
    import hashlib
    counter = [0]
    tags = r'(<(?:p|h[1-6]|li|blockquote|tr|pre))([ >])(.*?)(?=<(?:p|h[1-6]|li|blockquote|tr|pre|/(?:ul|ol|table|blockquote|section|div))[ >]|$)'

    # 간단한 접근: 순차 번호 유지하되, 내용 해시도 data-hash에 저장
    # 코멘트 리매핑 시 해시로 매칭
    counter2 = [0]
    tags2 = r'(<(?:p|h[1-6]|li|blockquote|tr|pre))([ >])'

    def replacer(m):
        counter2[0] += 1
        tag_open = m.group(1)
        rest = m.group(2)
        # 태그 뒤의 텍스트에서 해시 생성 (완벽하지 않지만 리매핑에 충분)
        pid = f"{file_id}-{counter2[0]}"
        return f'{tag_open} id="{pid}" data-file="{file_id}" data-line="{counter2[0]}"{rest}'

    return re.sub(tags2, replacer, html_content)


def remap_comments():
    """재빌드 후 코멘트 targetId를 새 HTML에 맞게 리매핑"""
    import json
    from difflib import SequenceMatcher

    comments_path = os.path.join(DOCS_DIR, '..', 'comments_latest.json')
    # GitHub에서 다운로드된 최신 파일 시도
    if not os.path.exists(comments_path):
        return

    with open(comments_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 현재 원고에서 파일별 문단 텍스트 매핑 생성
    paragraph_map = {}  # {file_id: [(line_num, text), ...]}
    for entry in CHAPTERS:
        filepath, part_info = entry
        if filepath is None:
            continue
        full_path = os.path.join(BASE_DIR, filepath)
        if not os.path.exists(full_path):
            continue
        file_id = os.path.basename(filepath).replace('.md', '')
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # 비어있지 않은 줄 수집 (문단 대응)
        paragraphs = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('|') and not stripped.startswith('---'):
                paragraphs.append((i, stripped[:100]))
        paragraph_map[file_id] = paragraphs

    remapped = 0
    for c in data.get('comments', []):
        file_id = c.get('file', '')
        excerpt = c.get('excerpt', '')[:80]
        if not file_id or not excerpt or file_id not in paragraph_map:
            continue

        # excerpt와 가장 유사한 문단 찾기
        best_ratio = 0
        best_line = c.get('line', 1)
        for line_num, text in paragraph_map[file_id]:
            ratio = SequenceMatcher(None, excerpt[:60], text[:60]).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_line = line_num

        if best_ratio > 0.4:
            new_target = f"{file_id}-{best_line}"
            if new_target != c.get('targetId'):
                c['targetId'] = new_target
                c['line'] = best_line
                remapped += 1

    if remapped > 0:
        with open(comments_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  코멘트 리매핑: {remapped}개 targetId 업데이트")


def build_content():
    """모든 챕터를 HTML로 변환"""
    sections = []
    md_ext = markdown.Markdown(extensions=['tables', 'fenced_code'])

    for entry in CHAPTERS:
        filepath, part_info = entry

        if filepath is None and part_info:
            part_num, part_title = part_info
            sections.append(
                f'<div class="part-divider" id="part-{part_num}">'
                f'<h1>{part_num}</h1><p>{part_title}</p></div>'
            )
            continue

        full_path = os.path.join(BASE_DIR, filepath)
        if not os.path.exists(full_path):
            continue

        file_id = os.path.basename(filepath).replace('.md', '')
        with open(full_path, 'r', encoding='utf-8') as f:
            text = f.read()

        md_ext.reset()
        html_content = md_ext.convert(text)
        html_content = add_paragraph_ids(html_content, file_id)

        sections.append(
            f'<section class="chapter" data-file="{file_id}">'
            f'<div class="chapter-label">{filepath}</div>'
            f'{html_content}'
            f'</section>'
        )

    return '\n'.join(sections)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="카니보어 탈고">
<link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📖</text></svg>">
<title>카니보어 탈고 리더</title>
<style>
:root {
  --bg: #fafaf8;
  --text: #1a1a1a;
  --sidebar-bg: #f0f0ed;
  --accent: #c85a2a;
  --comment-bg: #fff8e1;
  --fixed-bg: #e8f5e9;
  --pending-bg: #fff3e0;
  --border: #ddd;
  --highlight: rgba(200, 90, 42, 0.08);
  --highlight-fixed: rgba(76, 175, 80, 0.08);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Noto Serif KR', 'Batang', Georgia, serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.85;
  font-size: 17px;
}

/* 레이아웃 */
.layout {
  display: flex;
  min-height: 100vh;
}
.toc-panel {
  width: 260px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  padding: 20px 16px;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  overflow-y: auto;
  z-index: 100;
  transition: transform 0.3s;
}
.toc-panel h2 { font-size: 15px; margin-bottom: 12px; color: var(--accent); }
.toc-panel ul { list-style: none; }
.toc-panel li { margin: 4px 0; }
.toc-panel a {
  text-decoration: none; color: var(--text); font-size: 13px;
  display: block; padding: 3px 8px; border-radius: 4px;
}
.toc-panel a:hover { background: rgba(0,0,0,0.05); }
.toc-panel a.part { font-weight: bold; color: var(--accent); margin-top: 12px; }

.content-area {
  flex: 1;
  margin-left: 260px;
  margin-right: 0;
  padding: 40px 60px;
  max-width: 800px;
  transition: margin 0.3s;
}
.comment-panel {
  width: 360px;
  background: var(--sidebar-bg);
  border-left: 1px solid var(--border);
  position: fixed;
  top: 0; right: 0; bottom: 0;
  overflow-y: auto;
  padding: 20px 16px;
  z-index: 100;
  transition: transform 0.3s;
}
.comment-panel.open ~ .content-area { margin-right: 360px; }

/* 콘텐츠 스타일 */
.chapter { margin-bottom: 60px; }
.chapter-label {
  font-size: 11px; color: #999; background: #eee;
  display: inline-block; padding: 2px 8px; border-radius: 3px;
  margin-bottom: 16px;
}
.content-area h1 { font-size: 26px; margin: 40px 0 20px; border-bottom: 2px solid var(--accent); padding-bottom: 8px; }
.content-area h2 { font-size: 21px; margin: 32px 0 16px; }
.content-area h3 { font-size: 18px; margin: 24px 0 12px; }
.content-area p { margin: 12px 0; text-align: justify; }
.content-area table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 15px; }
.content-area th, .content-area td { border: 1px solid var(--border); padding: 8px 12px; }
.content-area th { background: var(--sidebar-bg); font-weight: bold; }
.content-area blockquote {
  border-left: 4px solid var(--accent); padding: 12px 20px;
  margin: 16px 0; background: rgba(200,90,42,0.04);
}
.content-area pre {
  background: #2d2d2d; color: #f8f8f2; padding: 16px;
  border-radius: 6px; overflow-x: auto; font-size: 14px;
  margin: 16px 0;
}
.content-area code { font-family: 'Consolas', monospace; }
.content-area ul, .content-area ol { margin: 12px 0; padding-left: 28px; }

/* 문단 호버/클릭 */
.content-area [id] {
  cursor: pointer;
  border-left: 3px solid transparent;
  padding-left: 8px;
  transition: all 0.15s;
  position: relative;
}
.content-area [id]:hover {
  background: rgba(0,0,0,0.02);
  border-left-color: #ccc;
}
.content-area [id].has-comment {
  background: var(--highlight);
  border-left-color: var(--accent);
}
.content-area [id].is-fixed {
  background: var(--highlight-fixed);
  border-left-color: #4caf50;
}
.content-area [id].has-comment::after,
.content-area [id].is-fixed::after {
  content: attr(data-comment-count);
  position: absolute;
  right: -8px; top: 2px;
  background: var(--accent);
  color: white;
  font-size: 11px;
  width: 20px; height: 20px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.content-area [id].is-fixed::after { background: #4caf50; }

/* 파트 구분 */
.part-divider {
  text-align: center;
  padding: 60px 20px;
  margin: 40px 0;
  border-top: 2px solid var(--accent);
  border-bottom: 2px solid var(--accent);
}
.part-divider h1 { font-size: 28px; color: var(--accent); border: none; }
.part-divider p { font-size: 18px; margin-top: 8px; color: #666; }

/* 코멘트 패널 */
.comment-panel h2 { font-size: 15px; margin-bottom: 12px; color: var(--accent); }
.comment-card {
  background: var(--comment-bg);
  border: 1px solid #e0d8b0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  font-size: 14px;
}
.comment-card.review { background: #e3f2fd; border-color: #90caf9; }
.comment-card.approved { background: var(--fixed-bg); border-color: #a5d6a7; }
.comment-card.rejected { background: #fce4ec; border-color: #ef9a9a; opacity: 0.7; }
.comment-card.suggested { background: #fff3e0; border-color: #ffcc80; }
.comment-card .meta {
  font-size: 11px; color: #888; margin-bottom: 6px;
  display: flex; justify-content: space-between; align-items: center;
}
.comment-card .meta a { color: var(--accent); cursor: pointer; text-decoration: underline; }
.comment-card .status-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: bold;
}
.comment-card .status-badge.pending { background: #fff8e1; color: #f57f17; }
.comment-card .status-badge.review { background: #e3f2fd; color: #1565c0; }
.comment-card .status-badge.approved { background: #e8f5e9; color: #2e7d32; }
.comment-card .status-badge.rejected { background: #fce4ec; color: #c62828; }
.comment-card .status-badge.suggested { background: #fff3e0; color: #e65100; }
.comment-card .excerpt {
  font-size: 12px; color: #666; margin-bottom: 8px;
  border-left: 2px solid #ccc; padding-left: 8px;
  max-height: 40px; overflow: hidden;
}
.comment-card .text { margin-bottom: 8px; white-space: pre-wrap; }
.comment-card .diff-box {
  margin: 8px 0; border-radius: 6px; overflow: hidden; font-size: 13px;
}
.comment-card .diff-label {
  display: inline-block; font-size: 11px; font-weight: bold;
  margin-bottom: 4px;
}
.comment-card .diff-original {
  background: #ffebee; padding: 8px 10px; border-left: 3px solid #e53935;
  color: #888; margin-bottom: 2px;
}
.comment-card .diff-original .diff-label { color: #c62828; }
.comment-card .diff-proposed {
  background: #e8f5e9; padding: 8px 10px; border-left: 3px solid #4caf50;
  margin-bottom: 2px;
}
.comment-card .diff-proposed .diff-label { color: #2e7d32; }
.comment-card .diff-suggestion {
  background: #fff3e0; padding: 8px 10px; border-left: 3px solid #ff9800;
}
.comment-card .diff-suggestion .diff-label { color: #e65100; }
.comment-card .actions { display: flex; gap: 6px; flex-wrap: wrap; }
.comment-card .actions button {
  font-size: 12px; padding: 4px 10px; border-radius: 4px;
  border: 1px solid var(--border); background: white; cursor: pointer;
}
.comment-card .actions button.approve-btn { background: #4caf50; color: white; border: none; }
.comment-card .actions button.reject-btn { background: #e53935; color: white; border: none; }
.comment-card .actions button.suggest-btn { background: #ff9800; color: white; border: none; }
.comment-card .actions button.del-btn { color: #e53935; }

/* 코멘트 입력 */
.comment-input-area {
  position: fixed;
  bottom: 0; right: 0;
  width: 360px;
  background: white;
  border-top: 2px solid var(--accent);
  padding: 16px;
  z-index: 200;
  display: none;
}
.comment-input-area.active { display: block; }
.comment-input-area .target-info { font-size: 12px; color: #888; margin-bottom: 6px; }
.comment-input-area .selected-text {
  font-size: 14px; color: var(--text); background: #fff8e1;
  border-left: 3px solid var(--accent); padding: 8px 12px;
  margin-bottom: 10px; border-radius: 4px;
  max-height: 120px; overflow-y: auto; line-height: 1.6;
}
.comment-input-area .selected-text mark {
  background: rgba(200, 90, 42, 0.3); padding: 0 2px; border-radius: 2px; font-weight: bold;
}
.comment-input-area .selected-text:empty { display: none; }
.comment-input-area textarea {
  width: 100%; height: 80px; border: 1px solid var(--border);
  border-radius: 6px; padding: 10px; font-size: 14px;
  font-family: inherit; resize: vertical;
}
.comment-input-area .input-actions { margin-top: 8px; display: flex; gap: 8px; justify-content: flex-end; }
.comment-input-area .input-actions button {
  padding: 8px 20px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px;
}
.comment-input-area .save-btn { background: var(--accent); color: white; }
.comment-input-area .cancel-btn { background: #eee; }

/* 툴바 */
.toolbar {
  position: fixed;
  top: 0; left: 260px; right: 0;
  background: white;
  border-bottom: 1px solid var(--border);
  padding: 8px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 150;
  font-size: 13px;
}
.toolbar button {
  padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border);
  background: white; cursor: pointer; font-size: 13px;
}
.toolbar button:hover { background: #f5f5f5; }
.toolbar button.active { background: var(--accent); color: white; border-color: var(--accent); }
.toolbar .stats { margin-left: auto; color: #888; }
.toolbar .stats span { font-weight: bold; color: var(--accent); }

.content-area { padding-top: 70px; }

/* 모바일 */
@media (max-width: 900px) {
  .toc-panel { transform: translateX(-100%); }
  .toc-panel.open { transform: translateX(0); }
  .content-area { margin-left: 0; padding: 70px 20px 20px; max-width: 100%; }
  .comment-panel { width: 100%; transform: translateX(100%); }
  .comment-panel.open { transform: translateX(0); }
  .comment-input-area { width: 100%; }
  .toolbar { left: 0; }
  .toolbar .menu-btn { display: inline-block !important; }
}
@media (min-width: 901px) {
  .toolbar .menu-btn { display: none; }
}

/* 스크롤바 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }

/* 검색 하이라이트 */
mark { background: #ffeb3b; padding: 0 2px; border-radius: 2px; }

/* 필터 */
.filter-bar { margin-bottom: 12px; display: flex; gap: 6px; }
.filter-bar button {
  font-size: 11px; padding: 4px 8px; border-radius: 4px;
  border: 1px solid var(--border); background: white; cursor: pointer;
}
.filter-bar button.active { background: var(--accent); color: white; border-color: var(--accent); }
</style>
</head>
<body>

<!-- 목차 패널 -->
<nav class="toc-panel" id="tocPanel">
  <h2>📖 목차</h2>
  <ul id="tocList"></ul>
</nav>

<!-- 툴바 -->
<div class="toolbar">
  <button class="menu-btn" onclick="toggleToc()">☰</button>
  <button onclick="toggleComments()" id="commentToggle">💬 코멘트</button>
  <button onclick="exportComments()">📤 내보내기</button>
  <button onclick="importComments()">📥 가져오기</button>
  <input type="file" id="importFile" accept=".json" style="display:none" onchange="handleImport(event)">
  <button onclick="setupToken()">🔑 GitHub</button>
  <span id="syncIndicator" title="동기화 상태">☁️</span>
  <div class="stats">
    코멘트 <span id="statTotal">0</span>개 |
    미수정 <span id="statPending">0</span> |
    완료 <span id="statFixed">0</span>
  </div>
</div>

<!-- 콘텐츠 영역 -->
<main class="content-area" id="contentArea">
{{CONTENT}}
</main>

<!-- 코멘트 패널 -->
<aside class="comment-panel" id="commentPanel">
  <h2>💬 코멘트 목록</h2>
  <div class="filter-bar">
    <button class="active" onclick="filterComments('all', this)">전체</button>
    <button onclick="filterComments('pending', this)">대기</button>
    <button onclick="filterComments('review', this)">검토</button>
    <button onclick="filterComments('approved', this)">승인</button>
    <button onclick="filterComments('rejected', this)">취소</button>
    <button onclick="filterComments('suggested', this)">제안</button>
  </div>
  <div id="commentList"></div>
</aside>

<!-- 코멘트 입력 -->
<div class="comment-input-area" id="commentInput">
  <div class="target-info" id="targetInfo"></div>
  <div class="selected-text" id="selectedText"></div>
  <textarea id="commentText" placeholder="수정 지시 사항을 입력하세요..."></textarea>
  <div class="input-actions">
    <button class="cancel-btn" onclick="cancelComment()">취소</button>
    <button class="save-btn" onclick="saveComment()">저장</button>
  </div>
</div>

<script>
// ── GitHub 설정 ──
const GITHUB_OWNER = 'ReachToWisdom';
const GITHUB_REPO = 'carnivore';
const COMMENTS_PATH = 'comments.json';
const BRANCH = 'main';

// ── 상태 ──
let comments = [];
let selectedEl = null;
let selectedWord = '';  // 사용자가 선택/롱프레스한 단어/텍스트
let currentFilter = 'all';
let commentPanelOpen = window.innerWidth > 900;
let ghToken = localStorage.getItem('gh-token') || '';
let fileSha = null; // GitHub 파일 SHA (업데이트 시 필요)
let syncStatus = 'idle'; // idle | syncing | error

// ── GitHub API ──
async function ghLoadComments() {
  if (!ghToken) return loadLocal();
  setSyncStatus('syncing');
  try {
    const res = await fetch(
      `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${COMMENTS_PATH}?ref=${BRANCH}`,
      { headers: { 'Authorization': `token ${ghToken}`, 'Accept': 'application/vnd.github.v3+json' } }
    );
    if (res.status === 404) {
      // 파일 없음 — 로컬에서 시작
      fileSha = null;
      setSyncStatus('idle');
      return loadLocal();
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    fileSha = data.sha;
    const b64 = data.content.replace(/\\n/g, '');
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const content = JSON.parse(new TextDecoder().decode(bytes));
    comments = content.comments || content || [];
    localStorage.setItem('carnivore-comments', JSON.stringify(comments));
    setSyncStatus('idle');
  } catch (err) {
    console.error('GitHub load failed:', err);
    setSyncStatus('error');
    loadLocal();
  }
}

async function ghSaveComments() {
  if (!ghToken) { persistLocal(); return; }
  setSyncStatus('syncing');
  const payload = {
    project: '카니보어 탈고',
    updatedAt: new Date().toISOString(),
    totalComments: comments.length,
    pending: comments.filter(c => c.status === 'pending').length,
    fixed: comments.filter(c => c.status === 'fixed').length,
    comments: comments
  };
  const body = {
    message: `탈고: 코멘트 ${comments.length}개 (미수정 ${payload.pending})`,
    content: btoa(unescape(encodeURIComponent(JSON.stringify(payload, null, 2)))),
    branch: BRANCH
  };
  if (fileSha) body.sha = fileSha;
  try {
    const res = await fetch(
      `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${COMMENTS_PATH}`,
      {
        method: 'PUT',
        headers: { 'Authorization': `token ${ghToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      }
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    fileSha = data.content.sha;
    setSyncStatus('idle');
  } catch (err) {
    console.error('GitHub save failed:', err);
    setSyncStatus('error');
  }
  persistLocal(); // 항상 로컬에도 백업
}

function loadLocal() {
  comments = JSON.parse(localStorage.getItem('carnivore-comments') || '[]');
}
function persistLocal() {
  localStorage.setItem('carnivore-comments', JSON.stringify(comments));
}

function setSyncStatus(s) {
  syncStatus = s;
  const el = document.getElementById('syncIndicator');
  if (!el) return;
  el.textContent = s === 'syncing' ? '🔄' : s === 'error' ? '⚠️ 오프라인' : '☁️';
  el.title = s === 'syncing' ? '동기화 중...' : s === 'error' ? 'GitHub 연결 실패 (로컬 저장 중)' : 'GitHub 동기화 완료';
}

function setupToken() {
  const token = prompt(
    'GitHub Personal Access Token을 입력하세요.\\n'
    + '(repo 권한 필요, Settings > Developer settings > Fine-grained tokens)\\n'
    + '비워두면 로컬 전용 모드로 전환됩니다.',
    ghToken
  );
  if (token === null) return;
  ghToken = token.trim();
  if (ghToken) {
    localStorage.setItem('gh-token', ghToken);
  } else {
    localStorage.removeItem('gh-token');
  }
  ghLoadComments().then(() => {
    renderComments();
    updateStats();
    applyCommentMarkers();
  });
}

// ── 초기화 ──
document.addEventListener('DOMContentLoaded', async () => {
  buildToc();
  await ghLoadComments();
  renderComments();
  updateStats();
  applyCommentMarkers();
  if (commentPanelOpen) document.getElementById('commentPanel').classList.add('open');

  // 롱프레스 + 텍스트 ��택으로 코멘트 트리거
  let pressTimer = null;
  let pressTarget = null;
  let pressTriggered = false;

  const contentArea = document.getElementById('contentArea');

  function startPress(e) {
    pressTriggered = false;
    const el = (e.target || e.touches?.[0]?.target)?.closest?.('[id]');
    if (!el || !el.dataset.file) return;
    pressTarget = el;
    pressTimer = setTimeout(() => {
      pressTriggered = true;
      openCommentForElement(el);
    }, 600); // 600ms 롱��레스
  }

  function endPress(e) {
    clearTimeout(pressTimer);
    // 롱프레스로 이미 열렸으면 무시
    if (pressTriggered) return;

    setTimeout(() => {
      const sel = window.getSelection();
      const hasSelection = sel && sel.toString().trim().length > 0;

      if (hasSelection) {
        // 텍스트 선택 → 새 코멘트 입력
        const el = sel.anchorNode?.parentElement?.closest?.('[id]');
        if (el && el.dataset.file) {
          openCommentForElement(el);
        }
      } else if (pressTarget) {
        // 짧은 클릭 + 기존 코멘트 있으면 → 우측 패널에 해당 코멘트 표시
        const existing = comments.filter(c => c.targetId === pressTarget.id);
        if (existing.length > 0) {
          if (!commentPanelOpen) toggleComments();
          // 해당 문단 코멘트만 필터링 표시
          showCommentsForTarget(pressTarget.id);
        }
      }
    }, 200);
  }

  function cancelPress() { clearTimeout(pressTimer); }

  contentArea.addEventListener('mousedown', startPress);
  contentArea.addEventListener('mouseup', endPress);
  contentArea.addEventListener('mouseleave', cancelPress);
  contentArea.addEventListener('touchstart', startPress, { passive: true });
  contentArea.addEventListener('touchend', endPress);
  contentArea.addEventListener('touchcancel', cancelPress);
  contentArea.addEventListener('touchmove', cancelPress, { passive: true });

  // Ctrl+Enter로 저장
  document.getElementById('commentText').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      saveComment();
    }
  });
});

// ── 문단별 코멘트 보기 (짧은 클릭) ──
function showCommentsForTarget(targetId) {
  const list = document.getElementById('commentList');
  const targetComments = comments.filter(c => c.targetId === targetId);
  if (targetComments.length === 0) return;

  // 필터 리셋 표시
  document.querySelectorAll('.filter-bar button').forEach(b => b.classList.remove('active'));

  // 상단에 "이 문단의 코멘트" 헤더 + 전체보기 버튼
  const header = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
    <span style="font-size:13px;font-weight:bold;color:var(--accent);">📍 이 문단의 코멘트 (${targetComments.length}개)</span>
    <button onclick="filterComments('all',null)" style="font-size:11px;padding:3px 8px;border-radius:4px;border:1px solid var(--border);background:white;cursor:pointer;">전체 보기</button>
  </div>`;

  // 기존 renderComments 로직 재활용
  const prevFilter = currentFilter;
  const prevComments = [...comments];
  comments = targetComments;
  currentFilter = 'all';
  renderComments();
  comments = prevComments;
  currentFilter = prevFilter;

  // 헤더 삽입
  list.insertAdjacentHTML('afterbegin', header);

  // 첫 코멘트 카드로 스크롤
  const firstCard = list.querySelector('.comment-card');
  if (firstCard) firstCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── 코멘트 열기 (선택 텍스트 + 문장 하이라이트) ──
function openCommentForElement(el) {
  selectedEl = el;

  // 선택된 텍스트 가져오기
  const sel = window.getSelection();
  selectedWord = (sel && sel.toString().trim()) || '';

  // 문단 전체 텍스트
  const fullText = el.textContent || '';

  // 선택 단어가 속한 문장 찾기
  let displayHtml = '';
  if (selectedWord) {
    // 문장 분리 (마침표, 물음표, 느낌표, 줄바꿈 기준)
    const sentences = fullText.split(/(?<=[.?!\\uB2E4\\n])\\s*/);
    const matchSentence = sentences.find(s => s.includes(selectedWord)) || fullText;
    // 선택 단어를 하이라이트
    const escaped = selectedWord.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
    displayHtml = matchSentence.replace(
      new RegExp(escaped, 'g'),
      '<mark>' + escHtml(selectedWord) + '</mark>'
    );
  } else {
    // 롱프레스만 한 경우 — 문단 앞부분 표시
    displayHtml = fullText.substring(0, 150) + (fullText.length > 150 ? '...' : '');
  }

  document.getElementById('targetInfo').textContent = `📍 ${el.dataset.file} #${el.dataset.line}`;
  document.getElementById('selectedText').innerHTML = displayHtml;
  document.getElementById('commentInput').classList.add('active');
  document.getElementById('commentText').value = '';
  document.getElementById('commentText').focus();
  if (!commentPanelOpen) toggleComments();
}

// ── 목차 빌드 ──
function buildToc() {
  const list = document.getElementById('tocList');
  const parts = document.querySelectorAll('.part-divider');
  const chapters = document.querySelectorAll('.chapter');

  parts.forEach(p => {
    const h = p.querySelector('h1');
    const sub = p.querySelector('p');
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.className = 'part';
    a.href = '#' + p.id;
    a.textContent = h.textContent + ' ' + (sub ? sub.textContent : '');
    li.appendChild(a);
    list.appendChild(li);
  });

  chapters.forEach(c => {
    const h = c.querySelector('h1');
    if (!h) return;
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent.substring(0, 30);
    li.appendChild(a);
    list.appendChild(li);
  });
}

// ── 코멘트 CRUD ──
function saveComment() {
  const text = document.getElementById('commentText').value.trim();
  if (!text || !selectedEl) return;

  const comment = {
    id: Date.now().toString(36),
    targetId: selectedEl.id,
    file: selectedEl.dataset.file,
    line: parseInt(selectedEl.dataset.line),
    excerpt: selectedEl.textContent.substring(0, 100),
    selectedWord: selectedWord || '',  // 사용자가 선택한 단어/구절
    text: text,
    status: 'pending', // pending | fixed
    createdAt: new Date().toISOString(),
    fixedAt: null
  };

  comments.push(comment);
  ghSaveComments();
  renderComments();
  updateStats();
  applyCommentMarkers();
  cancelComment();
}

function cancelComment() {
  document.getElementById('commentInput').classList.remove('active');
  document.getElementById('commentText').value = '';
  selectedEl = null;
}

// ── 리뷰 액션 ──
function approveComment(id) {
  const c = comments.find(x => x.id === id);
  if (!c) return;
  c.status = 'approved';
  c.reviewedAt = new Date().toISOString();
  ghSaveComments();
  renderComments();
  updateStats();
  applyCommentMarkers();
}

function rejectComment(id) {
  const c = comments.find(x => x.id === id);
  if (!c) return;
  c.status = 'rejected';
  c.reviewedAt = new Date().toISOString();
  ghSaveComments();
  renderComments();
  updateStats();
  applyCommentMarkers();
}

function suggestComment(id) {
  const c = comments.find(x => x.id === id);
  if (!c) return;
  const suggestion = prompt('수정 제안을 입력하세요:', c.proposed || '');
  if (suggestion === null) return;
  c.status = 'suggested';
  c.suggestion = suggestion.trim();
  c.reviewedAt = new Date().toISOString();
  ghSaveComments();
  renderComments();
  updateStats();
  applyCommentMarkers();
}

function resetToReview(id) {
  const c = comments.find(x => x.id === id);
  if (!c) return;
  c.status = 'review';
  c.reviewedAt = null;
  c.suggestion = null;
  ghSaveComments();
  renderComments();
  updateStats();
  applyCommentMarkers();
}

function deleteComment(id) {
  if (!confirm('이 코멘트를 삭제할까요?')) return;
  comments = comments.filter(x => x.id !== id);
  ghSaveComments();
  renderComments();
  updateStats();
  applyCommentMarkers();
}

function editComment(id) {
  const c = comments.find(x => x.id === id);
  if (!c) return;
  const newText = prompt('수정:', c.text);
  if (newText !== null && newText.trim()) {
    c.text = newText.trim();
    ghSaveComments();
    renderComments();
  }
}

// ── 렌더링 ──
function renderComments() {
  const list = document.getElementById('commentList');
  const filtered = currentFilter === 'all' ? comments
    : comments.filter(c => c.status === currentFilter);

  if (filtered.length === 0) {
    list.innerHTML = '<p style="color:#999;font-size:13px;padding:20px 0;text-align:center;">'
      + (comments.length === 0 ? '문단을 클릭하여 코멘트를 추가하세요' : '해당 필터에 코멘트가 없습니다')
      + '</p>';
    return;
  }

  list.innerHTML = filtered.map(c => {
    const statusLabels = {
      pending: '⏳ 대기', review: '🔍 검토', approved: '✅ 승인',
      rejected: '❌ 취소', suggested: '💡 제안'
    };
    const statusLabel = statusLabels[c.status] || c.status;

    // 변경 비교 영역 (review 상태일 때)
    let diffHtml = '';
    if (['review','approved','rejected','suggested'].includes(c.status)) {
      const hasOriginal = c.original && c.original !== c.excerpt;
      const hasProposed = c.proposed && c.proposed !== '원고에 반영 완료 — 탈고 리더에서 확인 후 승인/취소/제안해주세요';
      diffHtml = '<div class="diff-box">';
      if (hasOriginal) {
        diffHtml += `<div class="diff-original"><span class="diff-label">❌ 수정 전</span>${escHtml(c.original)}</div>`;
      }
      if (hasProposed) {
        diffHtml += `<div class="diff-proposed"><span class="diff-label">✅ 수정 후</span>${escHtml(c.proposed)}</div>`;
      }
      if (!hasOriginal && !hasProposed) {
        diffHtml += `<div class="diff-proposed"><span class="diff-label">📝 반영됨</span>본문에 직접 반영 완료 — 해당 문단을 클릭하여 확인하세요</div>`;
      }
      if (c.suggestion) {
        diffHtml += `<div class="diff-suggestion"><span class="diff-label">💡 내 제안</span>${escHtml(c.suggestion)}</div>`;
      }
      diffHtml += '</div>';
    }

    // 액션 버튼 (상태에 따라)
    let actionsHtml = '';
    if (c.status === 'pending') {
      actionsHtml = `
        <button onclick="editComment('${c.id}')">✏️ 수정</button>
        <button class="del-btn" onclick="deleteComment('${c.id}')">🗑</button>`;
    } else if (c.status === 'review') {
      actionsHtml = `
        <button class="approve-btn" onclick="approveComment('${c.id}')">✅ 승인</button>
        <button class="reject-btn" onclick="rejectComment('${c.id}')">❌ 취소</button>
        <button class="suggest-btn" onclick="suggestComment('${c.id}')">💡 제안</button>`;
    } else if (['approved','rejected','suggested'].includes(c.status)) {
      actionsHtml = `
        <button onclick="resetToReview('${c.id}')">↩ 다시 검토</button>
        <button class="del-btn" onclick="deleteComment('${c.id}')">🗑</button>`;
    }

    return `
    <div class="comment-card ${c.status}" data-id="${c.id}">
      <div class="meta">
        <span>${c.file}:${c.line}</span>
        <span class="status-badge ${c.status}">${statusLabel}</span>
        <a onclick="scrollToTarget('${c.targetId}')">이동</a>
      </div>
      <div class="excerpt">${c.selectedWord ? '📌 "' + escHtml(c.selectedWord) + '" — ' : ''}${escHtml(c.excerpt)}</div>
      <div class="text">💬 ${escHtml(c.text)}</div>
      ${diffHtml}
      <div class="meta">${formatDate(c.createdAt)}${c.reviewedAt ? ' → ' + formatDate(c.reviewedAt) : ''}</div>
      <div class="actions">${actionsHtml}</div>
    </div>`;
  }).join('');
}

function applyCommentMarkers() {
  // 모든 마커 초기화
  document.querySelectorAll('.has-comment, .is-fixed').forEach(el => {
    el.classList.remove('has-comment', 'is-fixed');
    el.removeAttribute('data-comment-count');
  });

  // 문단별 코멘트 수 집계
  const countMap = {};
  const statusMap = {};
  comments.forEach(c => {
    countMap[c.targetId] = (countMap[c.targetId] || 0) + 1;
    if (!statusMap[c.targetId]) statusMap[c.targetId] = c.status;
    // 우선순위: review > pending > suggested > approved > rejected
    const priority = { review: 5, pending: 4, suggested: 3, approved: 2, rejected: 1 };
    const cur = priority[c.status] || 0;
    const prev = priority[statusMap[c.targetId]] || 0;
    if (cur > prev) statusMap[c.targetId] = c.status;
  });

  Object.keys(countMap).forEach(tid => {
    const el = document.getElementById(tid);
    if (!el) return;
    el.setAttribute('data-comment-count', countMap[tid]);
    const s = statusMap[tid];
    if (s === 'approved') {
      el.classList.add('is-fixed');
    } else if (s === 'review') {
      el.classList.add('has-comment');
      el.style.borderLeftColor = '#1565c0';
    } else {
      el.classList.add('has-comment');
    }
  });
}

function updateStats() {
  const total = comments.length;
  const pending = comments.filter(c => c.status === 'pending').length;
  const review = comments.filter(c => c.status === 'review').length;
  const approved = comments.filter(c => c.status === 'approved').length;
  document.getElementById('statTotal').textContent = total;
  document.getElementById('statPending').textContent = pending;
  document.getElementById('statFixed').textContent = review + '검토 ' + approved + '승인';
}

// ── 필터 ──
function filterComments(filter, btn) {
  currentFilter = filter;
  document.querySelectorAll('.filter-bar button').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderComments();
}

// ── 내보내기/가져오기 ──
function exportComments() {
  const data = {
    project: '카니보어 탈고',
    exportedAt: new Date().toISOString(),
    totalComments: comments.length,
    pending: comments.filter(c => c.status === 'pending').length,
    fixed: comments.filter(c => c.status === 'fixed').length,
    comments: comments
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `carnivore-comments-${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function importComments() {
  document.getElementById('importFile').click();
}

function handleImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result);
      const imported = data.comments || data;
      if (!Array.isArray(imported)) throw new Error('invalid');

      // 중복 제거: 같은 ID는 건너뜀
      const existingIds = new Set(comments.map(c => c.id));
      let added = 0;
      imported.forEach(c => {
        if (!existingIds.has(c.id)) {
          comments.push(c);
          added++;
        }
      });

      ghSaveComments();
      renderComments();
      updateStats();
      applyCommentMarkers();
      alert(`${added}개 코멘트를 가져왔습니다 (중복 ${imported.length - added}개 건너뜀)`);
    } catch (err) {
      alert('잘못된 파일 형식입니다');
    }
  };
  reader.readAsText(file);
  event.target.value = '';
}

// ── UI 토글 ──
function toggleComments() {
  const panel = document.getElementById('commentPanel');
  commentPanelOpen = !commentPanelOpen;
  panel.classList.toggle('open');
  const btn = document.getElementById('commentToggle');
  btn.classList.toggle('active', commentPanelOpen);
}

function toggleToc() {
  document.getElementById('tocPanel').classList.toggle('open');
}

function scrollToTarget(targetId) {
  const el = document.getElementById(targetId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.style.outline = '2px solid var(--accent)';
    setTimeout(() => el.style.outline = '', 2000);
  }
}

// ── 유틸 ──
function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`;
}
</script>

</body>
</html>
"""


def build_term_index():
    """핵심 용어 색인 생성 — 용어별 등장 위치(파일:줄) 매핑"""
    import json

    # 핵심 용어 목록 (카니보어 원고에서 반복 등장하는 전문 용어)
    TERMS = [
        # 호르몬/대사
        "인슐린", "인슐린 저항성", "고인슐린혈증", "케톤", "케톤체", "BHB",
        "렙틴", "코르티솔", "에스트로겐", "이소플라본", "mTOR", "오토파지",
        "글루카곤", "IGF-1",
        # 지질
        "콜레스테롤", "LDL", "sdLDL", "HDL", "중성지방", "TG/HDL",
        "포화지방", "불포화지방", "오메가6", "오메가3", "리놀레산",
        "트랜스 지방", "과산화지질", "PUFA",
        # 항영양소/독소
        "렉틴", "글루텐", "글리아딘", "피틴산", "옥살산", "사포닌",
        "솔라닌", "zonulin", "항영양소",
        # 장/면역
        "장누수", "장벽", "타이트 정션", "마이크로바이옴", "장-뇌 축",
        "LPS", "TNF", "IL-6", "사이토카인", "자가면역",
        # 질환
        "당뇨", "비만", "치매", "우울", "아토피", "PCOS", "지방간",
        "역류성 식도염", "식곤증", "브레인포그", "대사증후군",
        # 식단/영양
        "카니보어", "키토", "저탄고지", "간헐적 단식",
        "비타민C", "비타민D", "비타민K2", "DHA", "EPA",
        "DIAAS", "생체이용률",
        # 인물/연구
        "앤셀 키스", "Bikman", "Jason Fung", "Paul Saladino", "Fasano",
        "웨스턴 프라이스", "이누이트", "마사이",
        # 산업/제도
        "스타틴", "식이지침", "맥거번", "PURE", "블루존",
    ]

    index = {}
    for entry in CHAPTERS:
        filepath, part_info = entry
        if filepath is None:
            continue
        full_path = os.path.join(BASE_DIR, filepath)
        if not os.path.exists(full_path):
            continue
        file_id = os.path.basename(filepath).replace('.md', '')
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for term in TERMS:
            for i, line in enumerate(lines, 1):
                if term in line:
                    if term not in index:
                        index[term] = []
                    index[term].append({
                        "file": file_id,
                        "line": i,
                        "context": line.strip()[:80]
                    })

    # 중복 제거 및 정렬
    for term in index:
        seen = set()
        unique = []
        for loc in index[term]:
            key = f"{loc['file']}:{loc['line']}"
            if key not in seen:
                seen.add(key)
                unique.append(loc)
        index[term] = sorted(unique, key=lambda x: (x['file'], x['line']))

    output = {
        "description": "카니보어 원고 용어 색인 — 용어별 등장 위치",
        "generatedAt": __import__('datetime').datetime.now().isoformat(),
        "totalTerms": len(index),
        "index": dict(sorted(index.items()))
    }

    output_path = os.path.join(DOCS_DIR, "term_index.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  용어 색인: {output_path} ({len(index)}개 용어)")
    return index


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    print("  원고 변환 중...")
    content = build_content()
    html_out = HTML_TEMPLATE.replace('{{CONTENT}}', content)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_out)
    size_kb = os.path.getsize(OUTPUT_HTML) // 1024
    print(f"  완료: {OUTPUT_HTML} ({size_kb}KB)")

    print("  용어 색인 생성 중...")
    build_term_index()

    print("  코멘트 리매핑 확인 중...")
    remap_comments()

    print(f"  GitHub Pages: docs/ 배포 준비 완료")


if __name__ == '__main__':
    main()
