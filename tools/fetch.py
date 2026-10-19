"""Fetch the exact open-source dependencies needed for a standalone build."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[1]
for key,info in json.loads((ROOT/'UPSTREAM.json').read_text()).items():
    if 'path' not in info:continue
    target=ROOT/info['path']
    if not target.exists():
        subprocess.run(['git','clone',info['url'],str(target)],check=True)
        subprocess.run(['git','-c',f'safe.directory={target.as_posix()}','-C',str(target),'checkout','--detach',info['commit']],check=True)
    actual=subprocess.check_output(['git','-c',f'safe.directory={target.as_posix()}','-C',str(target),'rev-parse','HEAD'],text=True).strip()
    if actual!=info['commit']:raise RuntimeError(key+' commit mismatch; keep existing checkout intact')
    print(key,actual)
