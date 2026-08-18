#!/usr/bin/env python3
"""Carry unchanged 3.8.1 translated textures into a newer Android bundle."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path

import UnityPy

from apply_pc_texture_translations import (
    expand_sprite_to_full_rect,
    mean_pixel_error,
    pixel_sha256,
)


# TMP font atlases are not ordinary localized artwork. Their pixels are indexed
# by the matching font asset's glyph and character tables and are also coupled
# to a material. Copying only an old atlas into a newer bundle scrambles every
# component that uses the newer tables. Font changes must go through the full
# font transplant pipeline instead.
FONT_ATLAS_SUFFIX = " atlas"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def named_objects(env: UnityPy.Environment, type_name: str) -> dict[str, list[object]]:
    result: dict[str, list[object]] = {}
    for obj in env.objects:
        if obj.type.name != type_name:
            continue
        result.setdefault(obj.read().m_Name, []).append(obj)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--previous-source-bundle", required=True, type=Path)
    parser.add_argument("--previous-translated-bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    env = UnityPy.load(str(args.base_bundle))
    previous_source_env = UnityPy.load(str(args.previous_source_bundle))
    previous_translated_env = UnityPy.load(str(args.previous_translated_bundle))

    current_textures = named_objects(env, "Texture2D")
    source_textures = named_objects(previous_source_env, "Texture2D")
    translated_textures = named_objects(previous_translated_env, "Texture2D")
    current_sprites = named_objects(env, "Sprite")
    source_sprites = named_objects(previous_source_env, "Sprite")
    translated_sprites = named_objects(previous_translated_env, "Sprite")

    applied: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []
    validation_images: dict[str, object] = {}
    candidate_names = sorted(set(source_textures) & set(translated_textures))
    for name in candidate_names:
        if name.casefold().endswith(FONT_ATLAS_SUFFIX):
            skipped.append({"name": name, "reason": "font_atlas_requires_dependency_transplant"})
            continue
        source_matches = source_textures[name]
        translated_matches = translated_textures[name]
        current_matches = current_textures.get(name, [])
        if len(source_matches) != 1 or len(translated_matches) != 1:
            continue
        source = source_matches[0].read()
        translated = translated_matches[0].read()
        source_hash = pixel_sha256(source.image)
        translated_hash = pixel_sha256(translated.image)
        if source_hash == translated_hash:
            continue
        if len(current_matches) != 1:
            skipped.append({"name": name, "reason": "target_not_unique", "target_count": len(current_matches)})
            continue
        current_obj = current_matches[0]
        current = current_obj.read()
        if (source.m_Width, source.m_Height) != (translated.m_Width, translated.m_Height):
            skipped.append({"name": name, "reason": "previous_translation_dimensions_changed"})
            continue
        if (current.m_Width, current.m_Height) != (source.m_Width, source.m_Height):
            skipped.append({"name": name, "reason": "target_dimensions_changed"})
            continue
        current_hash = pixel_sha256(current.image)
        if current_hash != source_hash:
            skipped.append(
                {
                    "name": name,
                    "reason": "official_3.9_pixels_changed",
                    "previous_source_pixel_sha256": source_hash,
                    "current_pixel_sha256": current_hash,
                }
            )
            continue

        texture_format = int(current.m_TextureFormat)
        before_error = mean_pixel_error(translated.image, current.image)
        current.image = translated.image.convert("RGBA")
        current_obj.save_typetree(current)
        validation_images[name] = translated.image.convert("RGBA").copy()

        sprite_mesh_expanded = False
        old_source_sprites = source_sprites.get(name, [])
        old_translated_sprites = translated_sprites.get(name, [])
        target_sprites = current_sprites.get(name, [])
        if (
            len(old_source_sprites) == 1
            and len(old_translated_sprites) == 1
            and len(target_sprites) == 1
            and bytes(old_source_sprites[0].get_raw_data())
            != bytes(old_translated_sprites[0].get_raw_data())
        ):
            target_sprite = target_sprites[0].read()
            expand_sprite_to_full_rect(target_sprite, current.m_Width, current.m_Height)
            target_sprites[0].save_typetree(target_sprite)
            sprite_mesh_expanded = True

        applied.append(
            {
                "name": name,
                "texture_path_id": current_obj.path_id,
                "dimensions": [current.m_Width, current.m_Height],
                "texture_format": texture_format,
                "previous_source_pixel_sha256": source_hash,
                "translated_pixel_sha256": translated_hash,
                "mean_pixel_error_before": round(before_error, 4),
                "sprite_mesh_expanded": sprite_mesh_expanded,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(env.file.save(packer=None if args.packer == "none" else args.packer))
    del env, previous_source_env, previous_translated_env
    gc.collect()

    check_env = UnityPy.load(str(args.output))
    check_textures = named_objects(check_env, "Texture2D")
    for record in applied:
        matches = check_textures.get(str(record["name"]), [])
        if len(matches) != 1:
            raise RuntimeError(f"translated texture vanished: {record['name']}")
        after_error = mean_pixel_error(
            validation_images[str(record["name"])],
            matches[0].read().image,
        )
        record["mean_pixel_error_after"] = round(after_error, 4)
        if after_error >= float(record["mean_pixel_error_before"]) or after_error > 8.0:
            raise RuntimeError(
                f"translated texture validation failed for {record['name']}: "
                f"before={record['mean_pixel_error_before']}, after={after_error:.4f}"
            )
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "previous_source": {
            "path": str(args.previous_source_bundle.resolve()),
            "sha256": sha256_file(args.previous_source_bundle),
        },
        "previous_translated": {
            "path": str(args.previous_translated_bundle.resolve()),
            "sha256": sha256_file(args.previous_translated_bundle),
        },
        "output": {
            "path": str(args.output.resolve()),
            "size": args.output.stat().st_size,
            "sha256": sha256_file(args.output),
        },
        "applied_count": len(applied),
        "applied": applied,
        "skipped_changed_or_ambiguous_count": len(skipped),
        "skipped": skipped,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": report["output"],
                "applied_count": len(applied),
                "applied_names": [record["name"] for record in applied],
                "skipped_count": len(skipped),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
