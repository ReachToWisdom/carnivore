#!/usr/bin/env python3
"""
카니보어 책 본문용 도식/흐름도/인포그래픽 생성
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

CHART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_charts")
os.makedirs(CHART_DIR, exist_ok=True)

# 색상 팔레트
DARK_RED = '#8B0000'
DARK_BLUE = '#2C3E50'
ORANGE = '#E67E22'
GREEN = '#27AE60'
GRAY = '#7F8C8D'
LIGHT_BG = '#F9F6F1'
WARNING = '#E74C3C'


def save(fig, name):
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  생성: {name}")


# ═══════════════════════════════════════════════════════
# 1. 식용유 6단계 정제 공정
# ═══════════════════════════════════════════════════════
def chart_seed_oil_process():
    fig, ax = plt.subplots(figsize=(10.0, 7.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # 제목
    ax.text(5, 9.5, '식물성 기름 6단계 정제 공정', fontsize=25.2, fontweight='bold',
            ha='center', va='center', color=DARK_BLUE)
    ax.text(5, 9.0, '씨앗에서 투명한 기름이 되기까지', fontsize=15.4,
            ha='center', va='center', color=GRAY)

    steps = [
        ('1단계', '분쇄·압착', '씨앗을 으깨어\n기름을 짜냄', '#3498DB'),
        ('2단계', '용매 추출', '헥산(석유 유래)\n화학 용매로 추출', '#E67E22'),
        ('3단계', '탈검', '인지질 등\n불순물 제거', '#E67E22'),
        ('4단계', '정제', '수산화나트륨\n(가성소다) 처리', WARNING),
        ('5단계', '표백', '활성백토로\n색소·산화물 제거', WARNING),
        ('6단계', '탈취', '200~270°C 고온\n냄새 제거', DARK_RED),
    ]

    y_start = 8.0
    y_step = 1.15
    box_w = 7.5
    box_h = 0.85

    for i, (num, title, desc, color) in enumerate(steps):
        y = y_start - i * y_step
        # 박스
        rect = FancyBboxPatch((1.25, y - box_h/2), box_w, box_h,
                              boxstyle="round,pad=0.1", facecolor=color, alpha=0.12,
                              edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)
        # 번호
        ax.text(2.0, y, num, fontsize=14, fontweight='bold', ha='center', va='center', color=color)
        # 제목
        ax.text(3.5, y, title, fontsize=18.2, fontweight='bold', ha='left', va='center', color=DARK_BLUE)
        # 설명
        ax.text(6.5, y, desc, fontsize=13.3, ha='left', va='center', color='#444')
        # 화살표
        if i < len(steps) - 1:
            ax.annotate('', xy=(5, y - box_h/2 - 0.05), xytext=(5, y - box_h/2 - y_step + box_h/2 + 0.35),
                        arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.5))

    # 비교 박스
    # 동물성
    rect1 = FancyBboxPatch((0.5, 0.15), 3.8, 0.8, boxstyle="round,pad=0.1",
                           facecolor=GREEN, alpha=0.15, edgecolor=GREEN, linewidth=1.5)
    ax.add_patch(rect1)
    ax.text(2.4, 0.55, '동물성 지방: 저온 렌더링 1단계', fontsize=14,
            fontweight='bold', ha='center', va='center', color=GREEN)

    rect2 = FancyBboxPatch((5.2, 0.15), 4.3, 0.8, boxstyle="round,pad=0.1",
                           facecolor=WARNING, alpha=0.15, edgecolor=WARNING, linewidth=1.5)
    ax.add_patch(rect2)
    ax.text(7.35, 0.55, '식물성 기름: 화학+고온 6단계 공정', fontsize=14,
            fontweight='bold', ha='center', va='center', color=WARNING)

    save(fig, 'seed_oil_process.png')


# ═══════════════════════════════════════════════════════
# 2. 인슐린 저항성 악순환
# ═══════════════════════════════════════════════════════
def chart_insulin_cycle():
    fig, ax = plt.subplots(figsize=(9.0, 9.0))
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    ax.text(0, 4.5, '인슐린 저항성 악순환', fontsize=25.2, fontweight='bold',
            ha='center', va='center', color=DARK_RED)

    # 원형 배치
    labels = [
        '탄수화물\n과잉 섭취',
        '혈당 급등',
        '인슐린\n대량 분비',
        '지방 저장\n촉진',
        '혈당 급락\n→ 배고픔',
        '과식\n반복',
    ]
    colors = [ORANGE, WARNING, DARK_RED, '#8E44AD', WARNING, ORANGE]
    n = len(labels)
    radius = 3.0
    angles = [np.pi/2 - i * 2 * np.pi / n for i in range(n)]

    for i in range(n):
        x = radius * np.cos(angles[i])
        y = radius * np.sin(angles[i])

        circle = plt.Circle((x, y), 0.9, facecolor=colors[i], alpha=0.15,
                            edgecolor=colors[i], linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, labels[i], fontsize=14, fontweight='bold',
                ha='center', va='center', color=colors[i])

        # 화살표
        next_i = (i + 1) % n
        x2 = radius * np.cos(angles[next_i])
        y2 = radius * np.sin(angles[next_i])
        dx = x2 - x
        dy = y2 - y
        dist = np.sqrt(dx**2 + dy**2)
        # 시작/끝 오프셋
        sx = x + dx/dist * 1.0
        sy = y + dy/dist * 1.0
        ex = x2 - dx/dist * 1.0
        ey = y2 - dy/dist * 1.0
        ax.annotate('', xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle='->', color=GRAY, lw=2))

    # 중심 텍스트
    ax.text(0, 0, '인슐린\n저항성', fontsize=19.6, fontweight='bold',
            ha='center', va='center', color=DARK_RED,
            bbox=dict(boxstyle='round,pad=0.5', facecolor=DARK_RED, alpha=0.1, edgecolor=DARK_RED))

    ax.text(0, -4.3, '→ 결과: 비만, 당뇨, 고혈압, 지방간, 만성 염증', fontsize=15.4,
            ha='center', va='center', color=DARK_BLUE, fontweight='bold')

    save(fig, 'insulin_cycle.png')


# ═══════════════════════════════════════════════════════
# 3. 동맥경화 실제 기전 (염증 모델)
# ═══════════════════════════════════════════════════════
def chart_atherosclerosis():
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    ax.text(5, 5.6, '동맥경화의 실제 기전 — 기름이 끼는 것이 아니다', fontsize=22.4,
            fontweight='bold', ha='center', va='center', color=DARK_RED)

    steps = [
        ('1', '혈관 내피 손상', '고혈당, 산화 스트레스,\n흡연, 만성 염증', WARNING),
        ('2', '산화 sdLDL 침투', '소형 LDL이 손상된\n내피 아래로 침투', ORANGE),
        ('3', '면역 반응', '대식세포가 산화 LDL을\n제거하다 거품세포 형성', '#8E44AD'),
        ('4', '플라크 형성', '거품세포 축적 →\n동맥벽 비후', DARK_RED),
    ]

    x_positions = [1.5, 3.75, 6.0, 8.25]
    for i, (num, title, desc, color) in enumerate(steps):
        x = x_positions[i]
        # 박스
        rect = FancyBboxPatch((x - 0.9, 2.0), 1.8, 2.8,
                              boxstyle="round,pad=0.15", facecolor=color, alpha=0.1,
                              edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        # 번호 원
        circle = plt.Circle((x, 4.3), 0.3, facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, 4.3, num, fontsize=16.8, fontweight='bold', ha='center', va='center', color='white')
        # 제목
        ax.text(x, 3.6, title, fontsize=14, fontweight='bold', ha='center', va='center', color=color)
        # 설명
        ax.text(x, 2.8, desc, fontsize=11.9, ha='center', va='center', color='#444')
        # 화살표
        if i < len(steps) - 1:
            ax.annotate('', xy=(x_positions[i+1] - 1.0, 3.4), xytext=(x + 1.0, 3.4),
                        arrowprops=dict(arrowstyle='->', color=GRAY, lw=2))

    # 핵심 메시지
    ax.text(5, 0.8, '핵심: 문제는 지방을 먹는 것이 아니라 염증이다', fontsize=18.2,
            fontweight='bold', ha='center', va='center', color=DARK_RED,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=DARK_RED, alpha=0.08, edgecolor=DARK_RED))
    ax.text(5, 0.2, '탄수화물 과잉 → 인슐린 저항성 → 만성 염증 → 혈관 손상', fontsize=14,
            ha='center', va='center', color=DARK_BLUE)

    save(fig, 'atherosclerosis_mechanism.png')


# ═══════════════════════════════════════════════════════
# 4. 기준치 하향 → 환자 수 폭증
# ═══════════════════════════════════════════════════════
def chart_threshold_patients():
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 5.0))
    fig.suptitle('진단 기준치 하향 → 하룻밤에 수천만 명의 "환자" 탄생',
                 fontsize=21, fontweight='bold', color=DARK_RED, y=1.02)

    # 고혈압
    ax = axes[0]
    years = ['~1993', '1993', '2017']
    thresholds = [160, 140, 130]
    patients = [30, 50, 81]  # 백만명 (미국)
    bars = ax.bar(years, patients, color=[GREEN, ORANGE, WARNING], alpha=0.7, edgecolor='white')
    for bar, t, p in zip(bars, thresholds, patients):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{t}mmHg\n{p}M명', ha='center', fontsize=11.9, fontweight='bold')
    ax.set_title('고혈압 기준', fontsize=16.8, fontweight='bold', color=DARK_BLUE)
    ax.set_ylabel('환자 수 (백만 명)', fontsize=12.6)
    ax.spines[['top', 'right']].set_visible(False)

    # 콜레스테롤
    ax = axes[1]
    years = ['~1987', '1987', '2001']
    thresholds = [300, 240, 200]
    patients = [12, 52, 105]
    bars = ax.bar(years, patients, color=[GREEN, ORANGE, WARNING], alpha=0.7, edgecolor='white')
    for bar, t, p in zip(bars, thresholds, patients):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{t}mg/dL\n{p}M명', ha='center', fontsize=11.9, fontweight='bold')
    ax.set_title('고콜레스테롤 기준', fontsize=16.8, fontweight='bold', color=DARK_BLUE)
    ax.spines[['top', 'right']].set_visible(False)

    # 당뇨
    ax = axes[2]
    years = ['~1997', '1997', '+HbA1c']
    thresholds = ['140', '126', '6.5%']
    patients = [12, 21, 37]
    bars = ax.bar(years, patients, color=[GREEN, ORANGE, WARNING], alpha=0.7, edgecolor='white')
    for bar, t, p in zip(bars, thresholds, patients):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{t}\n{p}M명', ha='center', fontsize=11.9, fontweight='bold')
    ax.set_title('당뇨 기준', fontsize=16.8, fontweight='bold', color=DARK_BLUE)
    ax.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
    save(fig, 'threshold_patients.png')


# ═══════════════════════════════════════════════════════
# 5. 탄수화물 vs 지방 에너지 시스템 비교
# ═══════════════════════════════════════════════════════
def chart_energy_systems():
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    ax.text(5, 6.6, '두 가지 에너지 시스템 비교', fontsize=22.4, fontweight='bold',
            ha='center', color=DARK_BLUE)

    # 왼쪽: 탄수화물
    rect = FancyBboxPatch((0.3, 0.5), 4.2, 5.5, boxstyle="round,pad=0.2",
                          facecolor=WARNING, alpha=0.06, edgecolor=WARNING, linewidth=2)
    ax.add_patch(rect)
    ax.text(2.4, 5.6, '탄수화물 연소', fontsize=19.6, fontweight='bold',
            ha='center', color=WARNING)

    carb_items = [
        ('저장량', '글리코겐 400~500g', '~ 2,000 kcal'),
        ('혈당', '급등 → 급락 반복', '식곤증, 배고픔'),
        ('인슐린', '지속적 고분비', '지방 저장 촉진'),
        ('결과', '에너지 롤러코스터', '2~3시간마다 배고픔'),
    ]
    for i, (label, desc, note) in enumerate(carb_items):
        y = 4.8 - i * 1.1
        ax.text(0.7, y, f'> {label}', fontsize=12.6, fontweight='bold', color=WARNING)
        ax.text(1.9, y, desc, fontsize=12.6, color='#444')
        ax.text(1.9, y - 0.35, note, fontsize=11.2, color=GRAY, style='italic')

    # 오른쪽: 지방
    rect = FancyBboxPatch((5.5, 0.5), 4.2, 5.5, boxstyle="round,pad=0.2",
                          facecolor=GREEN, alpha=0.06, edgecolor=GREEN, linewidth=2)
    ax.add_patch(rect)
    ax.text(7.6, 5.6, '지방 연소 (케톤)', fontsize=19.6, fontweight='bold',
            ha='center', color=GREEN)

    fat_items = [
        ('저장량', '체지방 10kg 기준', '~ 90,000 kcal'),
        ('혈당', '안정적 유지', '식곤증 없음'),
        ('인슐린', '낮게 유지', '지방 분해 활성'),
        ('결과', '안정적 에너지 공급', '하루 1~2끼로 충분'),
    ]
    for i, (label, desc, note) in enumerate(fat_items):
        y = 4.8 - i * 1.1
        ax.text(5.9, y, f'> {label}', fontsize=12.6, fontweight='bold', color=GREEN)
        ax.text(7.1, y, desc, fontsize=12.6, color='#444')
        ax.text(7.1, y - 0.35, note, fontsize=11.2, color=GRAY, style='italic')

    # VS
    ax.text(5.0, 3.2, 'VS', fontsize=28, fontweight='bold', ha='center', va='center',
            color=DARK_BLUE, alpha=0.3)

    save(fig, 'energy_systems.png')


# ═══════════════════════════════════════════════════════
# 6. 케톤 대사 흐름도
# ═══════════════════════════════════════════════════════
def chart_ketone_pathway():
    fig, ax = plt.subplots(figsize=(10.0, 7.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    ax.text(5, 8.5, '케톤 대사의 다중 효과', fontsize=22.4, fontweight='bold',
            ha='center', color=DARK_BLUE)

    # 중심: 케톤체
    circle = plt.Circle((5, 4.5), 1.0, facecolor=DARK_RED, alpha=0.15,
                        edgecolor=DARK_RED, linewidth=2.5)
    ax.add_patch(circle)
    ax.text(5, 4.7, '케톤체', fontsize=19.6, fontweight='bold', ha='center', color=DARK_RED)
    ax.text(5, 4.2, '(BHB)', fontsize=14, ha='center', color=DARK_RED)

    # 효과 배치
    effects = [
        (1.5, 6.5, '뇌 에너지\n공급', '포도당보다\n효율적', '#3498DB'),
        (8.5, 6.5, '항염 작용', 'NLRP3\n인플라마좀 억제', GREEN),
        (1.5, 2.5, '항산화', 'HDAC 억제 →\n항산화 유전자 활성', '#8E44AD'),
        (8.5, 2.5, '지방 분해\n촉진', '체지방을\n연료로 사용', ORANGE),
        (5, 1.0, 'BDNF 증가', '뇌 신경세포\n성장·보호', '#2980B9'),
        (5, 7.0, '식욕 조절', '포만감 증가\n과식 방지', GREEN),
    ]

    for (x, y, title, desc, color) in effects:
        rect = FancyBboxPatch((x - 0.9, y - 0.5), 1.8, 1.0,
                              boxstyle="round,pad=0.1", facecolor=color, alpha=0.1,
                              edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y + 0.15, title, fontsize=12.6, fontweight='bold', ha='center', va='center', color=color)
        ax.text(x, y - 0.25, desc, fontsize=10.5, ha='center', va='center', color='#555')

        # 화살표 (중심에서 바깥으로)
        dx = x - 5
        dy = y - 4.5
        dist = np.sqrt(dx**2 + dy**2)
        sx = 5 + dx/dist * 1.1
        sy = 4.5 + dy/dist * 1.1
        ex = x - dx/dist * 1.0
        ey = y - dy/dist * 0.6
        ax.annotate('', xy=(ex, ey), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.6))

    save(fig, 'ketone_pathway.png')


# ═══════════════════════════════════════════════════════
def main():
    print("도식/흐름도 이미지 생성 시작...\n")

    chart_seed_oil_process()      # 식용유 6단계 공정
    chart_insulin_cycle()         # 인슐린 저항성 악순환
    chart_atherosclerosis()       # 동맥경화 실제 기전
    chart_threshold_patients()    # 기준치 하향 → 환자 폭증
    chart_energy_systems()        # 탄수화물 vs 지방 에너지
    chart_ketone_pathway()        # 케톤 대사 흐름도

    print(f"\n완료! {CHART_DIR} 에 6개 이미지 생성됨")


if __name__ == "__main__":
    main()
