"""
Sprite sheet loader for unit rendering.
Standard sheets: 4-col × 2-row  (NE=0, SE=1, SW=2, NW=3 | idle=row0, walk=row1).
Stacked sheets:  4-col × 4-row  — two unit types share one file; specify row_offset=2
                 for the second unit.
Grey checkerboard backgrounds are converted to transparency.
"""
import os, pygame
from typing import Optional

# Maps unit facing index → sprite sheet column
# facing: 0=SW  1=SE  2=NE  3=NW
_FACING_COL = {0: 2, 1: 1, 2: 0, 3: 3}

# utype → (filename, row_offset, total_rows)
#   row_offset  — which row to start reading from (0 for normal sheets, 2 for bottom half)
#   total_rows  — total rows in the file (2 for standard, 4 for stacked)
_SHEET_MAP = {
    "gravy_seal":     ("MAGAtummy.jpg",             0, 2),
    "ice_agent":      ("ICE agent.jpg",             0, 2),
    "ice_agent_tac":  ("Ice Agent wTac Gear.jpg",   0, 2),
    "unmarked_van":   ("unmarked van.jpg",          0, 2),
    "proxy":          ("proxy.jpg",                 0, 2),
    "maga_cart":      ("MagaCart.jpg",              0, 2),
    "contractor":     ("contractor.jpg",            0, 2),
    "compliance_bus": ("compliance van.jpg",        0, 2),
    "drone_operator": ("drone operator.jpg",        0, 2),
    "drone_scout":    ("ScoutandAssaultDrones.jpg", 0, 4),
    "drone_assault":  ("ScoutandAssaultDrones.jpg", 2, 4),
    "vbied":          ("coloredcars.jpg",           0, 2),
    "civilian_car":   ("cars.jpg",                 0, 2),
    "patriot_lawyer": ("MAGAmericaFirst.jpg",       0, 2),
}

_TARGET_W = 44    # rendered sprite width  (px)
_TARGET_H = 56    # rendered sprite height (px)


def _remove_grey_bg(surf: pygame.Surface) -> pygame.Surface:
    out = surf.convert_alpha()
    arr = pygame.PixelArray(out)
    w, h = out.get_size()
    for x in range(w):
        for y in range(h):
            col = out.unmap_rgb(arr[x, y])
            r, g, b = col[0], col[1], col[2]
            spread = max(r, g, b) - min(r, g, b)
            avg    = (r + g + b) / 3
            if spread < 28 and 60 < avg < 200:
                arr[x, y] = out.map_rgb(0, 0, 0, 0)
    del arr
    return out


def _load_sheet(path: str, row_offset: int, total_rows: int):
    raw = pygame.image.load(path).convert_alpha()
    raw = _remove_grey_bg(raw)
    sw, sh = raw.get_size()
    fw = sw // 4
    fh = sh // total_rows
    frames = []   # frames[0]=idle, frames[1]=walk
    for anim_row in range(2):
        src_row = row_offset + anim_row
        row_frames = []
        for col in range(4):
            rect = pygame.Rect(col * fw, src_row * fh, fw, fh)
            frame = raw.subsurface(rect).copy()
            frame = pygame.transform.smoothscale(frame, (_TARGET_W, _TARGET_H))
            row_frames.append(frame)
        frames.append(row_frames)
    return frames


class SpriteManager:
    def __init__(self):
        self._sheets: dict[str, list] = {}
        self._base_dir = os.path.join(
            os.path.dirname(__file__), "..", "assets", "sprites"
        )

    def _ensure(self, utype: str) -> bool:
        if utype in self._sheets:
            return True
        entry = _SHEET_MAP.get(utype)
        if not entry:
            return False
        fname, row_offset, total_rows = entry
        path = os.path.normpath(os.path.join(self._base_dir, fname))
        if not os.path.exists(path):
            return False
        try:
            self._sheets[utype] = _load_sheet(path, row_offset, total_rows)
            return True
        except Exception:
            self._sheets[utype] = None
            return False

    def get_frame(self, utype: str, facing: int, moving: bool) -> Optional[pygame.Surface]:
        if not self._ensure(utype):
            return None
        frames = self._sheets.get(utype)
        if not frames:
            return None
        row = 1 if moving else 0
        col = _FACING_COL.get(facing, 2)
        return frames[row][col]


_manager: Optional[SpriteManager] = None


def get_manager() -> SpriteManager:
    global _manager
    if _manager is None:
        _manager = SpriteManager()
    return _manager
