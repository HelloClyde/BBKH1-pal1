"""Check pinned Git dependencies or the hashes of an expanded release source ZIP."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]

def dependency(relative,expected):
    repo=ROOT/relative
    git=['git','-c','safe.directory=*','-C',str(repo)]
    top=subprocess.run([*git,'rev-parse','--show-toplevel'],capture_output=True,text=True)
    if top.returncode==0 and Path(top.stdout.strip()).resolve()==repo.resolve():
        actual=subprocess.check_output([*git,'rev-parse','HEAD'],text=True).strip()
        if actual!=expected:raise ValueError(relative+' commit mismatch')
        if subprocess.check_output([*git,'status','--porcelain','--untracked-files=no']).strip():
            raise ValueError(relative+' tracked source modified')
    else:
        manifest=json.loads((ROOT/'SOURCE-MANIFEST.json').read_text(encoding='utf-8'))
        info=next(v for v in manifest['dependencies'].values() if v['path']==relative)
        if info['commit']!=expected:raise ValueError(relative+' source manifest commit mismatch')
        files={n:sha for n,sha in manifest['files'].items() if n.startswith(relative+'/')}
        if not files:raise ValueError(relative+' has no pinned source files')
        for name,sha in files.items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:
                raise ValueError('Source archive file modified: '+name)
    return expected
