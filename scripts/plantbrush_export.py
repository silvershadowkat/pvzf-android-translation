"""Export the supplied, checksum-pinned CLIP vision tower, never its text tower.

Development-only tool. The APK contains ONNX and primitive numeric index data,
not Python, pickle, executable upstream code, or a desktop launcher.
"""
import argparse, hashlib, importlib.util, json, os, struct
from pathlib import Path

def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--upstream',type=Path,required=True)
    ap.add_argument('--clip-source',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    os.environ['OMP_NUM_THREADS']='2'; os.environ['MKL_NUM_THREADS']='2'
    import numpy as np
    import torch
    import onnxruntime as ort
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    spec=importlib.util.spec_from_file_location('clip_source',a.clip_source)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    model=a.upstream/'data/model/ViT-B-32.pt'
    provenance=json.loads((model.parent/'provenance.json').read_text('utf-8'))
    assert sha(model)==provenance['weights_sha256']
    archived=torch.jit.load(str(model),map_location='cpu')
    visual=mod.VisionTransformer(224,32,768,12,12,512).eval().float()
    visual.load_state_dict({k[7:]:v.float() for k,v in archived.state_dict().items() if k.startswith('visual.')})
    del archived
    torch.backends.mha.set_fastpath_enabled(False)
    example=torch.zeros(1,3,224,224)
    with torch.inference_mode():
        torch.onnx.export(visual,example,str(a.output/'vision.onnx'),input_names=['image'],output_names=['embedding'],opset_version=17,dynamo=False)
    opts=ort.SessionOptions(); opts.intra_op_num_threads=2; opts.inter_op_num_threads=1
    session=ort.InferenceSession(str(a.output/'vision.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
    rng=np.random.default_rng(173); comparisons=[]
    for x in (np.zeros((1,3,224,224),np.float32),rng.standard_normal((1,3,224,224)).astype(np.float32)):
        with torch.inference_mode(): expected=visual(torch.from_numpy(x)).numpy()
        actual=session.run(None,{'image':x})[0]
        cosine=float((actual*expected).sum()/np.linalg.norm(actual)/np.linalg.norm(expected))
        error=float(abs(actual-expected).max()); assert cosine>0.99999 and error<0.001
        comparisons.append({'cosine':cosine,'max_abs_error':error})
    catalog=json.loads((a.upstream/'data/catalog.json').read_text('utf-8-sig'))
    refs=[{k:x[k] for k in ('plantType','enumName','displayName','skinIndex')} for x in catalog['references']]
    idx=np.load(a.upstream/'data/index.npz',allow_pickle=False)
    # Big endian lets Java's bounded DataInputStream parse without native code.
    with (a.output/'index.bin').open('wb') as f:
        f.write(b'PVZAI001')
        for key in ('features','records','negative_features','colors','shapes','spatial','variant_colors','negative_shapes'):
            data=idx[key]; f.write(struct.pack('>II',len(data),data.size//len(data)))
            f.write(data.astype('>i4' if key=='records' else '>f4').tobytes())
    for i,x in enumerate(refs):x['fingerprint']=str(idx['fingerprints'][i])
    (a.output/'catalog.json').write_text(json.dumps(refs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    manifest={'format':1,'recognition_revision':3,'model':'OpenAI CLIP ViT-B/32 vision only, float32',
        'upstream_model':provenance,'upstream_catalog_sha256':sha(a.upstream/'data/catalog.json'),
        'upstream_index_sha256':sha(a.upstream/'data/index.npz'),'export_checks':comparisons,
        'files':{p.name:sha(p) for p in sorted(a.output.iterdir()) if p.name in ('vision.onnx','index.bin','catalog.json')}}
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'export_checks':comparisons,'model_bytes':(a.output/'vision.onnx').stat().st_size,'plants':catalog['plantCount']}),flush=True)

if __name__=='__main__':main()
