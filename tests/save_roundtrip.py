"""Exercise SDLPAL's real save writer and loader in two independent BDA runs."""
from pathlib import Path
import argparse,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
ap=argparse.ArgumentParser();ap.add_argument('--drive',choices=('A','B'),default='A');args=ap.parse_args()
DATA=(args.drive+mod.DATA[1:]).lower()
files={DATA+'pal9588.pak':(ROOT/'build/resources/PAL9588.PAK').read_bytes(),DATA+'porttest.save':b'1'}
bda=ROOT/'build/regression/H1PAL.bda'
first=mod.PalMachine(bda,files,999999);first.run()
assert b'SAVE PASS' in first.files[DATA+'porttest.log']
save=first.files[DATA+'2.rpg'];assert len(save)==183488 and save[:2]==b'\x34\x12'
second=mod.PalMachine(bda,first.files,999999);second.run()
assert b'RELOAD PASS' in second.files[DATA+'porttest.log']
assert second.files[DATA+'2.rpg']==save
assert ('DATA_PATH '+args.drive+':').encode() in second.files[DATA+'h1pal.log']
assert not any(name[0].upper()!=args.drive for name in second.files)
out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
report={'ok':True,'environment':'real MIPS engine with modeled H1 services','drive':args.drive,'save_size':len(save),
    'log':second.files[DATA+'porttest.log'].decode(),'sha256':first.meta['sha256'],
    'leaked_handles':[len(first.handles),len(second.handles)],'leaked_allocations':[len(first.allocations),len(second.allocations)]}
(out/('save-roundtrip.json' if args.drive=='A' else 'save-roundtrip-B.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
