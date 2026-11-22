"""Build an ARM64-only startup experiment over immutable EN pre7.

This probe is for an isolated test installation. It does not install, publish,
change a release, or include the experiment in ordinary runtime builds.
"""
import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from apply_41_prerelease4 import file_sha, write
from build_41_prerelease4 import audit_apk, CERT
from package_apk_payload import copy_entry, is_old_signature

BASE = 'dbfb2d9b5666aa52d3a441e28bbe659073dcff4cf597302a4fa2754dbf4d8e2e'
LIB = 'lib/arm64-v8a/libpvzfenglish.so'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('base', 'work', 'output', 'sdk', 'jdk', 'secret', 'dobby'):
        p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args()
    assert file_sha(a.base) == BASE, 'Requires the exact public EN pre7 base'
    assert a.output.resolve() != a.base.resolve(), 'Never overwrite the release'
    a.work.mkdir(parents=True, exist_ok=True); a.output.parent.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]; src = a.work / 'runtime'; src.mkdir(exist_ok=True)
    for f in (root / 'runtime').iterdir():
        if f.is_file(): shutil.copy2(f, src / f.name)
    for n in ('startup_bench.inc', 'lazy_ui_candidate.inc'):
        shutil.copy2(root / 'runtime/diagnostics' / n, src / n)
    source = (src / 'english.cpp').read_text('utf8')
    replacements = {
        'static void update(P o,M m){': 'static void benchTick();\nstatic void update(P o,M m){',
        '    oldUpdate(o,m);': '    oldUpdate(o,m);\n    benchTick();',
        'static void initialize(){': '#include "startup_bench.inc"\nstatic void initialize(){\n    initializeStartupBench();',
    }
    for old, new in replacements.items():
        assert source.count(old) == 1, 'Runtime changed; review the probe injection'
        source = source.replace(old, new)
    (src / 'english.cpp').write_text(source, 'utf8')
    logs = a.work / 'logs'; logs.mkdir(exist_ok=True)
    def run(n, args, timeout=180, env=None):
        with (logs / (n + '.log')).open('w', encoding='utf8') as f:
            result = subprocess.run(list(map(str, args)), stdout=f, stderr=subprocess.STDOUT, timeout=timeout, env=env)
        if result.returncode: raise RuntimeError(n + ' failed; inspect ' + str(logs / (n + '.log')))
        print(n + ' passed', flush=True)
    cm = a.sdk / 'cmake/3.22.1/bin/cmake.exe'; build = a.work / 'native'
    run('configure', [cm, '-S', src, '-B', build, '-G', 'Ninja',
        '-DCMAKE_MAKE_PROGRAM=' + str(a.sdk / 'cmake/3.22.1/bin/ninja.exe'),
        '-DCMAKE_TOOLCHAIN_FILE=' + str(a.sdk / 'ndk/25.2.9519653/build/cmake/android.toolchain.cmake'),
        '-DANDROID_ABI=arm64-v8a', '-DANDROID_PLATFORM=android-22', '-DCMAKE_BUILD_TYPE=Release',
        '-DANDROID_STL=c++_static', '-DDOBBY_SOURCE=' + str(a.dobby)])
    run('compile', [cm, '--build', build, '--target', 'pvzfenglish', '--parallel', '2'], 240)
    unsigned = a.work / 'unsigned.apk'; aligned = a.work / 'aligned.apk'
    with zipfile.ZipFile(a.base) as z, zipfile.ZipFile(unsigned, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as out:
        for info in z.infolist():
            if is_old_signature(info.filename): continue
            if info.filename == LIB: out.writestr(copy.copy(info), (build / 'libpvzfenglish.so').read_bytes())
            else: copy_entry(z, out, info)
    bt = a.sdk / 'build-tools/35.0.0'; run('align', [bt / 'zipalign.exe', '-f', '-P', '16', '4', unsigned, aligned])
    props = {}
    for line in (a.secret / 'signing.properties').read_text('utf-8-sig').splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1); props[k.strip()] = v.strip()
    env = os.environ.copy(); env['PVZF_STORE_PASS'] = props['storepass']; env['PVZF_KEY_PASS'] = props['keypass']
    signer = [a.jdk / 'bin/java.exe', '-XX:ActiveProcessorCount=2', '-Xmx512m', '-jar', bt / 'lib/apksigner.jar']
    run('sign', signer + ['sign', '--ks', a.secret / 'PvZ-Fusion-English-Release.jks', '--ks-key-alias', props['alias'],
        '--ks-pass', 'env:PVZF_STORE_PASS', '--key-pass', 'env:PVZF_KEY_PASS', '--v4-signing-enabled', 'false',
        '--out', a.output, aligned], env=env)
    del props, env
    run('verify', signer + ['verify', '--verbose', '--print-certs', a.output])
    assert CERT in (logs / 'verify.log').read_text()
    run('alignment', [bt / 'zipalign.exe', '-c', '-P', '16', '4', a.output])
    changed = audit_apk(a.base, a.output, {LIB}, {LIB})
    write(a.work / 'BUILD.json', dict(apk=str(a.output), sha256=file_sha(a.output), base_sha256=BASE,
        diagnostic=True, experiment_abi='arm64-v8a', changed_entries=changed,
        other_entries_identical=True, source_files={n: file_sha(src / n) for n in ('english.cpp', 'startup_bench.inc', 'lazy_ui_candidate.inc')},
        certificate_sha256=CERT, installed=False, published=False,
        limitations=['Experimental owner tracking and fallback need production hardening before a release.',
                     'No 32-bit experiment or physical-device validation.']))


if __name__ == '__main__': main()
