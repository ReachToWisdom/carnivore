# 카니보어 — 인간 본래의 식단으로 돌아가다

진화적 영양학 기반 카니보어(육식) 식단 출판용 원고 프로젝트

## 기술 스택

- **원고**: 마크다운(.md) → chapters/ 폴더
- **출력**: LaTeX PDF (메인), HTML 인쇄본/압축본 (보조)
- **차트**: matplotlib (generate_charts.py → _charts/*.png)
- **생성 스크립트**: Python (generate_book_latex.py, generate_book_html.py 등)
- **탈고 리더**: GitHub Pages (docs/index.html) + GitHub API 코멘트 동기화
- **배포**: https://reachtowisdom.github.io/carnivore/

## 현재 상태 (2026-04-05)

- **원고**: 전체 완성 (~6,900줄 / 35개 파일 / 6부+부록)
- **파일 구조**: 모듈화 완료 — `BOOK_INDEX.md`로 파일↔내용 매핑
- **출력물**: carnivore_book.pdf (LaTeX, 1.7MB)
- **탈고 시스템**: GitHub Pages 이북 리더 + 코멘트 리뷰 워크플로우
- **단계**: 탈고/교정 진행 중

## 핵심 규칙

1. **근거 원칙**: 모든 핵심 주장에 논문/연구/뉴스 출처 명시
2. **소개자 톤**: "내 주장"이 아닌 "연구를 소개하는" 입장
3. **두괄식**: 쉬운 요약 → 전문적 뒷받침 순서
4. **제작자**: 혜통

## 개발 명령어

```bash
cd D:/Claudehub/apps/carnivore
python generate_book_latex.py    # LaTeX PDF 생성 (메인 출력물)
python generate_proofreader.py   # 탈고 리더 생성 (docs/index.html + 코멘트 리매핑)
python generate_charts.py        # 차트 재생성
```

**SSOT**: 챕터 배열, GitHub 레포 정보, localStorage 키는 모두 `book_config.py`에 단일 정의되어 있다.

## 폴더 구조

```
carnivore/
├── chapters/           # 원고 마크다운 35개 (모듈화 완료)
├── _charts/            # 통계 차트 15개 (PNG)
├── docs/               # GitHub Pages 배포
│   ├── index.html      # 탈고 리더 (자동 생성)
│   └── term_index.json # 용어 색인 (80개 용어, 자동 생성)
├── BOOK_INDEX.md       # 파일↔내용 인덱스 (편집 시 반드시 참조)
├── book_config.py      # SSOT (챕터 배열, GitHub 레포, localStorage 키)
├── generate_book_latex.py   # LaTeX PDF 생성
├── generate_proofreader.py  # 탈고 리더 생성
├── generate_charts.py       # 차트 생성
└── _archive/           # outdated 스크립트 보관
```

## 탈고 워크플로우

### 코멘트 저장 위치
- **GitHub**: `comments.json` (레포 루트, API로 자동 저장)
- **크로스 디바이스**: 아이폰/PC 어디서든 동일 코멘트 동기화

### 리뷰 상태 흐름
```
1. 사용자: 탈고 리더에서 코멘트 등록 (pending)
2. Claude: comments.json 읽고 → 원고 수정 → original/proposed 기록 (review)
3. 사용자: 승인(approved) / 취소(rejected) / 제안(suggested)
4. suggested → Claude가 제안 반영 → 다시 review
```

### Claude 수정 절차
1. `comments.json` 다운로드 → pending 코멘트 확인
2. `term_index.json`으로 용어 중복 등장 위치 파악
3. 원고 수정 → comments.json에 original/proposed 기록 → status를 review로 변경
4. `python generate_proofreader.py` → git push
5. 사용자가 탈고 리더에서 승인/취소/제안

### 탈고 리더 조작법
- **짧은 클릭**: 코멘트 있는 문단 → 우측에 기존 코멘트 표시
- **롱프레스(0.6초)**: 새 코멘트 입력
- **텍스트 선택**: 선택한 단어가 속한 문장 표시 + 새 코멘트 입력

## 편집 규칙 (토큰 최소화)

1. **파일 전체 Read 금지**: `BOOK_INDEX.md`에서 키워드→파일+줄번호(L#) 특정 → `Read(offset=L#, limit=50~100)`으로 해당 섹션만 읽기
2. **용어 색인 활용**: 동일 용어 수정 시 `docs/term_index.json`에서 전체 등장 위치 확인 → 일괄 수정
3. **300줄 초과 금지**: 넘으면 섹션 단위 분할 (응집도 높으면 예외, 최대 450줄)
4. **분할/병합 시**: `BOOK_INDEX.md` + `generate_book_latex.py` chapters 배열 동시 갱신
5. **PDF 빌드**: 사용자가 요청할 때만 `python generate_book_latex.py` 실행
6. **인덱스 먼저**: 어떤 편집이든 BOOK_INDEX.md를 먼저 Read → 대상 특정 → 최소 범위만 Read/Edit

## 자기 검증

위 규칙을 위반하는 코드를 작성하려 할 때:
1. 즉시 중단하고 "⚠️ SPEC 위반: [항목]" 경고 출력
2. 사용자에게 승인 요청
3. 승인 없이 진행 금지
