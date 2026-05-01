"""
Sprite sheet loader for unit rendering.
Sheets are 4-col × 2-row JPEGs: NE=0, SE=1, SW=2, NW=3 | idle=row0, walk=row1.
Grey checkerboard backgrounds are converted to transparency.
"""
import os, pygame
from typing import Optional

# Maps unit facing index → sprite sheet column
# facing: 0=SW  1=SE  2=NE  3=NW
_FACING_COL = {0: 2, 1: 1, 2: 0, 3: 3}

# Maps unit type → sprite sheet filename (relative to assets/sprites/)
_SHEET_MAP = {
    "gravy_seal":   "MAGAtummy.jpg",
    "ice_agent":    "ICE agent.jpg",
    "unmarked_van": "unmarked van.jpg",
    "proxy":        "proxy.jpg",
    "maga_cart":    "MagaCart.jpg",
}

_FRAME_W = None   # detected from sheet size
_FRAME_H = None

_TARGET_W = 44    # rendered sprite width  (px)
_TARGET_H = 56    # rendered sprite height (px)


def _remove_grey_bg(surf: pygame.Surface) -> pygame.Surface:
    """Turn checkerboard-grey pixels transparent in-place."""
    out = surf.convert_alpha()
    arr = pygame.PixelArray(out)
    w, h = out.get_size()
    for x in range(w):
        for y in range(h):
            col = out.unmap_rgb(arr[x, y])
            r, g, b = col[0], col[1], col[2]
            mn, mx = min(r, g, b), max(r, g, b)
            spread = mx - mn
            avg    = (r + g + b) / 3
            if spread < 28 and 60 < avg < 200:
                arr[x, y] = out.map_rgb(0, 0, 0, 0)
    del arr
    return out


def _load_sheet(path: str):
    """Load one JPEG sheet, remove grey bg, split into 4×2 scaled frames."""
    raw = pygame.image.load(path).convert_alpha()
    raw = _remove_grey_bg(raw)
    sw, sh = raw.get_size()
    fw, fh = sw // 4, sh // 2
    frames = []   # [row][col] → Surface
    for row in range(2):
        row_frames = []
        for col in range(4):
            rect = pygame.Rect(col * fw, row * fh, fw, fh)
            frame = raw.subsurface(rect).copy()
            frame = pygame.transform.smoothscale(frame, (_TARGET_W, _TARGET_H))
            row_frames.append(frame)
        frames.append(row_frames)
    return frames  # frames[0] = idle row, frames[1] = walk row


class SpriteManager:
    def __init__(self):
        self._sheets: dict[str, list] = {}   # utype → frames[row][col]
        self._base_dir = os.path.join(
            os.path.dirname(__file__), "..", "assets", "sprites"
        )

    def _ensure(self, utype: str) -> bool:
        if utype in self._sheets:
            return True
        fname = _SHEET_MAP.get(utype)
        if not fname:
            return False
        path = os.path.normpath(os.path.join(self._base_dir, fname))
        if not os.path.exists(path):
            return False
        try:
            self._sheets[utype] = _load_sheet(path)
            return True
        except Exception:
            self._sheets[utype] = None  # mark failed so we don't retry
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
