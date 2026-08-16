#!/usr/bin/env python3
"""Bake validated PC English textures into the Android Unity bundle.

The PC translator replaces assets dynamically by exact asset name. Android does
not run that translator, so the equivalent PNGs must be serialized into
``data.unity3d``. This pass is deliberately narrow: it audits the complete PC
English texture catalog. Particle effects also receive a full-rectangle Sprite
mesh because English lettering can extend beyond the original Chinese mesh.
Other compatible textures are written only when name and dimensions match one
unique Android Texture2D exactly. Every such validated match is baked from the
canonical PC source: whole-canvas pixel averages are not reliable localization
detectors because a few untranslated glyphs can occupy a tiny transparent area.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import struct
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
    "Menu/深渊入口.png": "Abyss is parked and must remain untouched",
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


def expand_sprite_to_full_rect(sprite: object, width: int, height: int) -> None:
    """Replace a retained tight Chinese mesh with a full rectangular quad.

    The PC English particle art does not share the outline of the original
    Chinese glyphs. Replacing only Texture2D pixels therefore leaves parts of
    the English letters outside the serialized tight mesh. A transparent full
    quad preserves every source pixel while retaining the original pivot, PPU,
    texture linkage, and overall 2D canvas.
    """

    if round(sprite.m_Rect.width) != width or round(sprite.m_Rect.height) != height:
        raise RuntimeError(
            f"Sprite {sprite.m_Name} canvas differs from its texture: "
            f"{sprite.m_Rect.width}x{sprite.m_Rect.height} != {width}x{height}"
        )

    ppu = float(sprite.m_PixelsToUnits)
    pivot_x = float(sprite.m_Pivot.x)
    pivot_y = float(sprite.m_Pivot.y)
    left = -(pivot_x * width) / ppu
    right = ((1.0 - pivot_x) * width) / ppu
    bottom = -(pivot_y * height) / ppu
    top = ((1.0 - pivot_y) * height) / ppu
    positions = (
        (left, top, 0.0),
        (right, top, 0.0),
        (left, bottom, 0.0),
        (right, bottom, 0.0),
    )

    render_data = sprite.m_RD
    vertex_data = render_data.m_VertexData
    vertex_data.m_VertexCount = 4
    # Unity stores the position stream first, followed by an unused UV stream.
    vertex_data.m_DataSize = b"".join(
        struct.pack("<3f", *position) for position in positions
    ) + bytes(32)
    render_data.m_IndexBuffer = struct.pack("<6H", 0, 1, 2, 2, 1, 3)
    if not render_data.m_SubMeshes:
        raise RuntimeError(f"Sprite {sprite.m_Name} has no serialized submesh")
    submesh = render_data.m_SubMeshes[0]
    submesh.firstByte = 0
    submesh.firstVertex = 0
    submesh.indexCount = 6
    submesh.vertexCount = 4
    submesh.baseVertex = 0
    submesh.topology = 0
    render_data.m_SubMeshes = [submesh]

    render_data.textureRect.x = 0.0
    render_data.textureRect.y = 0.0
    render_data.textureRect.width = float(width)
    render_data.textureRect.height = float(height)
    render_data.textureRectOffset.x = 0.0
    render_data.textureRectOffset.y = 0.0
    render_data.uvTransform.x = ppu
    render_data.uvTransform.y = width / 2.0
    render_data.uvTransform.z = ppu
    render_data.uvTransform.w = height / 2.0
    render_data.settingsRaw &= ~64  # SpriteMeshType.Tight -> FullRect


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
    parser.add_argument(
        "--apply-compatible-catalog",
        action="store_true",
        help="also apply non-particle PC textures with unique exact-name/dimension matches",
    )
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    env = UnityPy.load(str(args.base_bundle))
    texture_objects = find_named_objects(env, "Texture2D")
    sprite_objects = find_named_objects(env, "Sprite")
    catalog_audit = audit_catalog(args.pc_texture_root, texture_objects)

    review_required = [
        item for item in catalog_audit if item.get("classification") == "manual_review_required"
    ]
    if review_required and not args.apply_compatible_catalog:
        names = [str(item["source"]) for item in review_required]
        raise RuntimeError(f"unclassified PC texture differences require review: {names}")

    applied: list[dict[str, object]] = []
    applied_catalog_textures: list[dict[str, object]] = []
    if args.apply_compatible_catalog:
        for item in review_required:
            source_path = args.pc_texture_root / str(item["source"])
            source = Image.open(source_path).convert("RGBA")
            targets = texture_objects.get(source_path.stem, [])
            if len(targets) != 1:
                continue
            texture_obj = targets[0]
            texture = texture_obj.read()
            target_size = (texture.m_Width, texture.m_Height)
            if target_size != source.size:
                continue
            before_error = mean_pixel_error(source, texture.image)
            texture_format = int(texture.m_TextureFormat)
            texture.image = source
            texture_obj.save_typetree(texture)
            item["classification"] = "compatible_translation"
            applied_catalog_textures.append(
                {
                    "name": source_path.stem,
                    "relative_source": str(item["source"]),
                    "texture_path_id": texture_obj.path_id,
                    "dimensions": list(source.size),
                    "texture_format": texture_format,
                    "source_sha256": sha256_file(source_path),
                    "mean_pixel_error_before": round(before_error, 4),
                }
            )

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
        expand_sprite_to_full_rect(sprite, *texture_source.size)
        sprite_obj.save_typetree(sprite)
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
                "sprite_mesh": "full_rect",
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
    for record in applied_catalog_textures:
        source = Image.open(
            args.pc_texture_root / str(record["relative_source"])
        ).convert("RGBA")
        texture = check_textures[str(record["name"])][0].read()
        after_error = mean_pixel_error(source, texture.image)
        record["mean_pixel_error_after"] = round(after_error, 4)
        if after_error >= float(record["mean_pixel_error_before"]) or after_error > 8.0:
            raise RuntimeError(
                f"reopened texture validation failed for {record['relative_source']}: "
                f"before={record['mean_pixel_error_before']}, after={after_error:.4f}"
            )
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
        if sprite.m_RD.settingsRaw & 64:
            raise RuntimeError(f"reopened Sprite still uses a tight mesh for {name}")
        if sprite.m_RD.m_VertexData.m_VertexCount != 4:
            raise RuntimeError(f"reopened Sprite is not a four-vertex quad for {name}")
        sprite_image = sprite.image.convert("RGBA")
        if sprite_image.size != source.size:
            raise RuntimeError(
                f"reopened Sprite canvas changed for {name}: {sprite_image.size} != {source.size}"
            )
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
        "applied_compatible_textures": applied_catalog_textures,
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
                "applied_compatible": [
                    record["relative_source"] for record in applied_catalog_textures
                ],
                "applied": [record["name"] for record in applied],
                "output": report["output"],
                "report": str(args.report),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
