"""Apply only shared drawing translations to published pre3. No AI hooks/model/service."""
import argparse,copy,json,os,subprocess,zipfile,shutil
from pathlib import Path
from build_plantbrush_prototype import BASE_SHA,CERT,sha
from package_apk_payload import copy_entry,is_old_signature

def main():
 p=argparse.ArgumentParser()
 for key in ('base','work','output','sdk','jdk','secret'):p.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();r=Path(__file__).resolve().parents[1];w=a.work/'regular-refresh';w.mkdir(parents=True,exist_ok=True);assert sha(a.base)==BASE_SHA
 def run(name,args,timeout=90,env=None):
  with (w/(name+'.log')).open('w') as f:out=subprocess.run(list(map(str,args)),stdout=f,stderr=subprocess.STDOUT,timeout=timeout,env=env)
  if out.returncode:raise RuntimeError(name+' failed')
  print(name+' passed',flush=True)
 # Keep the regular release's original runtime behavior and native library.
 files=['EnglishActivity.java','ManagedFiles.java'];sources=[]
 for name in files:
  result=subprocess.run(['git','show','v4.0.5-release-3:runtime/java/com/silvershadow/pvzf/'+name],cwd=r,capture_output=True,check=True,timeout=15)
  s=result.stdout.decode('utf-8')
  if name=='EnglishActivity.java':
   needle='        Log.i(TAG,"Display translations loaded: '
   assert s.count(needle)==1
   add='        for(String[] pair:PlantbrushTranslations.EXACT)exact.put(pair[0],pair[1]);\n        for(String[] rule:PlantbrushTranslations.RULES)rules.add(new Rule(rule[0],rule[1]));\n'
   s=s.replace(needle,add+needle)
  path=w/name;path.write_text(s,encoding='utf-8');sources.append(path)
 sources.append(r/'runtime/java/com/silvershadow/pvzf/PlantbrushTranslations.java')
 android=a.sdk/'platforms/android-35/android.jar';bt=a.sdk/'build-tools/35.0.0';classes=w/'classes';classes.mkdir(exist_ok=True);dex=w/'dex';dex.mkdir(exist_ok=True)
 run('javac',[a.jdk/'bin/javac.exe','-encoding','UTF-8','-source','8','-target','8','-classpath',android,'-d',classes,*sources])
 run('d8',[a.jdk/'bin/java.exe','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--release','--min-api','22','--lib',android,'--output',dex,*sorted(classes.rglob('*.class'))])
 assert not (dex/'classes2.dex').exists()
 unsigned=w/'unsigned.apk'
 with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(unsigned,'w') as z:
  for info in base.infolist():
   if is_old_signature(info.filename):continue
   if info.filename=='classes2.dex':z.writestr(copy.copy(info),(dex/'classes.dex').read_bytes())
   else:copy_entry(base,z,info)
 aligned=w/'aligned.apk';run('align',[bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned])
 props=dict(line.split('=',1) for line in (a.secret/'signing.properties').read_text('utf-8-sig').splitlines() if '=' in line and not line.startswith('#'))
 env=os.environ.copy();env['PVZF_LOCAL_STORE_PASS']=props['storepass'];env['PVZF_LOCAL_KEY_PASS']=props['keypass']
 output=a.output/'PvZ-Fusion-4.0.5-English-Android-prerelease3-drawing-text-fix.apk';signer=[a.jdk/'bin/java.exe','-jar',bt/'lib/apksigner.jar']
 run('sign',signer+['sign','--ks',a.secret/'PvZ-Fusion-English-Release.jks','--ks-key-alias',props['alias'],'--ks-pass','env:PVZF_LOCAL_STORE_PASS','--key-pass','env:PVZF_LOCAL_KEY_PASS','--v4-signing-enabled','false','--out',output,aligned],180,env);del env
 run('signature',signer+['verify','--verbose','--print-certs',output]);assert CERT in (w/'signature.log').read_text()
 run('alignment',[bt/'zipalign.exe','-c','-P','16','4',output])
 with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(output) as z:
  assert z.testzip() is None
  changes=[i.filename for i in base.infolist() if not is_old_signature(i.filename) and i.CRC!=z.getinfo(i.filename).CRC]
  assert changes==['classes2.dex']
  assert {n for n in z.namelist() if not is_old_signature(n)}=={n for n in base.namelist() if not is_old_signature(n)}
 record={'apk':str(output),'sha256':sha(output),'size_bytes':output.stat().st_size,'package':'com.LanPiaoPiao.PlantsVsZombiesEN','base_sha256':BASE_SHA,'changed_entries':changes,'local_only':True,'ai_features_included':False,'source_tag':'v4.0.5-release-3'}
 (a.output/'REGULAR-DRAWING-TEXT-BUILD.json').write_text(json.dumps(record,indent=2));print('Verified '+str(output))
if __name__=='__main__':main()
