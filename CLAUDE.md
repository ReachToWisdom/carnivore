# 카니보어 — 인간 본래의 식단으로 돌아가다

진화적 영양학 기반 카니보어(육식) 식단 출판용 원고 프로젝트

## 기술 스택

- **원고**: 마크다운(.md) → chapters/ 폴더
- **출력**: LaTeX PDF (메인), HTML 인쇄본/압축본 (보조)
- **차트**: matplotlib (generate_charts.py → _charts/*.png)
- **생성 스크립트**: Python (generate_book_latex.py, generate_book_html.py 등)

## 현재 상태 (2026-04-03)

- **원고**: 전체 완성 (~6,800줄 / 30개 파일 / 6부+부록)
- **파일 구조**: 모듈화 완료 — `BOOK_INDEX.md`로 파일↔내용 매핑
- **출력물**: carnivore_book.pdf (LaTeX, 1.6MB)
- **단계**: 최종 교정/출판 준비

## 핵심 규칙

1. **근거 원칙**: 모든 핵심 주장에 논문/연구/뉴스 출처 명시
2. **소개자 톤**: "내 주장"이 아닌 "연구를 소개하는" 입장
3. **두괄식**: 쉬운 요약 → 전문적 뒷받침 순서
4. **제작자**: 혜통

## 개발 명령어

```bash
cd D:/DevBrowser/apps/carnivore
python generate_book_latex.py    # LaTeX PDF 생성 (메인)
python generate_book_html.py     # HTML 인쇄본
python generate_charts.py        # 차트 재생성
```

## 폴더 구조

- `chapters/` — 원고 마크다운 30개 (모듈화 완료)
- `BOOK_INDEX.md` — **파일↔내용 인덱스** (편집 시 반드시 참조)
- `_charts/` — 통계 차트 15개 (PNG)
- `_backup_full/` — 구 모놀리식 파일 백업

## 편집 규칙 (토큰 최소화)

1. **파일 전체 Read 금지**: `BOOK_INDEX.md`에서 키워드→파일+줄번호(L#) 특정 → `Read(offset=L#, limit=50~100)`으로 해당 섹션만 읽기
2. **300줄 초과 금지**: 넘으면 섹션 단위 분할 (응집도 높으면 예외, 최대 450줄)
3. **분할/병합 시**: `BOOK_INDEX.md` + `generate_book_latex.py` chapters 배열 동시 갱신
4. **PDF 빌드**: 사용자가 요청할 때만 `python generate_book_latex.py` 실행
5. **인덱스 먼저**: 어떤 편집이든 BOOK_INDEX.md를 먼저 Read → 대상 특정 → 최소 범위만 Read/Edit

## 자기 검증

위 규칙을 위반하는 코드를 작성하려 할 때:
1. 즉시 중단하고 "⚠️ SPEC 위반: [항목]" 경고 출력
2. 사용자에게 승인 요청
3. 승인 없이 진행 금지
