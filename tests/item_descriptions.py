"""Check owner-supplied DOS descriptions in the unchanged, actual MIPS BDA.

Requires private game resources; not part of resource-free public CI.
"""
from pathlib import Path
import argparse,hashlib,json,re,struct,sys
from unicorn import UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A0,UC_MIPS_REG_A1
from music import MusicMachine,DATA
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from palpak import verify_archive

def digest(data):return hashlib.sha256(data).hexdigest()
def members(path):
    data=path.read_bytes()
    return {e.name:data[e.offset:e.offset+e.size] for e in verify_archive(path)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resources',type=Path,required=True)
    ap.add_argument('--baseline',type=Path)
    ap.add_argument('--descriptions',type=Path)
    args=ap.parse_args();packed=members(args.resources);raw=packed['desc.dat']
    records={}
    for line in raw.splitlines():
        match=re.match(rb'^([0-9a-fA-F]{1,4})\(([^=]*)\)=(.*)$',line)
        if match:
            object_id=int(match[1],16)
            assert object_id not in records,'duplicate description ID'
            records[object_id]=match[3]
    assert records and all(records.values())
    if args.descriptions:assert raw==args.descriptions.read_bytes()
    original=members(args.baseline) if args.baseline else None
    if original is not None:
        assert set(packed)-set(original)=={'desc.dat'}
        assert all(packed[name]==data for name,data in original.items())
    files={(DATA+'PAL9588.PAK').lower():args.resources.read_bytes()}
    save=ROOT/'build/verification/native-1.rpg'
    if save.is_file():files[(DATA+'1.rpg').lower()]=save.read_bytes()
    class DescriptionMachine(MusicMachine):
        def event(self,code,key,*args):
            event=self.events.pop(0) if self.events else (-1,-1)
            self.word(code,event[0]);self.word(key,event[1]);return 0
    m=DescriptionMachine(ROOT/'build/release/H1PAL.bda',files,999999)
    def wide(pointer):
        values=[]
        for i in range(512):
            value=struct.unpack('<I',m.read(pointer+4*i,4))[0]
            if not value:return ''.join(values)
            values.append(chr(value))
        raise AssertionError('unterminated description')
    m.call('h1_run_init_array');m.call('PAL_LoadConfig',1);m.call('UTIL_Platform_Init',0,0)
    m.call('SDL_Init',0);assert m.call('PAL_InitGlobals')==0
    m.call('VIDEO_Startup');m.call('PAL_InitFont',m.meta['symbols']['gConfig'])
    m.call('PAL_InitUI');m.call('PAL_InitText');m.call('PAL_InitInput');m.call('PAL_InitResources')
    scratch=0x81800000;m.write(scratch,b'desc.dat\0')
    descriptions=m.call('PAL_LoadObjectDesc',scratch);assert descriptions
    texts={object_id:wide(m.call('PAL_GetObjectDesc',descriptions,object_id)) for object_id in records}
    assert all(texts.values()) and not any('\ufffd' in text for text in texts.values())
    glyphs=set(''.join(texts.values()))-set(' *\t\r\n')
    for char in glyphs:
        value=ord(char);assert value<0xd800 or 0xf900<=value<65534,repr(char)
        index=value if value<0xd800 else value-(0xf900-0xd800)
        assert any(m.read(m.meta['symbols']['unicode_font']+index*32,32)),repr(char)
    assert texts[0x65]=='上等刀傷藥，去腐生肌。*HP+200'
    assert texts[0xa6]=='用木材雕刻的劍，小孩玩具。*武術+2 身法+3'
    m.call('PAL_FreeObjectDesc',descriptions)
    m.call('PAL_InitGameData',1 if save.is_file() else 0)
    if save.is_file():
        m.call('PAL_SetLoadFlags',3);m.call('PAL_LoadResources');m.call('PAL_UpdatePartyGestures',0)
    m.call('PAL_SetPalette',0,0)
    out=ROOT/'build/verification/item-descriptions';out.mkdir(parents=True,exist_ok=True)
    drawn=[];selected=[]
    def draw(uc,address,size,user):
        pos=uc.reg_read(UC_MIPS_REG_A1)
        if pos&0xffff==75 and pos>>16>=150:
            drawn.append({'text':wide(uc.reg_read(UC_MIPS_REG_A0)),'x':pos&0xffff,'y':pos>>16})
    def lookup(uc,address,size,user):selected.append(uc.reg_read(UC_MIPS_REG_A1))
    for name,callback in [('PAL_DrawText',draw),('PAL_GetObjectDesc',lookup)]:
        address=m.meta['symbols'][name];m.uc.hook_add(UC_HOOK_CODE,callback,begin=address,end=address)
    examples=[]
    for object_id,label in [(0x65,'medicine'),(0xa6,'equipment'),(0x10e,'quest-item')]:
        m.call('PAL_AddItemToInventory',object_id,(-999)&0xffffffff);m.call('PAL_CompressInventory')
        assert m.call('PAL_AddItemToInventory',object_id,1)
        # Exclude the usable-equipment append branch so End selects this last item.
        m.call('PAL_ItemSelectMenuInit',0xfffe)
        m.call('PAL_MakeScene' if save.is_file() else 'PAL_DrawOpeningMenuBackground')
        drawn.clear();selected.clear()
        m.word(m.meta['symbols']['g_InputState']+8,1<<17)
        m.call('PAL_ItemSelectMenuUpdate');m.call('VIDEO_UpdateScreen',0)
        assert selected==[object_id],selected
        assert [line['text'] for line in drawn]==texts[object_id].split('*'),drawn
        assert all(line['y']+16<=204 for line in drawn)
        image=m.image();assert image.size==(480,272);image.save(out/(label+'.png'))
        examples.append({'object_id':hex(object_id),'name':wide(m.call('PAL_GetWord',object_id)),
                         'lines':list(drawn),'screenshot':label+'.png'})
    m.call('VIDEO_Shutdown');m.call('SDL_Quit');m.call('h1pal_files_close');m.call('h1pal_allocations_free')
    assert not m.handles and not m.allocations and not m.gui_active
    report={'ok':True,'kind':'actual MIPS BDA with modeled H1 services; owner resources',
        'bda_sha256':m.meta['sha256'],'resource_sha256':digest(args.resources.read_bytes()),
        'resource_size':args.resources.stat().st_size,'archive_members':len(packed),
        'unchanged_original_members':len(original) if original is not None else None,
        'description_sha256':digest(raw),'description_size':len(raw),'description_count':len(texts),
        'source_bytes_preserved':args.descriptions is not None,'all_descriptions_loaded':True,
        'all_description_glyphs_present':True,'unique_description_glyphs':len(glyphs),
        'max_lines':max(text.count('*')+1 for text in texts.values()),'fullscreen':[480,272],
        'examples':examples,'clean_exit':True}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
