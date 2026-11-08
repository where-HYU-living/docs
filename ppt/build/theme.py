"""배경 테마 SVG 를 만든다: python3 docs/ppt/build/theme.py

PDF 뷰어(macOS 미리보기 등)가 SVG mask·pattern·반투명을 저해상도 이미지로 바꾸지 않도록
모든 선을 바탕색과 미리 섞은 단색으로 그린다. 페이드는 세로선을 짧은 토막으로 나눠 표현한다.
"""
from pathlib import Path

W, H = 1920, 1080
NAVY = (0x12, 0x3F, 0x74)
PAPER = (0xF6, 0xF8, 0xFB)
WHITE = (0xFF, 0xFF, 0xFF)
OUT = Path(__file__).resolve().parent.parent / 'assets' / 'theme'


def mix(bg, fg, a):
    return '#%02x%02x%02x' % tuple(round(b + (f - b) * a) for b, f in zip(bg, fg))


def grid(bg, fg, minor_a, major_a, fade, y_end, seg=12):
    """fade(y) -> 0..1. y_end 아래로는 그리지 않는다."""
    out = []
    for major in (False, True):
        a0 = major_a if major else minor_a
        sw = 1.4 if major else 1
        step = 120 if major else 24
        # 가로선
        for y in range(0, y_end + 1, step):
            if not major and y % 120 == 0:
                continue
            f = fade(y)
            if f <= 0.01:
                continue
            out.append(f'<path d="M0 {y}.5H{W}" stroke="{mix(bg, fg, a0 * f)}" stroke-width="{sw}"/>')
        # 세로선: 토막마다 색을 달리한다
        for x in range(0, W + 1, step):
            if not major and x % 120 == 0:
                continue
            for y in range(0, y_end, seg):
                f = fade(y + seg / 2)
                if f <= 0.01:
                    continue
                out.append(f'<path d="M{x}.5 {y}V{min(y + seg, y_end)}" stroke="{mix(bg, fg, a0 * f)}" stroke-width="{sw}"/>')
    return out


def svg(comment, bg, body):
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" shape-rendering="crispEdges">\n<!-- {comment} -->\n'
    return head + f'<rect width="{W}" height="{H}" fill="{mix(bg, bg, 0)}"/>\n<g fill="none">\n' + '\n'.join(body) + '\n</g>\n'


def lerp_fade(points):
    def f(y):
        for (y0, v0), (y1, v1) in zip(points, points[1:]):
            if y0 <= y <= y1:
                return v0 + (v1 - v0) * (y - y0) / (y1 - y0)
        return points[-1][1] if y > points[-1][0] else points[0][1]
    return f


# 본문 장: 제목 영역에만 모눈, 아래로 사라짐 + 위·아래 남색 띠
page = svg('본문 장 배경: 평면도 모눈(24px, 굵은 선 120px = 본문 여백)이 제목 영역에만 깔리고 아래로 사라진다', PAPER,
           grid(PAPER, NAVY, .10, .20, lerp_fade([(0, 1), (180, .45), (360, 0)]), 360))
page += f'<rect width="{W}" height="10" fill="{mix(NAVY, NAVY, 0)}"/>\n<rect y="{H - 6}" width="{W}" height="6" fill="{mix(NAVY, NAVY, 0)}"/>\n</svg>\n'

# 표지·마무리: 전체 모눈, 아래로 갈수록 옅게
cover = svg('표지·마무리 배경: 왼쪽 글 영역 전체에 평면도 모눈', PAPER,
            grid(PAPER, NAVY, .10, .20, lerp_fade([(0, 1), (H, .35)]), H, seg=24))
cover += f'<rect width="{W}" height="10" fill="{mix(NAVY, NAVY, 0)}"/>\n</svg>\n'

# 구분 장: 남색 위 흰 모눈
blue = svg('구분 장 배경: 남색 위 흰 모눈', NAVY, grid(NAVY, WHITE, .08, .16, lambda y: 1, H, seg=H)) + '</svg>\n'

for name, s in (('page.svg', page), ('cover.svg', cover), ('blueprint.svg', blue)):
    (OUT / name).write_text(s)
    print(name, len(s) // 1024, 'KB')
