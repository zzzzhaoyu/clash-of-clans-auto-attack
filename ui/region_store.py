"""已绑定屏幕区域的本地存储。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from uuid import uuid4

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "regions.json"
_NAME_PATTERN = re.compile(r"区域(\d+)")


@dataclass(frozen=True)
class Region:
    """一块屏幕区域。坐标是屏幕绝对坐标，单位像素。"""

    id: str
    name: str
    x1: int
    y1: int
    x2: int
    y2: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class RegionStore:
    """把区域列表写到 data/regions.json，重启后仍然在。"""

    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path) if path is not None else _DEFAULT_PATH
        self._regions: list[Region] = []
        self._next_index = 1
        self.reload()

    def regions(self) -> list[Region]:
        return list(self._regions)

    def get(self, region_id: str) -> Region | None:
        for region in self._regions:
            if region.id == region_id:
                return region
        return None

    def add(self, bounds: tuple[int, int, int, int]) -> Region:
        x1, y1, x2, y2 = _normalize_bounds(bounds)
        region = Region(
            id=uuid4().hex,
            name=self._allocate_name(),
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
        )
        self._regions.append(region)
        self._save()
        return region

    def rename(self, region_id: str, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("名称不能为空")
        self._regions = [
            Region(region.id, cleaned, region.x1, region.y1, region.x2, region.y2)
            if region.id == region_id
            else region
            for region in self._regions
        ]
        if any(region.id == region_id for region in self._regions):
            self._save()

    def update_bounds(self, region_id: str, bounds: tuple[int, int, int, int]) -> None:
        if self.get(region_id) is None:
            return
        x1, y1, x2, y2 = _normalize_bounds(bounds)
        self._regions = [
            Region(region.id, region.name, x1, y1, x2, y2)
            if region.id == region_id
            else region
            for region in self._regions
        ]
        self._save()

    def delete(self, region_id: str) -> None:
        remaining = [region for region in self._regions if region.id != region_id]
        if len(remaining) == len(self._regions):
            return
        self._regions = remaining
        self._save()

    def reload(self) -> None:
        self._regions = []
        self._next_index = 1
        if not self._path.is_file():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return
        if not isinstance(payload, dict):
            return

        raw_regions = payload.get("regions", [])
        if not isinstance(raw_regions, list):
            raw_regions = []

        seen: set[str] = set()
        for item in raw_regions:
            region = _parse_region(item)
            if region is None or region.id in seen:
                continue
            seen.add(region.id)
            self._regions.append(region)

        try:
            self._next_index = int(payload.get("next_index", 1))
        except (TypeError, ValueError):
            self._next_index = 1
        self._next_index = max(1, self._next_index)
        self._ensure_next_index()

    def _allocate_name(self) -> str:
        existing = {region.name for region in self._regions}
        while True:
            name = f"区域{self._next_index}"
            self._next_index += 1
            if name not in existing:
                return name

    def _ensure_next_index(self) -> None:
        highest = 0
        for region in self._regions:
            matched = _NAME_PATTERN.fullmatch(region.name)
            if matched is not None:
                highest = max(highest, int(matched.group(1)))
        self._next_index = max(self._next_index, highest + 1, 1)

    def _save(self) -> None:
        payload = {
            "next_index": self._next_index,
            "regions": [region.to_dict() for region in self._regions],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_suffix(self._path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(self._path)


def _normalize_bounds(
    bounds: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = (int(value) for value in bounds)
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    return x1, y1, x2, y2


def _parse_region(item: object) -> Region | None:
    if not isinstance(item, dict):
        return None
    try:
        region_id = str(item["id"]).strip()
        name = str(item["name"]).strip()
        x1 = int(item["x1"])
        y1 = int(item["y1"])
        x2 = int(item["x2"])
        y2 = int(item["y2"])
    except (KeyError, TypeError, ValueError):
        return None
    if not region_id or not name:
        return None
    x1, y1, x2, y2 = _normalize_bounds((x1, y1, x2, y2))
    return Region(region_id, name, x1, y1, x2, y2)
