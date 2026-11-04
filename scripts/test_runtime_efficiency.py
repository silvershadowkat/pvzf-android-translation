#!/usr/bin/env python3
"""Reproduce host translation parity/cache tests; never launches an Android app."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import zipfile

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('apk','work','jdk','android_jar'):
        ap.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    ap.add_argument('--dictionary',type=Path,help='Test a staged dictionary before APK packaging')
    ap.add_argument('--baseline-ref',default='49818776a1f2c0ddfa5da59bf67711a469b34a24',
                    help='Frozen source ref for the game version under test')
    ap.add_argument('--online-plantbrush',action='store_true',help='Use current 4.1 display fixtures instead of the legacy offline recognition census')
    a=ap.parse_args();r=Path(__file__).resolve().parents[1]
    a.work.mkdir(parents=True,exist_ok=True);classes=a.work/'classes';classes.mkdir(exist_ok=True)
    baseline=subprocess.run(['git','show',a.baseline_ref+':runtime/java/com/silvershadow/pvzf/EnglishActivity.java'],cwd=r,capture_output=True,check=True,timeout=30).stdout.decode('utf8')
    frozen=a.work/'BaselineEnglishActivity.java'
    frozen.write_text(baseline.replace('EnglishActivity','BaselineEnglishActivity'),encoding='utf8')
    with zipfile.ZipFile(a.apk) as z:payload=json.loads(z.read('assets/english/translations.json'))
    if a.dictionary:payload=json.loads(a.dictionary.read_text('utf8'))
    def encode(s):return base64.b64encode(s.encode('utf8')).decode('ascii')
    rows=['\t'.join(['E',encode(k),encode(v)]) for k,v in payload['exact'].items()]
    rows+=['\t'.join(['N',encode(v)]) for v in payload.get('recipe_names',[])]
    rows+=['\t'.join(['R',encode(k),encode(v)]) for k,v in payload['regex']]
    if a.online_plantbrush:
        rows+=['\t'.join(['C',encode(k),encode(v)]) for k,v in json.loads((r/'tests/fixtures/display-4.1.json').read_text('utf8')).items()]
    else:
        rows+=(r/'runtime/plantbrush/tests/plantbrush-display-census.tsv').read_text('utf8').splitlines()
    if not a.online_plantbrush:
        rows+=['\t'.join(['M',encode(c['source']),encode(c['previous']),encode(c['english'])]) for c in json.loads((r/'runtime/tests/modifier-display-cases.json').read_text('utf8'))]
    fixture=a.work/'payload.tsv';fixture.write_text('\n'.join(rows)+'\n',encoding='utf8')
    def run(stage,args):
        with (a.work/(stage+'.log')).open('w',encoding='utf8') as log:
            p=subprocess.run(list(map(str,args)),stdout=log,stderr=subprocess.STDOUT,timeout=120)
        if p.returncode:raise RuntimeError(stage+' failed: '+str(a.work/(stage+'.log')))
        print(stage+' passed',flush=True)
    cp=os.pathsep.join(map(str,[a.android_jar,classes]))
    run('compile',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-cp',cp,'-d',classes,*sorted((r/'runtime/java').rglob('*.java')),*sorted((r/'runtime/tests').glob('*.java')),r/'runtime/plantbrush/tests/PlantbrushTextTest.java',frozen])
    java=[a.jdk/'bin/java.exe','-XX:ActiveProcessorCount=2','-Xmx512m','-cp',cp]
    drawing_test=('PayloadTranslationTest',[fixture,a.work/'translated.tsv']) if a.online_plantbrush else ('PlantbrushTextTest',[fixture])
    # The 4.1 fixture file includes current original/mixed Gods cards. The three
    # hard-coded legacy modifier cases require the older game's exact wording.
    tests=[('RuntimeEfficiencyTest',[a.work]),('TranslationParityTest',[fixture]),('TranslationTest',[]),drawing_test]
    if not a.online_plantbrush:tests.append(('ModifierDisplayTest',[fixture]))
    tests.append(('ManagedFilesTest',[a.work]))
    for test,args in tests:
        run(test,java+[test,*args])

if __name__=='__main__':main()
