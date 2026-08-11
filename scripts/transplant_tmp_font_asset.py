#!/usr/bin/env python3
"""Transplant a TMP font asset, atlas, and material into stable target object IDs."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
from pathlib import Path

import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def object_map(env):
    return {(obj.assets_file.name, obj.path_id): obj for obj in env.objects}


def mono_name(obj) -> str:
    raw = bytes(obj.get_raw_data())
    size = int.from_bytes(raw[28:32], "little", signed=True)
    return raw[32 : 32 + size].decode("utf-8")


def find_named_mono(objects, name: str):
    matches = [obj for obj in objects.values() if obj.type.name == "MonoBehaviour" and mono_name(obj) == name]
    if len(matches) != 1:
        raise RuntimeError(f"expected one MonoBehaviour named {name!r}, found {len(matches)}")
    return matches[0]


def find_named_font(objects, name: str):
    matches = []
    for obj in objects.values():
        if obj.type.name == "Font" and obj.read().m_Name == name:
            matches.append(obj)
    if len(matches) != 1:
        raise RuntimeError(f"expected one Font named {name!r}, found {len(matches)}")
    return matches[0]


def remap_main_texture(material_tree: dict, atlas_path_id: int) -> None:
    for name, value in material_tree["m_SavedProperties"]["m_TexEnvs"]:
        if name == "_MainTex":
            value["m_Texture"] = {"m_FileID": 0, "m_PathID": atlas_path_id}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-bundle", required=True, type=Path)
    parser.add_argument("--donor-bundle", required=True, type=Path)
    parser.add_argument("--dummy-dll-dir", required=True, type=Path)
    parser.add_argument("--unity-version", default="2022.3.62f1")
    parser.add_argument("--donor-font-asset", required=True)
    parser.add_argument("--target-font-asset", action="append", required=True)
    parser.add_argument("--fallback-font-asset")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--packer", choices=("original", "lz4", "none"), default="original")
    args = parser.parse_args()

    generator = make_generator(args.unity_version, args.dummy_dll_dir)
    env = UnityPy.load(str(args.base_bundle))
    donor_env = UnityPy.load(str(args.donor_bundle))
    env.typetree_generator = generator
    donor_env.typetree_generator = generator
    objects = object_map(env)
    donor_objects = object_map(donor_env)

    donor_font_obj = find_named_mono(donor_objects, args.donor_font_asset)
    donor_font_tree = donor_font_obj.read_typetree(check_read=False)
    donor_material_id = donor_font_tree["material"]["m_PathID"]
    donor_atlas_id = donor_font_tree["m_AtlasTextures"][0]["m_PathID"]
    donor_material_obj = donor_objects[(donor_font_obj.assets_file.name, donor_material_id)]
    donor_atlas_obj = donor_objects[(donor_font_obj.assets_file.name, donor_atlas_id)]
    donor_material_tree = donor_material_obj.read_typetree()
    donor_atlas_tree = donor_atlas_obj.read_typetree()
    donor_atlas_data_hash = sha256(bytes(donor_atlas_obj.read().image_data))

    fallback_pointer = None
    if args.fallback_font_asset:
        fallback_obj = find_named_mono(objects, args.fallback_font_asset)
        fallback_pointer = {"m_FileID": 0, "m_PathID": fallback_obj.path_id}

    changes = []
    expected = {}
    for target_name in args.target_font_asset:
        target_font_obj = find_named_mono(objects, target_name)
        target_tree = target_font_obj.read_typetree(check_read=False)
        material_id = target_tree["material"]["m_PathID"]
        source_font_id = target_tree["m_SourceFontFile"]["m_PathID"]
        atlas_id = target_tree["m_AtlasTextures"][0]["m_PathID"]
        target_material_obj = objects[(target_font_obj.assets_file.name, material_id)]
        target_atlas_obj = objects[(target_font_obj.assets_file.name, atlas_id)]

        material_tree = copy.deepcopy(donor_material_tree)
        material_tree["m_Name"] = target_material_obj.read().m_Name
        material_tree["m_Shader"] = target_material_obj.read_typetree()["m_Shader"]
        remap_main_texture(material_tree, atlas_id)
        target_material_obj.save_typetree(material_tree)

        target_atlas_name = target_atlas_obj.read().m_Name
        atlas_tree = copy.deepcopy(donor_atlas_tree)
        atlas_tree["m_Name"] = target_atlas_name
        target_atlas_obj.save_typetree(atlas_tree)

        transplanted = copy.deepcopy(donor_font_tree)
        transplanted["m_GameObject"] = target_tree["m_GameObject"]
        transplanted["m_Enabled"] = target_tree["m_Enabled"]
        transplanted["m_Script"] = target_tree["m_Script"]
        transplanted["m_Name"] = target_tree["m_Name"]
        transplanted["material"] = {"m_FileID": 0, "m_PathID": material_id}
        transplanted["materialHashCode"] = target_tree["materialHashCode"]
        transplanted["m_SourceFontFile"] = {"m_FileID": 0, "m_PathID": source_font_id}
        transplanted["m_AtlasTextures"] = [{"m_FileID": 0, "m_PathID": atlas_id}]
        transplanted["m_AtlasTextureIndex"] = 0
        transplanted["m_IsMultiAtlasTexturesEnabled"] = 0
        if fallback_pointer is not None:
            transplanted["fallbackFontAssets"] = [fallback_pointer]
            transplanted["m_FallbackFontAssetTable"] = [fallback_pointer]
        target_font_obj.save_typetree(transplanted)

        expected[target_name] = {
            "font_asset_path_id": target_font_obj.path_id,
            "material_path_id": material_id,
            "atlas_path_id": atlas_id,
            "source_font_path_id": source_font_id,
            "glyph_count": len(donor_font_tree["m_GlyphTable"]),
            "character_count": len(donor_font_tree["m_CharacterTable"]),
            "atlas_data_sha256": donor_atlas_data_hash,
        }
        changes.append({"target_font_asset": target_name, **expected[target_name]})

    output_bytes = env.file.save(packer=None if args.packer == "none" else args.packer)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output_bytes)
    del output_bytes, env, donor_env
    gc.collect()

    check_generator = make_generator(args.unity_version, args.dummy_dll_dir)
    check_env = UnityPy.load(str(args.output))
    check_env.typetree_generator = check_generator
    check_objects = object_map(check_env)
    for name, wanted in expected.items():
        obj = find_named_mono(check_objects, name)
        tree = obj.read_typetree(check_read=False)
        if len(tree["m_GlyphTable"]) != wanted["glyph_count"] or len(tree["m_CharacterTable"]) != wanted["character_count"]:
            raise RuntimeError(f"TMP table validation failed for {name}")
        if tree["material"]["m_PathID"] != wanted["material_path_id"]:
            raise RuntimeError(f"TMP material validation failed for {name}")
        if tree["m_AtlasTextures"][0]["m_PathID"] != wanted["atlas_path_id"]:
            raise RuntimeError(f"TMP atlas pointer validation failed for {name}")
        atlas_obj = check_objects[(obj.assets_file.name, wanted["atlas_path_id"])]
        if sha256(bytes(atlas_obj.read().image_data)) != wanted["atlas_data_sha256"]:
            raise RuntimeError(f"TMP atlas data validation failed for {name}")
    del check_env
    gc.collect()

    report = {
        "format_version": 1,
        "base": {"path": str(args.base_bundle.resolve()), "sha256": sha256_file(args.base_bundle)},
        "donor": {"path": str(args.donor_bundle.resolve()), "sha256": sha256_file(args.donor_bundle)},
        "donor_font_asset": args.donor_font_asset,
        "output": {"path": str(args.output.resolve()), "size": args.output.stat().st_size, "sha256": sha256_file(args.output)},
        "validated_font_assets": len(expected),
        "changes": changes,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("output", "validated_font_assets", "changes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
