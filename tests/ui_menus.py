"""Visit real SDLPAL menu loops and cancel each via native H1 key events."""
from pathlib import Path
import importlib.util,json,struct,time
from unicorn import UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A0,UC_MIPS_REG_PC
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
DATA=mod.DATA.lower();out=ROOT/'build/verification/ui';out.mkdir(parents=True,exist_ok=True)
NAMES={1:'title',2:'status',3:'equipment',4:'load-slots',5:'game-menu',6:'inventory-menu',
       7:'item-list',8:'magic-list',9:'magic-roles',10:'item-target',11:'confirmation',12:'shop-buy',13:'shop-sell'}
READ_MENU={1,4,5,6,9,11,12}
shots={};bases={};ready=set()
class UIMachine(mod.PalMachine):
    def word_at(self,address):return struct.unpack('<I',self.read(address,4))[0]
    def event(self,code,key,*args):
        phase=self.word_at(self.meta['symbols']['h1pal_ui_test_stage'])
        if phase and phase not in shots and (phase not in READ_MENU or phase in ready) and self.stats()[2]>bases.get(phase,999999):
            dimensions={k:self.word_at(self.meta['symbols'][k]) for k in ('width','height','logical_width','logical_height','map_full')}
            assert dimensions=={'width':480,'height':272,'logical_width':360,'logical_height':204,'map_full':1},(phase,dimensions)
            self.image().save(out/(NAMES[phase]+'.png'));shots[phase]=dimensions
            self.events.extend([(9,24),(10,24)])
            print('menu',phase,NAMES[phase],'480x272',flush=True)
        event=self.events.pop(0) if self.events else (-1,-1)
        self.word(code,event[0]);self.word(key,event[1]);return 0
files={DATA+'pal9588.pak':(ROOT/'build/resources/PAL9588.PAK').read_bytes(),
       DATA+'1.rpg':(ROOT/'build/verification/native-1.rpg').read_bytes(),DATA+'porttest.ui':b'1'}
m=UIMachine(ROOT/'build/regression/H1PAL.bda',files,999999)
def checkpoint(uc,address,size,user):
    phase=uc.reg_read(UC_MIPS_REG_A0);bases[phase]=m.stats()[2]
def read_menu(uc,address,size,user):
    ready.add(m.word_at(m.meta['symbols']['h1pal_ui_test_stage']))
for name,callback in (('h1pal_ui_checkpoint',checkpoint),('PAL_ReadMenu',read_menu)):
    fn=m.meta['symbols'][name];m.uc.hook_add(UC_HOOK_CODE,callback,begin=fn,end=fn)
start=time.monotonic();pc=0x83c00020
for iteration in range(12):
    m.uc.emu_start(pc,0,timeout=30_000_000,count=500_000_000)
    if m.finished:break
    pc=m.uc.reg_read(UC_MIPS_REG_PC)
    print('progress',iteration,'menus',list(shots),'frames',m.stats()[2],hex(pc),flush=True)
assert m.finished and set(shots)==set(NAMES),(m.finished,shots)
assert b'UI PASS' in m.files[DATA+'porttest.log']
assert not m.handles and not m.allocations and not m.gui_active and not m.audio_active
report={'ok':True,'sha256':m.meta['sha256'],'menus':{NAMES[k]:v for k,v in shots.items()},
        'clean_exit':True,'seconds':round(time.monotonic()-start,2)}
(ROOT/'build/verification/ui-menus.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
