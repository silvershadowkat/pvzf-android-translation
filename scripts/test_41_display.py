"""Run real Java display fixtures against a staged 4.1 dictionary, offline."""
import argparse, base64, json, os, subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('dictionary','work','jdk','android-jar'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=Path(__file__).resolve().parents[1];a.work.mkdir(parents=True,exist_ok=True)
    classes=a.work/'classes';classes.mkdir(exist_ok=True)
    d=json.loads(a.dictionary.read_text(encoding='utf8'))
    def enc(s):return base64.b64encode(s.encode('utf8')).decode('ascii')
    rows=['\t'.join(('E',enc(k),enc(v))) for k,v in d['exact'].items()]
    rows+=['\t'.join(('N',enc(v))) for v in d['recipe_names']]
    rows+=['\t'.join(('R',enc(k),enc(v))) for k,v in d['regex']]
    fixtures=json.loads((r/'tests/fixtures/display-4.1.json').read_text(encoding='utf8'))
    rows+=['\t'.join(('C',enc(k),enc(v))) for k,v in fixtures.items()]
    fixture=a.work/'payload.tsv';fixture.write_text('\n'.join(rows)+'\n',encoding='utf8')
    sources=[r/'runtime/java/com/silvershadow/pvzf'/(s+'.java') for s in
             ('EnglishActivity','EnglishApplication','ProcessStartGate','ManagedFiles','BoundedTextCache','RegexPrefix','PlantbrushTranslations')]
    tests=['PayloadTranslationTest','TranslationTest','ManagedFilesTest','RestoredMetadataTest','RestoredAlmanacTest']
    subprocess.run([str(a.jdk/'bin/javac.exe'),'-encoding','UTF-8','-cp',str(a.android_jar),'-d',str(classes),
                    *map(str,sources),*[str(r/'runtime/tests'/(s+'.java')) for s in tests]],check=True,timeout=60)
    java=[str(a.jdk/'bin/java.exe'),'-XX:ActiveProcessorCount=2','-Xmx256m','-cp',os.pathsep.join(map(str,[classes,a.android_jar]))]
    for test,args in [('PayloadTranslationTest',[fixture,a.work/'translated.tsv']),('TranslationTest',[]),('ManagedFilesTest',[a.work])]:
        subprocess.run(java+[test,*map(str,args)],check=True,timeout=60)

if __name__=='__main__':main()
