"""Measure and gain-match original/Blooms music; preserve paired-stem balance.

Emits reviewed PCM intermediates for Android Unity streaming import. Never changes
tempo, loop lengths or the relative gain of a base/drum pair. Processing is serial
and ffmpeg uses one thread. No APKs or player files are modified.
"""
import argparse, hashlib, json, math, re, subprocess
from pathlib import Path
import UnityPy
from UnityPy.helpers.ResourceReader import get_resource_data


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def measure(ffmpeg, files):
    args = [str(ffmpeg), '-nostdin', '-hide_banner', '-threads', '1']
    for path in files:
        args += ['-i', str(path)]
    audio = '[0:a]'
    filters = ''
    if len(files) == 2:
        filters = '[0:a][1:a]amix=inputs=2:normalize=0[mix];'
        audio = '[mix]'
    filters += audio + 'loudnorm=I=-18:TP=-2:LRA=11:print_format=json[analysis]'
    result = subprocess.run(args + ['-filter_complex_threads', '1', '-filter_complex', filters,
                                   '-map', '[analysis]', '-f', 'null', '-'],
                            capture_output=True, text=True, timeout=180, check=True)
    return json.loads(re.findall(r'\{[^{}]+"input_i"[^{}]+\}', result.stderr, re.S)[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('official-bundle', 'pc-audio', 'ffmpeg', 'decoder', 'work'):
        ap.add_argument('--' + key, type=Path, required=True)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    report_path = a.work / 'normalization.json'
    if report_path.exists():
        prior = json.loads(report_path.read_text(encoding='utf8'))
        if prior['official_bundle_sha256'] == sha(a.official_bundle) and all(
            sha(a.work / r['output']) == r['output_sha256'] and sha(Path(r['input'])) == r['input_sha256']
            for r in prior['tracks']):
            print('Existing normalized music verified', flush=True)
            return
        raise RuntimeError('Existing normalization differs; review in a fresh work directory')
    original = a.work / 'raw-original'
    original.mkdir(exist_ok=True)
    env = UnityPy.load(str(a.official_bundle))
    music_ids = set()
    for o in env.objects:
        if o.type.name == 'ResourceManager':
            for path, pointer in o.read_typetree()['m_Container']:
                if path.startswith('audio/music/') and path != 'audio/music/loon':
                    music_ids.add(pointer['m_PathID'])
    tracks = {}
    for o in env.objects:
        if o.type.name != 'AudioClip' or o.path_id not in music_ids or o.assets_file.name != 'resources.assets':
            continue
        clip = o.read()
        resource = clip.m_Resource
        bank = original / (clip.m_Name + '.fsb')
        with (a.official_bundle.parent / resource.m_Source).open('rb') as f:
            f.seek(resource.m_Offset)
            data = f.read(resource.m_Size)
        if len(data) != resource.m_Size or not data.startswith(b'FSB5'):
            raise RuntimeError('Invalid original music bank: ' + clip.m_Name)
        bank.write_bytes(data)
        path = original / (clip.m_Name + '.wav')
        subprocess.run([str(a.decoder), '-i', '-o', str(path), str(bank)], check=True,
                       stdout=subprocess.DEVNULL, timeout=90)
        tracks[clip.m_Name] = path
    del env
    profiles = {'original': tracks, 'blooms': {}}
    # The rhythm minigame suppresses PC replacements. Battle has no reviewed
    # replacement in the Android mapping. Preserve both through the game itself.
    for path in sorted(a.pc_audio.iterdir()):
        if path.suffix.lower() in ('.mp3', '.ogg', '.wav') and path.stem in tracks and path.stem not in ('Battle', 'loon'):
            profiles['blooms'][path.stem] = path
    output = a.work / 'normalized'
    output.mkdir(exist_ok=True)
    report = {'target_lufs': -18, 'true_peak_ceiling_db': -2,
              'method': 'Constant gain only, common gain per base/drum pair; no dynamic compression or tempo changes',
              'official_bundle_sha256': sha(a.official_bundle), 'groups': [], 'tracks': []}
    for profile, files in profiles.items():
        used = set()
        for name, path in sorted(files.items()):
            if name in used:
                continue
            base = name.removesuffix('_drum')
            members = [n for n in (base, base + '_drum') if n in files]
            if name not in members:
                members = [name]
            used.update(members)
            levels = measure(a.ffmpeg, [files[n] for n in members])
            loudness, peak = float(levels['input_i']), float(levels['input_tp'])
            # The PC Roof prelude is intentionally silent apart from MP3 noise.
            # Never amplify decoder noise by treating it as a quiet song.
            silent_prelude = profile == 'blooms' and name == 'Roof_pre' and loudness == -math.inf and peak < -70
            if not silent_prelude and not (-100 < loudness < 10 and -100 < peak < 20):
                raise RuntimeError('Invalid/silent music measurement: ' + name)
            gain = 0 if silent_prelude else min(-18 - loudness, -2 - peak)
            report['groups'].append({'profile': profile, 'members': members, 'input_lufs': None if silent_prelude else loudness,
                                     'input_true_peak_db': None if silent_prelude else peak, 'gain_db': gain,
                                     'expected_lufs': None if silent_prelude else loudness + gain,
                                     'expected_true_peak_db': None if silent_prelude else peak + gain,
                                     'intentional_silent_prelude': silent_prelude})
            for n in members:
                dest = output / (profile + '__' + n + '.wav')
                subprocess.run([str(a.ffmpeg), '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                                '-threads', '1', '-i', str(files[n]), '-filter_threads', '1', '-af', f'volume={gain:.6f}dB',
                                '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', str(dest)],
                               timeout=180, check=True)
                report['tracks'].append({'profile': profile, 'name': n, 'input': str(files[n].resolve()),
                                         'input_sha256': sha(files[n]), 'output': dest.relative_to(a.work).as_posix(),
                                         'output_sha256': sha(dest), 'gain_db': gain})
            print(profile, ', '.join(members), f'{loudness:.2f} LUFS -> {loudness+gain:.2f} LUFS', flush=True)
            (a.work / 'normalization-in-progress.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('Normalized tracks:', len(report['tracks']), flush=True)


if __name__ == '__main__':
    main()
