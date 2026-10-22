import sys,re,json,bisect,struct
from pathlib import Path
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);args=ap.parse_args()
W=args.work.resolve(); U=W.parent/'upgrade405'; P=U/'pre3'
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(P/'inspect-tools'),str(R/'scripts')]
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile
from build_metadata_translation import parse_metadata,load_pc_translations
A=W/'mode-audit';A.mkdir(exist_ok=True)
_,original=parse_metadata((U/'android405/global-metadata.dat').read_bytes())
_,current=parse_metadata((P/'metadata.dat').read_bytes())
runtime=json.loads((P/'english/translations.json').read_text(encoding='utf-8'))
pc,_,pcrules,_=load_pc_translations(P/'coverage-r12/pc-main/PvZ_Fusion_Translator/Localization/English/Strings',False)
raw=(U/'android405/libil2cpp.so').read_bytes()
with (U/'android405/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);segs=[(s['p_vaddr'],s['p_offset'],s['p_filesz']) for s in e.iter_segments() if s['p_type']=='PT_LOAD'];rels={x['r_offset']:x['r_addend'] for x in e.get_section_by_name('.rela.dyn').iter_relocations() if x['r_info_type']==1027}
def read(a,n):
 for v,o,z in segs:
  if v<=a and a+n<=v+z:return raw[o+a-v:o+a-v+n]
 return bytes(n)
methods={};cls='';rva=None
for line in (U/'types/dump.cs').read_text(encoding='utf-8').splitlines():
 m=re.match(r'(?:public|private|internal).*? (?:class|struct) ([^ :]+)',line)
 if m:cls=m[1]
 m=re.search(r'// RVA: 0x([0-9A-Fa-f]+)',line)
 if m:rva=int(m[1],16)
 elif rva and '(' in line and '{ }' in line:methods.setdefault(rva,[]).append(cls+'::'+line.strip());rva=None
addresses=sorted(methods);md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);md.detail=True
refs={};inspected=[];calls={}
for a,names in methods.items():
 if not any('MaLiang' in n for n in names):continue
 end=addresses[bisect.bisect_right(addresses,a)];pages={};found=set();called=set()
 for i in md.disasm(read(a,end-a),a):
  page_match=re.fullmatch(r'(x\d+), #0x([0-9a-f]+)',i.op_str)
  m=re.search(r'\[(x\d+)(?:, #0x([0-9a-f]+))?\]',i.op_str)
  if i.mnemonic=='ldr' and m and m[1] in pages:
   slot=pages[m[1]]+int(m[2] or '0',16);ptr=rels.get(slot,slot);v=int.from_bytes(read(ptr,8),'little')
   if v>>29==5 and v&1:
    idx=(v&0x1fffffff)>>1
    if idx<len(original):found.add(idx);refs.setdefault(idx,[]).extend(names)
  if i.mnemonic in ('b','bl') and i.op_str.startswith('#0x'):
   dest=int(i.op_str[1:],16)
   if dest in methods:called.update(methods[dest])
  for reg in i.regs_access()[1]:pages.pop(i.reg_name(reg).replace('w','x'),None)
  if i.mnemonic=='bl':
   for reg in range(19):pages.pop('x'+str(reg),None)
  if i.mnemonic=='adrp' and page_match:pages[page_match[1]]=int(page_match[2],16)
 inspected.append({'rva':hex(a),'methods':names,'literal_indices':sorted(found)})
 calls[hex(a)]=sorted(called)
def row(idx):
 s=original[idx].text;t=current[idx].text
 return {'index':idx,'source':s,'packaged_metadata':t,'runtime_exact':runtime['exact'].get(t),'pc_exact':pc.get(s),'methods':sorted(set(refs.get(idx,[])))}
rows=[row(i) for i in sorted(refs)]
keywords=['马良','画作','画的','画布','笔刷','鉴定','本地识别','植物候选','指定植物评分']
related=[row(i) for i,x in enumerate(original) if any(k in x.text for k in keywords) and i not in refs]
(A/'native-inventory.json').write_text(json.dumps({'methods':inspected,'literals':rows,'related_keyword_literals':related,'calls':calls},ensure_ascii=False,indent=2),encoding='utf-8')
chinese=[r for r in rows if re.search('[\u3400-\u9fff]',r['source'])]
(A/'chinese-review.json').write_text(json.dumps(chinese,ensure_ascii=False,indent=2),encoding='utf-8')
print('Methods',len(inspected),'literal references',len(rows),'Chinese',len(chinese),'additional keyword literals',len(related))
for r in chinese:print(r['index'],repr(r['source']),'=>',repr(r['packaged_metadata'] if r['source']!=r['packaged_metadata'] else r['runtime_exact']))
