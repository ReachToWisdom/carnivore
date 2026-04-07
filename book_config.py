"""
카니보어 책 프로젝트 공통 설정 (SSOT)
모든 빌드 스크립트(latex, html, proofreader)는 여기서 import한다.
"""

# ── GitHub 레포 ──────────────────────────────
GITHUB_OWNER = "ReachToWisdom"
GITHUB_REPO = "carnivore"
GITHUB_BRANCH = "main"
COMMENTS_FILE = "comments.json"

# ── localStorage 키 ──────────────────────────
LS_COMMENTS_KEY = "carnivore-comments"
LS_TOKEN_KEY = "gh-token"

# ── 챕터 빌드 순서 (단일 정의) ────────────────
# (filepath, part_info)
# part_info: 부 구분일 때 (부번호, 부제목), 본문일 때 None
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

# ── 헬퍼 ─────────────────────────────────────
GH_REPO_PATH = f"{GITHUB_OWNER}/{GITHUB_REPO}"
GH_API_COMMENTS = f"repos/{GH_REPO_PATH}/contents/{COMMENTS_FILE}"
