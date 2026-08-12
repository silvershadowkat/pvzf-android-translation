#!/usr/bin/env python3
"""Bake Android-port credits into the Help parchment and disable its live overlay."""

from __future__ import annotations

import argparse
import gc
import hashlib
import io
import json
from pathlib import Path

import UnityPy
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


HELP_TEXTURE_PATH_ID = 2199
HANDWRITING_FONT_PATH_ID = 6493
PORT_CREDITS_COMPONENT_PATH_ID = 179902
CREDIT_TEXT = "Joseph Franci  ·  aha  ·  SilverShadow  ·  Codex"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def make_generator(unity_version: str, dummy_dll_dir: Path) -> TypeTreeGenerator:
    generator = TypeTreeGenerator(unity_version)
    generator.load_local_dll_folder(str(dummy_dll_dir))
    return generator


def render_credit(texture: Image.Image, font_bytes: bytes) -> Image.Image:
    """Replace Joseph's baked line with the complete, consistently styled credit."""
    image = texture.convert("RGBA")
    pixels = image.load()
    x0, y0, x1, y1 = 238, 493, 410, 532

    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((x0, y0, x1, y1), radius=4, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(5.0))

    fill = image.copy()
    fill_pixels = fill.load()
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        for x in range(x0, x1):
            top_samples = [pixels[x, sy][:3] for sy in range(446, 458)]
            bottom_samples = [pixels[x, sy][:3] for sy in range(536, 544)]
            top = tuple(sum(c[i] for c in top_samples) / len(top_samples) for i in range(3))
            bottom = tuple(sum(c[i] for c in bottom_samples) / len(bottom_samples) for i in range(3))
            color = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            fill_pixels[x, y] = (*color, 255)
    image = Image.composite(fill, image, mask)

    font = ImageFont.truetype(io.BytesIO(font_bytes), size=20)
    ImageDraw.Draw(image).text((250, 495), CREDIT_TEXT, font=font, fill=(15, 15, 10, 255))
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    env.typetree_generator = generator
    objects = {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}

    texture_obj = objects[("resources.assets", HELP_TEXTURE_PATH_ID)]
    texture = texture_obj.read()
    if texture.m_Name != "thanks" or (texture.m_Width, texture.m_Height) != (1400, 600):
        raise RuntimeError("Help parchment texture identity changed")
    texture_before = {
        "name": texture.m_Name,
        "width": texture.m_Width,
        "height": texture.m_Height,
        "format": int(texture.m_TextureFormat),
    }
    font_obj = objects[("resources.assets", HANDWRITING_FONT_PATH_ID)]
    font = font_obj.read()
    if font.m_Name != "fzjz":
        raise RuntimeError("Embedded parchment handwriting Font identity changed")
    font_bytes = bytes(font.m_FontData)
    replacement = render_credit(texture.image, font_bytes)
    if replacement.size != (1400, 600):
        raise RuntimeError(f"Help texture must remain 1400x600, got {replacement.size}")
    texture.image = replacement
    texture_obj.save_typetree(texture)

    credit_obj = objects[("resources.assets", PORT_CREDITS_COMPONENT_PATH_ID)]
    credit_tree = credit_obj.read_typetree(check_read=False)
    overlay_before = credit_tree["m_text"]
    credit_tree["m_text"] = "   "
    credit_obj.save_typetree(credit_tree)

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    check_env = UnityPy.load(str(args.output))
    check_env.typetree_generator = generator
    check_objects = {(obj.assets_file.name, obj.path_id): obj for obj in check_env.objects}
    check_texture = check_objects[("resources.assets", HELP_TEXTURE_PATH_ID)].read()
    check_overlay = check_objects[("resources.assets", PORT_CREDITS_COMPONENT_PATH_ID)].read_typetree(
        check_read=False
    )["m_text"]
    if check_texture.m_Name != "thanks" or (check_texture.m_Width, check_texture.m_Height) != (1400, 600):
        raise RuntimeError("Reopened Help parchment failed identity validation")
    if check_overlay.strip():
        raise RuntimeError("Live Android-port credit overlay is still enabled")

    args.preview.parent.mkdir(parents=True, exist_ok=True)
    check_texture.image.save(args.preview)
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "render": {
            "text": CREDIT_TEXT,
            "font_path_id": HANDWRITING_FONT_PATH_ID,
            "font_name": font.m_Name,
            "font_data_sha256": hashlib.sha256(font_bytes).hexdigest(),
            "font_size": 20,
            "position": [250, 495],
            "width": replacement.width,
            "height": replacement.height,
        },
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "preview": {"path": str(args.preview.resolve()), "sha256": sha256_file(args.preview)},
        "texture": {"path_id": HELP_TEXTURE_PATH_ID, "before": texture_before},
        "disabled_overlay": {
            "path_id": PORT_CREDITS_COMPONENT_PATH_ID,
            "before": overlay_before,
            "after": "   ",
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
