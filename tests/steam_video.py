"""Decode all six owner-supplied AVI clips with the actual MIPS BDA."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,time
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
from unicorn.mips_const import UC_MIPS_REG_PC,UC_MIPS_REG_SP
class VideoMachine(mod.PalMachine):
    def __init__(self,bda,files):
        self.skipped=False;super().__init__(bda,files,999999)
    def event(self,code,key,*a):
        frame=int.from_bytes(self.read(self.meta['symbols']['g_presented_frames'],4),'little')
        if frame<8:self.skipped=False
        if frame>=8 and not self.skipped:
            self.skipped=True;self.events.extend([(9,24),(10,24)])
        e=self.events.pop(0) if self.events else (-1,-1)
        self.word(code,e[0]);self.word(key,e[1]);return 0
ap=argparse.ArgumentParser();ap.add_argument('--resources',type=Path,default=ROOT/'build/h264-resources');ap.add_argument('--report',default='steam-video');args=ap.parse_args()
assert args.report.isidentifier() or args.report.replace('-','').isidentifier()
files={(mod.DATA+name).lower():(args.resources/name).read_bytes() for name in ('PAL9588.PAK','PALVIDEO.PAK')}
files[(mod.DATA+'PORTTEST.VIDEO').lower()]=b'1'
m=VideoMachine(ROOT/'build/regression/H1PAL.bda',files);started=time.monotonic();pc=0x83c00020
for step in range(8):
    m.uc.emu_start(pc,0,timeout=30_000_000,count=500_000_000)
    if m.finished:break
    pc=m.uc.reg_read(UC_MIPS_REG_PC);print('progress',step,m.stats(),hex(pc),flush=True)
assert m.finished
log=m.files[(mod.DATA+'PORTTEST.LOG').lower()].decode()
assert log.count('PASS')==7 and 'FAIL' not in log,log
assert not m.handles and not m.allocations and not m.gui_active and not m.audio_active
assert m.uc.reg_read(UC_MIPS_REG_SP)==0x83aff000
report={'ok':True,'sha256':m.meta['sha256'],'video_pack_sha256':hashlib.sha256(files[(mod.DATA+'PALVIDEO.PAK').lower()]).hexdigest(),'log':log,'stats':m.stats(),'seconds':round(time.monotonic()-started,2)}
(ROOT/f'build/verification/{args.report}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
