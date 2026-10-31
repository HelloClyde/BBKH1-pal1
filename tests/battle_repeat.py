"""Actual MIPS battle-only R shortcut, mapping priority and previous-action reuse."""
from pathlib import Path
import argparse,json,struct
from elftools.elf.elffile import ELFFile
from music import MusicMachine,DATA
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--resources',type=Path);args=ap.parse_args()
    class RepeatMachine(MusicMachine):
        def event(self,code,key,*args):
            event=self.events.pop(0) if self.events else (-1,-1)
            self.word(code,event[0]);self.word(key,event[1]);return 0
    m=RepeatMachine(ROOT/'build/release/H1PAL.bda',{},999999)
    layouts={}
    with (ROOT/'build/release/H1PAL.elf').open('rb') as stream:
        for cu in ELFFile(stream).get_dwarf_info().iter_CUs():
            for die in cu.iter_DIEs():
                name=die.attributes.get('DW_AT_name')
                if die.tag=='DW_TAG_structure_type' and name and name.value in (b'tagGLOBALVARS',b'tagBATTLE',b'tagBATTLEPLAYER',b'tagBATTLEUI'):
                    fields={child.attributes['DW_AT_name'].value.decode():child.attributes['DW_AT_data_member_location'].value
                        for child in die.iter_children() if child.tag=='DW_TAG_member' and child.attributes.get('DW_AT_name') and child.attributes.get('DW_AT_data_member_location')}
                    if fields:layouts[name.value.decode()]=fields
    def word(address):return int.from_bytes(m.read(address,4),'little')
    global_vars=word(m.meta['symbols']['gpGlobals'])
    in_battle=global_vars+layouts['tagGLOBALVARS']['fInBattle']
    input_bits=m.meta['symbols']['g_InputState']+8
    repeat=1<<8
    def process():
        m.call('PAL_ClearKeyState');m.call('PAL_ProcessEvent');return word(input_bits)
    m.call('h1_run_init_array');m.call('PAL_LoadConfig',1);m.call('UTIL_Platform_Init',0,0)
    assert m.call('h1pal_platform_open')==1
    m.call('PAL_InitInput')
    m.physical_keys.add(4);assert process()==0,'R affected map/menu input'
    m.physical_keys.clear();process()
    m.word(in_battle,1)
    m.physical_keys.add(4);assert process()==repeat,'held R did not reach kKeyRepeat'
    assert process()==0,'holding R repeated the command every frame'
    m.physical_keys.clear();process()
    m.events.extend([(9,4),(10,4)]);assert process()==repeat,'short event-only R press was lost'
    assert process()==0
    m.call('h1pal_platform_settings_input',1)
    m.events.extend([(9,4),(10,4)]);assert process()==0
    m.call('h1pal_platform_capture_keys',1)
    m.events.extend([(9,4),(10,4)]);assert process()==0
    assert m.call('h1pal_platform_take_capture_key')==4,'R could not be captured for a custom mapping'
    m.call('h1pal_platform_capture_keys',0);m.call('h1pal_platform_settings_input',0)
    assert m.call('h1pal_keymap_assign',4,4)
    m.physical_keys.add(4);assert process()==2,'custom R-confirm binding lost priority'
    m.physical_keys.clear();process();assert m.call('h1pal_keymap_restore')
    m.events.append((9,4));m.call('h1pal_platform_pump')
    m.word(in_battle,0);assert process()==0,'latched R leaked outside combat'
    # The shortcut supplies the upstream repeat flag; upstream retains its
    # validation and fallback rather than replaying raw key presses.
    battle=m.meta['symbols']['g_Battle'];player=battle+layouts['tagBATTLE']['rgPlayer']
    action=player+layouts['tagBATTLEPLAYER']['action']
    previous=player+layouts['tagBATTLEPLAYER']['prevAction']
    m.word(in_battle,1)
    m.write(previous,struct.pack('<IHhI',1,0x123,0,0)) # Previous defend.
    m.write(action,struct.pack('<IHhI',5,0,0,0)) # Different current command.
    m.call('PAL_BattleCommitAction',1)
    assert m.read(action,12)==m.read(previous,12),'engine did not restore previous action'
    m.write(previous,bytes(12));m.call('PAL_BattleCommitAction',1)
    assert word(action)==2 and struct.unpack('<h',m.read(action+6,2))[0]==-1,'first-turn fallback changed'
    m.call('PAL_ShutdownInput');m.call('PAL_FreeConfig');m.call('h1pal_platform_close')
    m.call('h1pal_files_close');m.call('h1pal_allocations_free')
    assert not m.handles and not m.allocations and not m.gui_active
    if args.resources:
        m=RepeatMachine(ROOT/'build/release/H1PAL.bda',{(DATA+'PAL9588.PAK').lower():args.resources.read_bytes()},999999)
        m.call('h1_run_init_array');m.call('PAL_LoadConfig',1);m.call('UTIL_Platform_Init',0,0)
        m.call('SDL_Init',0);m.call('PAL_InitGlobals');m.call('VIDEO_Startup')
        m.call('PAL_InitFont',m.meta['symbols']['gConfig']);m.call('PAL_InitUI');m.call('PAL_InitText')
        m.call('PAL_InitInput');m.call('PAL_InitResources');m.call('PAL_InitGameData',0)
        global_vars=word(m.meta['symbols']['gpGlobals']);m.word(global_vars+layouts['tagGLOBALVARS']['fInBattle'],1)
        ui=battle+layouts['tagBATTLE']['UI'];m.word(ui+layouts['tagBATTLEUI']['state'],1)
        m.write(previous,struct.pack('<IHhI',1,0,0,0));m.write(action,struct.pack('<IHhI',5,0,0,0))
        m.physical_keys.add(4);assert process()==repeat
        m.call('PAL_BattleUIUpdate');assert word(action)==1,'real battle UI did not dispatch R to repeat'
        m.call('VIDEO_Shutdown');m.call('SDL_Quit');m.call('h1pal_files_close');m.call('h1pal_allocations_free')
        assert not m.handles and not m.allocations and not m.gui_active
    report={'ok':True,'sha256':m.meta['sha256'],'kind':'actual MIPS with modeled H1 services; '+('owner-resource battle UI' if args.resources else 'no game assets'),
        'r_matrix_key':4,'battle_only':True,'event_and_held_paths':True,'one_command_per_press':True,
        'settings_capture_preserved':True,'custom_binding_priority':True,'no_latched_key_after_battle':True,
        'upstream_previous_action_restored':True,'first_turn_attack_fallback':True,
        'owner_resource_ui_dispatch_checked':bool(args.resources),'clean_exit':True}
    out=ROOT/'build/verification';out.mkdir(exist_ok=True)
    (out/'battle-repeat.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
