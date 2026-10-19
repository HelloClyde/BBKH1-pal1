"""Run an actual SDLPAL auto-battle through the cross-compiled H1 BDA."""
from pathlib import Path
import importlib.util,json,time
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
from unicorn.mips_const import UC_MIPS_REG_PC,UC_MIPS_REG_V0,UC_MIPS_REG_SP
from unicorn import UC_HOOK_CODE
DATA=mod.DATA.lower()
files={DATA+'pal9588.pak':(ROOT/'build/resources/PAL9588.PAK').read_bytes(),DATA+'porttest.battle':b'1'}
m=mod.PalMachine(ROOT/'build/regression/H1PAL.bda',files,999999)
active_captured=False
def capture_active(uc,address,size,user):
 global active_captured
 if not active_captured and m.stats()[2]>=40:
  image=m.image();assert image.getbbox()==(0,0,480,272),'battle did not fill the LCD'
  image.save(ROOT/'build/verification/battle-active.png');active_captured=True
present=m.meta['symbols']['h1pal_platform_present']
m.uc.hook_add(UC_HOOK_CODE,capture_active,begin=present,end=present)
started=time.monotonic();pc=0x83c00020
for step in range(12):
 m.uc.emu_start(pc,0,timeout=30_000_000,count=500_000_000)
 if m.finished:break
 pc=m.uc.reg_read(UC_MIPS_REG_PC)
 print('progress',step,m.stats(),hex(pc),flush=True)
assert m.finished
assert active_captured
log=m.files[DATA+'porttest.log'].decode()
assert 'BATTLE WON' in log,log
assert not m.handles and not m.allocations and not m.audio_active and not m.gui_active
assert m.uc.reg_read(UC_MIPS_REG_SP)==0x83aff000
assert any(any(b) for b in m.audio_observed)
out=ROOT/'build/verification';m.image().save(out/'battle.png')
report={'ok':True,'environment':'real MIPS SDLPAL with modeled H1 services','fullscreen':[480,272],'sha256':m.meta['sha256'],'log':log,'stats':m.stats(),'seconds':round(time.monotonic()-started,2)}
(out/'battle.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
