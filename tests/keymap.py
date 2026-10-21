"""Execute mapping, storage and native event/held-key paths in the actual MIPS BDA."""
from pathlib import Path
import importlib.util,json
from unicorn.mips_const import UC_MIPS_REG_RA,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_V0
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
DEFAULT=[37,27,40,35,25,24]
DIR=':\\应用\\数据\\PAL\\'

class KeysMachine(mod.PalMachine):
    def __init__(self,files=None):
        super().__init__(ROOT/'build/release/H1PAL.bda',files or {},999999)
    def event(self,code,key,*args):
        event=self.events.pop(0) if self.events else (-1,-1)
        self.word(code,event[0]);self.word(key,event[1]);return 0
    def call(self,name,*args):
        self.finished=False;self.uc.reg_write(UC_MIPS_REG_RA,0x80001ff0)
        for reg,value in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),args):self.uc.reg_write(reg,value)
        self.uc.emu_start(self.meta['symbols'][name],0,timeout=10_000_000,count=30_000_000)
        assert self.finished,name
        return self.uc.reg_read(UC_MIPS_REG_V0)
    def mapping(self):return [self.call('h1pal_keymap_get',i) for i in range(6)]
    def close(self):
        if self.gui_active:self.call('h1pal_platform_close')
        self.call('h1pal_files_close');assert not self.handles and not self.allocations

for drive in ('A','B'):
    path=lambda name:(drive+DIR+name).lower()
    m=KeysMachine({path('PAL9588.PAK'):b'volume-presence-probe'})
    assert m.call('h1pal_select_data_path')==1
    m.call('h1pal_keymap_load');assert m.mapping()==DEFAULT
    assert m.call('h1pal_keymap_assign',4,17)==1 # Confirm -> X.
    assert m.call('h1pal_keymap_assign',5,16)==1 # Cancel -> Z.
    assert m.call('h1pal_keymap_assign',0,27)==1 # Duplicate direction swaps.
    expected=[27,37,40,35,17,16];assert m.mapping()==expected
    for action,key in ((9,1),(0,0),(0,41),(0,43),(0,44)):
        assert m.call('h1pal_keymap_assign',action,key)==0
        assert m.mapping()==expected
    assert m.call('h1pal_platform_open')==1
    for key,bit in ((17,16),(16,32),(27,1),(37,2),(40,4),(35,8),(25,0),(24,0)):
        m.physical_keys.add(key);assert m.call('h1pal_platform_keys')==bit,(key,bit)
        assert m.call('h1pal_platform_keys')==bit
        m.physical_keys.clear();assert m.call('h1pal_platform_keys')==0
        m.events.extend([(9,key),(10,key)]);assert m.call('h1pal_platform_keys')==bit
        assert m.call('h1pal_platform_keys')==0
    # Settings always retain factory navigation, including Escape as a way back.
    m.call('h1pal_platform_settings_input',1)
    for key,bit in ((25,16),(24,32),(17,0),(16,0),(37,1),(27,2)):
        m.physical_keys.add(key);assert m.call('h1pal_platform_keys')==bit
        m.physical_keys.clear();m.call('h1pal_platform_keys')
    # Capture accepts an otherwise unbound key through either firmware input path.
    m.call('h1pal_platform_capture_keys',1);m.physical_keys.add(18)
    m.call('h1pal_platform_pump');assert m.call('h1pal_platform_take_capture_key')==18
    m.physical_keys.clear();m.call('h1pal_platform_capture_keys',0)
    m.call('h1pal_platform_capture_keys',1);m.events.extend([(9,39),(10,39)])
    m.call('h1pal_platform_pump');assert m.call('h1pal_platform_take_capture_key')==25
    m.call('h1pal_platform_capture_keys',0);m.call('h1pal_platform_settings_input',0)
    assert m.call('h1pal_platform_detached')==0
    m.physical_keys.update((16,17));m.call('h1pal_platform_pump');m.ticks+=2000
    m.call('h1pal_platform_pump');assert m.call('h1pal_platform_detached')==0
    m.physical_keys.clear();m.call('h1pal_platform_pump')
    # A failing write cannot install an unsaved mapping in the running game.
    original=m.fopen
    def fail(path_ptr,mode,*args):
        if m.string(path_ptr).endswith('h1keys.cfg') and 'w' in m.string(mode):return 0
        return original(path_ptr,mode,*args)
    addresses=[a for a,fn in m.callbacks.items() if fn==original]
    assert addresses
    for a in addresses:m.callbacks[a]=fail
    assert m.call('h1pal_keymap_assign',4,18)==0 and m.mapping()==expected
    for a in addresses:m.callbacks[a]=original
    saved=m.files[path('h1keys.cfg')];m.close()
    fresh=KeysMachine({path('PAL9588.PAK'):b'probe',path('h1keys.cfg'):saved})
    fresh.call('h1pal_select_data_path');fresh.call('h1pal_keymap_load');assert fresh.mapping()==expected
    assert fresh.call('h1pal_keymap_restore')==1 and fresh.mapping()==DEFAULT
    restored=fresh.files[path('h1keys.cfg')];fresh.close()
    assert restored==b'H1PAL-KEYS 1\n37 27 40 35 25 24\n'
    # Legacy aliases cannot create conflicting held scancodes in a config file.
    for broken in (b'',b'H1PAL-KEYS 2\n37 27 40 35 25 24\n',
                   b'H1PAL-KEYS 1\n37 37 40 35 25 24\n',
                   b'H1PAL-KEYS 1\n37 27 26 35 25 24\n',
                   b'H1PAL-KEYS 1\n37 27 40 35 25 999\n',
                   b'H1PAL-KEYS 1\n37 27 40\n',
                   b'H1PAL-KEYS 1\n37 27 40 35 25 24 garbage\n'):
        bad=KeysMachine({path('PAL9588.PAK'):b'probe',path('h1keys.cfg'):broken})
        bad.call('h1pal_select_data_path');bad.call('h1pal_keymap_load');assert bad.mapping()==DEFAULT
        bad.close()
    emergency=KeysMachine();emergency.call('h1pal_platform_open')
    emergency.call('h1pal_keymap_assign',4,17);emergency.call('h1pal_keymap_assign',5,16)
    emergency.physical_keys.update((25,24));emergency.call('h1pal_platform_pump');emergency.ticks+=2000
    emergency.call('h1pal_platform_pump');assert emergency.call('h1pal_platform_detached')==1
    emergency.close()
report={'ok':True,'sha256':m.meta['sha256'],'six_actions':True,'held_and_event_paths':True,
        'duplicate_swap':True,'fixed_settings_navigation':True,'raw_capture_and_aliases':True,
        'selected_volume_persistence':['A','B'],'fresh_process_reload':True,'restore_defaults':True,
        'invalid_config_fallback':True,'save_failure_preserves_active_mapping':True,'physical_emergency_exit':True,'clean_exit':True}
(ROOT/'build/verification/keymap.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
