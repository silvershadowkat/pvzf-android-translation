#!/usr/bin/env python3
"""Promote the verified performance2 APKs with only manifest version changes.

Signing material stays local. Reports belong in audit documentation, not release
assets. Every non-signature entry other than the manifest must remain identical.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

from build_performance_candidate import CERT, manifest, sha
from package_apk_payload import copy_entry, is_old_signature

INPUTS = {
    'Standard': ('PvZ-Fusion-4.0.5-English-prerelease3.apk',
                 '33b1aaf004a3f13529e92dd2a2232b621abad5dc89f1304466da75a3183c1ba7',
                 'com.LanPiaoPiao.PlantsVsZombiesEN'),
    'AI': ('PvZ-Fusion-4.0.5-English-prerelease3-Experimental-AI.apk',
           '34158c00ce48c9bf8a85ac94ae52d5316957755fb132d0b56df38c254b701d53',
           'com.LanPiaoPiao.PlantsVsZombiesENAI'),
}
VERSION_CODE = 4050400
VERSION_NAME = '4.0.5-English-pre4'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('input', 'output', 'work', 'sdk', 'jdk', 'secret'):
        ap.add_argument('--' + key, type=Path, required=True)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    a.output.mkdir(parents=True, exist_ok=True)
    bt = a.sdk / 'build-tools/35.0.0'
    props = dict(line.split('=', 1) for line in
                 (a.secret / 'signing.properties').read_text('utf-8-sig').splitlines()
                 if '=' in line and not line.startswith('#'))
    env = os.environ.copy()
    env['PVZF_LOCAL_STORE_PASS'] = props['storepass']
    env['PVZF_LOCAL_KEY_PASS'] = props['keypass']
    signer = [a.jdk / 'bin/java.exe', '-XX:ActiveProcessorCount=2', '-Xmx512m',
              '-jar', bt / 'lib/apksigner.jar']

    def run(name, args):
        with (a.work / (name + '.log')).open('w', encoding='utf-8') as log:
            subprocess.run(list(map(str, args)), stdout=log, stderr=subprocess.STDOUT,
                           env=env, check=True, timeout=180)

    records = []
    for variant, (filename, digest, package) in INPUTS.items():
        source = a.input / filename
        assert sha(source) == digest, 'Unverified input APK: ' + variant
        output = a.output / ('PvZ-Fusion-4.0.5-English-prerelease4-' + variant + '.apk')
        assert not output.exists(), 'Refusing to replace an existing deliverable'
        unsigned = a.work / (variant + '-unsigned.apk')
        aligned = a.work / (variant + '-aligned.apk')
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(unsigned, 'w') as dst:
            for entry in src.infolist():
                if is_old_signature(entry.filename):
                    continue
                if entry.filename == 'AndroidManifest.xml':
                    dst.writestr(copy.copy(entry), manifest(src.read(entry), package,
                                                           VERSION_CODE, VERSION_NAME))
                else:
                    copy_entry(src, dst, entry)
        print(variant + ' repackaged', flush=True)
        run(variant + '-align', [bt / 'zipalign.exe', '-f', '-P', '16', '4', unsigned, aligned])
        run(variant + '-sign', signer + ['sign', '--ks', a.secret / 'PvZ-Fusion-English-Release.jks',
            '--ks-key-alias', props['alias'], '--ks-pass', 'env:PVZF_LOCAL_STORE_PASS',
            '--key-pass', 'env:PVZF_LOCAL_KEY_PASS', '--v4-signing-enabled', 'false',
            '--out', output, aligned])
        run(variant + '-signature', signer + ['verify', '--verbose', '--print-certs', output])
        assert CERT in (a.work / (variant + '-signature.log')).read_text('utf-8')
        run(variant + '-alignment', [bt / 'zipalign.exe', '-c', '-P', '16', '4', output])
        run(variant + '-manifest', [bt / 'aapt2.exe', 'dump', 'badging', output])
        badging = (a.work / (variant + '-manifest.log')).read_text('utf-8')
        assert "package: name='" + package + "'" in badging
        assert "versionCode='4050400'" in badging
        assert "versionName='4.0.5-English-pre4'" in badging
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(output) as dst:
            names = {n for n in src.namelist() if not is_old_signature(n)}
            assert names == {n for n in dst.namelist() if not is_old_signature(n)}
            assert dst.testzip() is None
            checked = 0
            for name in sorted(names - {'AndroidManifest.xml'}):
                with src.open(name) as x, dst.open(name) as y:
                    assert hashlib.file_digest(x, 'sha256').digest() == hashlib.file_digest(y, 'sha256').digest(), name
                checked += 1
            assert dst.read('AndroidManifest.xml') == manifest(src.read('AndroidManifest.xml'), package,
                                                               VERSION_CODE, VERSION_NAME)
        records.append(dict(filename=output.name, package=package, version_code=VERSION_CODE,
            version_name=VERSION_NAME, sha256=sha(output), size=output.stat().st_size,
            input_sha256=digest, certificate_sha256=CERT, unchanged_entries_verified=checked,
            only_manifest_version_and_signature_changed=True))
        print(variant + ' verified', flush=True)
    report = dict(date='2026-10-28', artifacts=records,
                  verification='Promoted verified performance2 payloads; no runtime, translation or save logic changes.')
    (a.work / 'prerelease4-build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
