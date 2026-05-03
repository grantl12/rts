"""
Generate civilian/Kirk sprite sheets + Kirk stage prop.
Run: python tools/gen_story_sprites.py
"""
import os
import pygame

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(ROOT, "assets", "sprites")
os.makedirs(OUT_DIR, exist_ok=True)

FRAME_W = 48
FRAME_H = 56


def _draw_person(frame, body, accent, hair, face, protest=False, runner=False):
    cx = FRAME_W // 2
    # shadow
    pygame.draw.ellipse(frame, (0, 0, 0, 60), (cx - 9, FRAME_H - 8, 18, 5))
    # legs + boots
    pygame.draw.rect(frame, body, (cx - 8, FRAME_H - 22, 6, 12), border_radius=2)
    pygame.draw.rect(frame, body, (cx + 2, FRAME_H - 22, 6, 12), border_radius=2)
    pygame.draw.rect(frame, (28, 24, 18), (cx - 9, FRAME_H - 11, 8, 3), border_radius=1)
    pygame.draw.rect(frame, (28, 24, 18), (cx + 1, FRAME_H - 11, 8, 3), border_radius=1)
    # torso
    pygame.draw.rect(frame, body, (cx - 10, FRAME_H - 35, 20, 14), border_radius=3)
    pygame.draw.rect(frame, accent, (cx - 9, FRAME_H - 34, 18, 3), border_radius=1)
    # arms
    pygame.draw.rect(frame, body, (cx - 14, FRAME_H - 34, 4, 11), border_radius=2)
    pygame.draw.rect(frame, body, (cx + 10, FRAME_H - 34, 4, 11), border_radius=2)
    # head
    pygame.draw.circle(frame, face, (cx, FRAME_H - 40), 6)
    pygame.draw.rect(frame, hair, (cx - 6, FRAME_H - 46, 12, 4), border_radius=2)

    if protest:
        pygame.draw.rect(frame, (185, 145, 90), (cx - 20, FRAME_H - 52, 15, 9))
        pygame.draw.line(frame, (120, 90, 55), (cx - 12, FRAME_H - 43), (cx - 12, FRAME_H - 24), 2)
    if runner:
        pygame.draw.polygon(frame, (255, 220, 60),
                            [(cx, FRAME_H - 42), (cx + 4, FRAME_H - 36),
                             (cx, FRAME_H - 30), (cx - 4, FRAME_H - 36)])


def _draw_kirk(frame):
    cx = FRAME_W // 2
    _draw_person(frame, (205, 190, 170), (120, 105, 90), (230, 220, 205), (240, 230, 210))
    pygame.draw.circle(frame, (255, 240, 190), (cx, FRAME_H - 40), 9, 1)


def _make_sheet(draw_fn):
    sheet = pygame.Surface((FRAME_W * 4, FRAME_H * 2), pygame.SRCALPHA)
    for row in range(2):
        for col in range(4):
            frame = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
            draw_fn(frame)
            if col in (1, 2):
                frame = pygame.transform.flip(frame, True, False)
            if row == 1:
                frame = frame.copy()
                frame.scroll(dx=(1 if col % 2 == 0 else -1), dy=0)
            sheet.blit(frame, (col * FRAME_W, row * FRAME_H))
    return sheet


def _save(path, surf):
    pygame.image.save(surf, path)
    print(f"saved {path}")


def _gen_unit_sheets():
    palettes = {
        "civilian_normie.png": ((132, 128, 120), (178, 170, 155), (75, 58, 44), (214, 182, 145)),
        "civilian_purple_hair.png": ((120, 118, 132), (165, 155, 190), (145, 72, 195), (214, 182, 145)),
        "civilian_riot_gear.png": ((88, 96, 108), (58, 66, 82), (36, 42, 54), (186, 170, 150)),
        "civilian_runner.png": ((150, 120, 84), (196, 168, 92), (70, 46, 24), (225, 190, 150)),
        "civilian_protester.png": ((92, 116, 96), (126, 150, 128), (170, 48, 48), (220, 186, 145)),
    }
    for fname, (body, accent, hair, face) in palettes.items():
        protest = "protester" in fname
        runner = "runner" in fname
        sheet = _make_sheet(lambda fr, b=body, a=accent, h=hair, f=face, p=protest, r=runner:
                            _draw_person(fr, b, a, h, f, protest=p, runner=r))
        _save(os.path.join(OUT_DIR, fname), sheet)

    kirk = _make_sheet(_draw_kirk)
    _save(os.path.join(OUT_DIR, "kirk.png"), kirk)


def _gen_kirk_stage():
    w, h = 180, 120
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # tent
    pygame.draw.polygon(surf, (58, 86, 112), [(22, 72), (90, 22), (156, 72)])
    pygame.draw.polygon(surf, (32, 56, 80), [(34, 72), (90, 30), (146, 72)])
    pygame.draw.rect(surf, (26, 34, 42), (80, 54, 20, 18), border_radius=2)
    # table
    pygame.draw.rect(surf, (126, 88, 54), (58, 78, 64, 9), border_radius=2)
    pygame.draw.rect(surf, (86, 56, 34), (62, 86, 4, 14))
    pygame.draw.rect(surf, (86, 56, 34), (114, 86, 4, 14))
    # papers + mic
    pygame.draw.rect(surf, (225, 225, 212), (74, 80, 12, 5))
    pygame.draw.rect(surf, (225, 225, 212), (89, 80, 15, 5))
    pygame.draw.line(surf, (18, 18, 18), (104, 77), (112, 68), 2)
    pygame.draw.circle(surf, (58, 58, 58), (114, 66), 3)
    _save(os.path.join(OUT_DIR, "kirk_tent_table.png"), surf)


if __name__ == "__main__":
    pygame.init()
    _gen_unit_sheets()
    _gen_kirk_stage()
    pygame.quit()
    print(f"done -> {OUT_DIR}")
