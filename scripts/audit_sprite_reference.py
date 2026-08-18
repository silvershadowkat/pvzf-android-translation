#!/usr/bin/env python3
"""Find official Unity sprites visually similar to a supplied reference crop."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import UnityPy
from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=80)
    return parser.parse_args()


def color_histogram(image: Image.Image) -> tuple[list[float], float]:
    bins = [0] * 48
    orange = 0
    colorful = 0
    for red, green, blue, alpha in image.convert("RGBA").getdata():
        maximum = max(red, green, blue)
        minimum = min(red, green, blue)
        if alpha <= 24 or maximum - minimum <= 30 or maximum <= 50:
            continue
        colorful += 1
        bins[red // 16] += 1
        bins[16 + green // 16] += 1
        bins[32 + blue // 16] += 1
        if red > 130 and red > green * 1.05 and green > blue * 1.15:
            orange += 1
    if colorful < 12:
        return [0.0] * 48, 0.0
    total = float(sum(bins))
    return [value / total for value in bins], orange / colorful


def score(reference_hist: list[float], reference_orange: float, image: Image.Image) -> float:
    histogram, orange = color_histogram(image)
    if not any(histogram) or orange < 0.01:
        return -1.0
    distance = sum(abs(reference - candidate) for reference, candidate in zip(reference_hist, histogram))
    orange_distance = abs(reference_orange - orange)
    return 1.0 - distance - orange_distance * 0.75


def main() -> int:
    args = parse_args()
    reference = Image.open(args.reference).convert("RGBA")
    # The supplied crop contains six identical cards. One sixth is enough and
    # avoids weighting the narrow seams between cards.
    reference = reference.crop((0, 0, max(1, reference.width // 6), reference.height))
    reference_hist, reference_orange = color_histogram(reference)

    env = UnityPy.load(str(args.bundle))
    ranked: list[tuple[float, int, str, Image.Image]] = []
    sprite_count = 0
    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        sprite_count += 1
        try:
            data = obj.read()
            image = data.image.convert("RGBA")
            width, height = image.size
            if width < 20 or height < 20 or width > 1024 or height > 1024:
                continue
            similarity = score(reference_hist, reference_orange, image)
            if similarity < 0:
                continue
            ranked.append((similarity, obj.path_id, data.m_Name, image.copy()))
        except Exception:
            continue

    ranked.sort(key=lambda item: item[0], reverse=True)
    ranked = ranked[: args.limit]
    thumb_width, thumb_height = 180, 180
    sheet = Image.new("RGB", (thumb_width * 8, thumb_height * ((len(ranked) + 7) // 8)), "#d8ead0")
    draw = ImageDraw.Draw(sheet)
    report_rows = []
    for index, (similarity, path_id, name, image) in enumerate(ranked):
        thumbnail = image.copy()
        thumbnail.thumbnail((150, 135), Image.Resampling.LANCZOS)
        x = (index % 8) * thumb_width
        y = (index // 8) * thumb_height
        sheet.paste(thumbnail, (x + (thumb_width - thumbnail.width) // 2, y + 4), thumbnail)
        label = f"{index + 1}. {path_id}\n{name[:23]}\n{similarity:.3f}"
        draw.multiline_text((x + 4, y + 142), label, fill="black", spacing=1)
        report_rows.append(
            {
                "rank": index + 1,
                "similarity": round(similarity, 6),
                "path_id": path_id,
                "name": name,
                "size": list(image.size),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    args.report.write_text(
        json.dumps(
            {
                "bundle": str(args.bundle),
                "reference": str(args.reference),
                "sprite_count": sprite_count,
                "reference_orange_ratio": reference_orange,
                "ranked": report_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Audited {sprite_count} sprites; wrote {len(ranked)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
