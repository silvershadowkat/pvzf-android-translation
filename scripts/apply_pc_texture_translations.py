#!/usr/bin/env python3
"""Bake validated PC English particle textures into the Android Unity bundle.

The PC translator replaces assets dynamically by exact asset name. Android does
not run that translator, so the equivalent PNGs must be serialized into
``data.unity3d``. This pass is deliberately narrow: it audits the complete PC
English texture catalog, but only writes the eight confirmed particle effects.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy
from PIL import Image, ImageChops, ImageStat


PARTICLE_NAMES = (
    "Dong",
    "Doom",
    "ExplosionPowie",
    "ExplosionSpudow",
    "guang",
    "Pow",
    "Sproing",
    "SunExplosionPowie",
)

# These exact-name PC textures intentionally remain outside this pass.
PRESERVE_REASONS = {
    "Logo/Logo3.6.png": "versioned PC 3.6 logo is unsuitable for Android 3.8.1",
    "Menu/thanks.png": "preserve the approved Android credits parchment",
    "Menu/\u6df1\u6e0a\u5165\u53e3.png": "Abyss is parked and must remain untouched",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def pixel_sha256(image: Image.Image) -> str:
    return hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest()


def mean_pixel_error(left: Image.Image, right: Image.Image) -> float:
    if left.size != right.size:
        raise ValueError(f"image size mismatch: {left.size} != {right.size}")
    difference = ImageChops.difference(left.convert("RGBA"), right.convert("RGBA"))
    return sum(ImageStat.Stat(difference).mean) / 4.0


def find_named_objects(env: UnityPy.Environment, type_name: str) -> dict[str, list[object]]:
    found: dict[str, list[object]] = {}
    for obj in env.objects:
        if obj.type.name != type_name:
            continue
        data = obj.read()
        found.setdefault(data.m_Name, []).append(obj)
    return found


def audit_catalog(
    texture_root: Path,
    texture_objects: dict[str, list[object]],
) -> list[dict[str, object]]:
    audit: list[dict[str, object]] = []
    for source_path in sorted(texture_root.rglob("*.png")):
        relative = source_path.relative_to(texture_root).as_posix()
        source = Image.open(source_path).convert("RGBA")
        matches = texture_objects.get(source_path.stem, [])
        item: dict[str, object] = {
            "source": relative,
            "source_size": list(source.size),
            "source_sha256": sha256_file(source_path),
            "target_count": len(matches),
        }
        if len(matches) == 1:
            target = matches[0].read()
            target_size = (target.m_Width, target.m_Height)
            item.update(
                {
                    "target_path_id": matches[0].path_id,
                    "target_size": list(target_size),
                    "dimensions_match": target_size == source.size,
                }
            )
            if target_size == source.size:
                error = mean_pixel_error(source, target.image)
                item["mean_pixel_error_before"] = round(error, 4)
                if relative in PRESERVE_REASONS:
                    item["classification"] = "preserved"
                    item["reason"] = PRESERVE_REASONS[relative]
                elif relative == f"Particles/{source_path.name}":
                    item["classification"] = "particle_translation"
                elif error <= 7.0:
                    item["classification"] = "already_localized_or_compression_only"
                else:
                    item["classification"] = "manual_review_required"
        audit.append(item)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--pc-texture-root", required=True, type=Path)
    parser.add_argument("--pc-sprite-particles", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    env = UnityPy.load(str(args.base_bundle))
    texture_objects = find_named_objects(env, "Texture2D")
    sprite_objects = find_named_objects(env, "Sprite")
    catalog_audit = audit_catalog(args.pc_texture_root, texture_objects)

    review_required = [
        item for item in catalog_audit if item.get("classification") == "manual_review_required"
    ]
    if review_required:
        names = [str(item["source"]) for item in review_required]
        raise RuntimeError(f"unclassified PC texture differences require review: {names}")

    applied: list[dict[str, object]] = []
    for name in PARTICLE_NAMES:
        texture_source_path = args.pc_texture_root / "Particles" / f"{name}.png"
        sprite_source_path = args.pc_sprite_particles / f"{name}.png"
        if not texture_source_path.is_file() or not sprite_source_path.is_file():
            raise FileNotFoundError(f"missing paired PC particle sources for {name}")

        texture_source = Image.open(texture_source_path).convert("RGBA")
        sprite_source = Image.open(sprite_source_path).convert("RGBA")
        if texture_source.size != sprite_source.size or pixel_sha256(texture_source) != pixel_sha256(
            sprite_source
        ):
            raise RuntimeError(f"PC Texture/Sprite particle sources disagree for {name}")

        targets = texture_objects.get(name, [])
        sprites = sprite_objects.get(name, [])
        if len(targets) != 1 or len(sprites) != 1:
            raise RuntimeError(
                f"expected one Android Texture2D and Sprite named {name}, "
                f"found textures={len(targets)}, sprites={len(sprites)}"
            )
        texture_obj = targets[0]
        sprite_obj = sprites[0]
        texture = texture_obj.read()
        sprite = sprite_obj.read()
        target_size = (texture.m_Width, texture.m_Height)
        if target_size != texture_source.size:
            raise RuntimeError(
                f"Android/PC dimensions differ for {name}: {target_size} != {texture_source.size}"
            )
        sprite_texture_path_id = sprite.m_RD.texture.path_id
        if sprite_texture_path_id != texture_obj.path_id:
            raise RuntimeError(
                f"Sprite {name} does not reference its same-name Texture2D: "
                f"{sprite_texture_path_id} != {texture_obj.path_id}"
            )

        before_error = mean_pixel_error(texture_source, texture.image)
        texture_format = int(texture.m_TextureFormat)
        texture.image = texture_source
        texture_obj.save_typetree(texture)
        applied.append(
            {
                "name": name,
                "texture_path_id": texture_obj.path_id,
                "sprite_path_id": sprite_obj.path_id,
                "dimensions": list(texture_source.size),
                "texture_format": texture_format,
                "source": str(texture_source_path.resolve()),
                "source_sha256": sha256_file(texture_source_path),
                "mean_pixel_error_before": round(before_error, 4),
            }
        )

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env
    gc.collect()

    check_env = UnityPy.load(str(args.output))
    check_textures = find_named_objects(check_env, "Texture2D")
    check_sprites = find_named_objects(check_env, "Sprite")
    for record in applied:
        name = str(record["name"])
        source = Image.open(args.pc_texture_root / "Particles" / f"{name}.png").convert("RGBA")
        texture_obj = check_textures[name][0]
        texture = texture_obj.read()
        sprite = check_sprites[name][0].read()
        if (texture.m_Width, texture.m_Height) != source.size:
            raise RuntimeError(f"reopened dimensions changed for {name}")
        if sprite.m_RD.texture.path_id != texture_obj.path_id:
            raise RuntimeError(f"reopened Sprite linkage changed for {name}")
        after_error = mean_pixel_error(source, texture.image)
        record["mean_pixel_error_after"] = round(after_error, 4)
        if after_error >= float(record["mean_pixel_error_before"]) or after_error > 8.0:
            raise RuntimeError(
                f"reopened texture validation failed for {name}: "
                f"before={record['mean_pixel_error_before']}, after={after_error:.4f}"
            )
    del check_env
    gc.collect()

    classifications: dict[str, int] = {}
    for item in catalog_audit:
        classification = str(item.get("classification", "no_exact_target"))
        classifications[classification] = classifications.get(classification, 0) + 1

    report = {
        "format_version": 1,
        "base": {
            "path": str(args.base_bundle.resolve()),
            "sha256": sha256_file(args.base_bundle),
        },
        "pc_texture_root": str(args.pc_texture_root.resolve()),
        "catalog_summary": {
            "pc_png_count": len(catalog_audit),
            "classifications": dict(sorted(classifications.items())),
        },
        "catalog_audit": catalog_audit,
        "applied_particle_textures": applied,
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "catalog_summary": report["catalog_summary"],
                "applied": [record["name"] for record in applied],
                "output": report["output"],
                "report": str(args.report),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
