"""Replace one reviewed UI image, gated by the exact original pixel hash."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import UnityPy
from PIL import Image
from apply_pc_texture_translations import pixel_sha256, mean_pixel_error
from polish_android_ui import object_map


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('source', 'image', 'output', 'report'):
        p.add_argument('--' + field, type=Path, required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--expected-source-pixels', required=True)
    a = p.parse_args()
    env = UnityPy.load(str(a.source))
    objects = object_map(env)
    expected = {key: hashlib.sha256(o.get_raw_data()).hexdigest() for key, o in objects.items()}
    matches = [(k, o) for k, o in objects.items() if o.type.name == 'Texture2D' and o.read().m_Name == a.name]
    assert len(matches) == 1
    key, obj = matches[0]
    tex = obj.read()
    assert pixel_sha256(tex.image) == a.expected_source_pixels
    image = Image.open(a.image).convert('RGBA')
    assert image.size == (tex.m_Width, tex.m_Height)
    before = mean_pixel_error(tex.image, image)
    tex.image = image
    obj.save_typetree(tex)
    expected[key] = hashlib.sha256(obj.data).hexdigest()
    a.output.write_bytes(env.file.save(packer='lz4'))
    del env, objects, obj, tex, matches
    gc.collect()
    check = object_map(UnityPy.load(str(a.output)))
    assert check.keys() == expected.keys()
    for k, o in check.items():
        assert hashlib.sha256(o.get_raw_data()).hexdigest() == expected[k], k
    after = mean_pixel_error(check[key].read().image, image)
    assert after < before and after < 8
    report = {'name': a.name, 'object': key, 'verified_objects': len(expected),
              'source_pixel_sha256': a.expected_source_pixels,
              'translation_file_sha256': hashlib.sha256(a.image.read_bytes()).hexdigest(),
              'mean_error_before': before, 'mean_error_after': after}
    a.report.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
