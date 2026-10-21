"""Visit quit -> settings -> key mapping using the owner's optional PAL resources."""
from pathlib import Path
import argparse,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A0,UC_MIPS_REG_A1
from music import MusicMachine,DATA
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resources',type=Path,default=ROOT/'build/resources/PAL9588.PAK')
    args=ap.parse_args()
    files={(DATA+'PAL9588.PAK').lower():args.resources.read_bytes()}
    class MenuMachine(MusicMachine):
        def event(self,code,key,*args):
            event=self.events.pop(0) if self.events else (-1,-1)
            self.word(code,event[0]);self.word(key,event[1]);return 0
    m=MenuMachine(ROOT/'build/release/H1PAL.bda',files,999999)
    m.call('h1_run_init_array');m.call('PAL_LoadConfig',1);m.call('UTIL_Platform_Init',0,0)
    m.call('SDL_Init',0);m.call('PAL_InitGlobals');m.call('VIDEO_Startup')
    m.call('PAL_InitFont',m.meta['symbols']['gConfig']);m.call('PAL_InitUI');m.call('PAL_InitText')
    m.call('PAL_InitInput');m.call('PAL_InitResources');m.call('AUDIO_OpenDevice');m.call('PAL_AVIInit')
    m.call('PAL_SetPalette',0,0);m.call('PAL_DrawOpeningMenuBackground');m.call('VIDEO_UpdateScreen',0)
    initial=m.read(0x82000000,480*272*4);allocations=len(m.allocations)
    out=ROOT/'build/verification/settings';out.mkdir(parents=True,exist_ok=True)
    sequence=[27,27,25,25,27,27,27,27,25,17,27,25,16,24,24,16]
    labels=[];screens=[]
    def wide(pointer):
        values=[]
        for i in range(64):
            v=struct.unpack('<I',m.read(pointer+4*i,4))[0]
            if not v:break
            values.append(chr(v))
        return ''.join(values)
    def draw(uc,address,size,user):
        if uc.reg_read(UC_MIPS_REG_A1)==(10<<16)|128:
            labels.append(wide(uc.reg_read(UC_MIPS_REG_A0)))
    def process(uc,address,size,user):
        assert sequence,'UI input did not return through the expected quit menu'
        name={3:'quit-settings',4:'system-settings',5:'keymap-default',10:'keymap-capture',11:'keymap-confirm-x',14:'keymap-custom'}.get(17-len(sequence))
        if name:
            m.image().save(out/(name+'.png'));screens.append(name)
            assert struct.unpack('<I',m.read(m.meta['symbols']['width'],4))[0]==480
        key=sequence.pop(0);m.events.extend([(9,key),(10,key)])
    for name,callback in [('PAL_DrawText',draw),('PAL_ProcessEvent',process)]:
        address=m.meta['symbols'][name];m.uc.hook_add(UC_HOOK_CODE,callback,begin=address,end=address)
    m.call('PAL_QuitGame')
    assert not sequence and {'系统设置','按键映射'}<=set(labels),labels
    assert m.call('h1pal_keymap_get',4)==17 and m.call('h1pal_keymap_get',5)==16
    assert m.read(0x82000000,480*272*4)==initial,'menu did not restore the original full-width background'
    assert len(m.allocations)==allocations,'settings leaked a surface or extended frame'
    m.call('AUDIO_CloseDevice');m.call('VIDEO_Shutdown');m.call('SDL_Quit');m.call('h1pal_files_close');m.call('h1pal_allocations_free')
    assert not m.handles and not m.allocations and not m.gui_active and not m.audio_active
    report={'ok':True,'sha256':m.meta['sha256'],'kind':'actual MIPS BDA, owner PAL UI assets',
            'quit_settings_keymap_path':True,'captured_confirm_x_cancel_z':True,'original_border_font_palette':True,
            'fullscreen':[480,272],'background_restored':True,'clean_exit':True,'screenshots':screens}
    (ROOT/'build/verification/settings-ui.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
