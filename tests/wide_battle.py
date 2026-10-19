"""Verify battle cover geometry, palette effects and sprites at the new edges."""
from pathlib import Path
import importlib.util, json, struct, time
from elftools.elf.elffile import ELFFile
from unicorn.mips_const import UC_MIPS_REG_RA,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_SP,UC_MIPS_REG_V0
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
m=mod.PalMachine(ROOT/'build/release/H1PAL.bda',{},999999)
def call(name,*args):
    m.finished=False;m.uc.reg_write(UC_MIPS_REG_RA,0x80001ff0)
    for reg,value in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),args):m.uc.reg_write(reg,value)
    sp=m.uc.reg_read(UC_MIPS_REG_SP)
    for i,value in enumerate(args[4:]):m.word(sp+16+4*i,value)
    m.uc.emu_start(m.meta['symbols'][name],0,timeout=10_000_000,count=30_000_000)
    assert m.finished,name
    return m.uc.reg_read(UC_MIPS_REG_V0)
def word(address):return int.from_bytes(m.read(address,4),'little')
def fields(name):
    with (ROOT/'build/release/H1PAL.elf').open('rb') as f:
        dwarf=ELFFile(f).get_dwarf_info()
        for cu in dwarf.iter_CUs():
            for d in cu.iter_DIEs():
                if d.tag=='DW_TAG_structure_type' and d.attributes.get('DW_AT_name') and d.attributes['DW_AT_name'].value==name.encode():
                    return {c.attributes['DW_AT_name'].value.decode():c.attributes['DW_AT_data_member_location'].value
                            for c in d.iter_children() if c.tag=='DW_TAG_member' and c.attributes.get('DW_AT_name')}
def pixels(surface):return word(surface+20)
def data(surface):return m.read(pixels(surface),64000)
def crop(wide):return b''.join(wide[(y+2)*360+20:(y+2)*360+340] for y in range(200))
def frame(surface):
    ptr=call('h1pal_scene_battle_pixels',surface);assert ptr
    return m.read(ptr,360*204)
def rgb(x,y):return word(0x82000000+(y*480+x)*4)
started=time.monotonic();g=word(m.meta['symbols']['gpGlobals']);gf=fields('tagGLOBALVARS');bf=fields('tagBATTLE');battle=m.meta['symbols']['g_Battle']
m.word(g+gf['fInBattle'],1)
assert call('h1pal_platform_open')==1
bg=call('SDL_CreateRGBSurface',0,320,200,8,0,0,0,0)
scene=call('SDL_CreateRGBSurface',0,320,200,8,0,0,0,0)
m.word(battle+bf['lpBackground'],bg);m.word(battle+bf['lpSceneBuf'],scene)
palette=bytes(v for i in range(256) for v in (i,i^85,255-i,0));palette_address=0x81800000;m.write(palette_address,palette)
call('SDL_SetPalette',bg,3,palette_address,0,256);call('SDL_SetPalette',scene,3,palette_address,0,256)
# Two coordinate grids ensure a uniformly colored border cannot conceal a
# wrong scale factor or different X/Y transforms. No game assets are needed.
for raw in (bytes((x^y)%256 for y in range(200) for x in range(320)),
            bytes((x+3*y)%256 for y in range(200) for x in range(320))):
    m.write(pixels(bg),raw);call('h1pal_battle_load_background',bg)
    expected=bytes(raw[((y*8+84)//9)*320+x*8//9] for y in range(204) for x in range(360))
    assert frame(bg)==expected and data(bg)==crop(expected),'nonuniform background cover'
    m.write(pixels(scene),data(bg));call('h1pal_battle_make_background')
    assert frame(scene)==expected and data(scene)==crop(expected)
    call('h1pal_platform_present',scene)
    for x,y in ((0,0),(479,0),(0,271),(479,271),(40,80)):
        i=expected[(y*3//4)*360+x*3//4]
        assert rgb(x,y)==(i<<16)|((i^85)<<8)|(255-i)
for phase in range(6):call('h1pal_scene_switch',bg,scene,phase)
assert frame(scene)==frame(bg),'transition lost the new edges'
# A sprite crossing x=0 draws into the extra left columns without changing
# its 8x8 shape. Repeat for the core's shadow, color-shift and mono variants.
rle=0x81810000;m.write(rle,struct.pack('<HHB',8,8,64)+bytes([77])*64)
for name,extra in (('PAL_RLEBlitToSurface',()),('PAL_RLEBlitToSurfaceWithShadow',(0,)),
                   ('PAL_RLEBlitWithColorShift',(2,)),('PAL_RLEBlitMonoColor',(32,1))):
    call(name,rle,scene,((30<<16)|0xfffb),*extra)
    wide=frame(scene);assert wide[32*360+15]!=expected[32*360+15],name
    assert wide[32*360+20:32*360+23]==data(scene)[30*320:30*320+3],name
    assert wide[32*360+14]==expected[32*360+14] and wide[32*360+23]==expected[32*360+23],name
# Palette shifts and waves must cover the new columns as well as the centre.
m.write(battle+bf['sBackgroundColorShift'],struct.pack('<h',3))
base=frame(bg);shifted=bytes((i&240)|min(15,(i&15)+3) for i in base)
m.write(pixels(scene),crop(shifted));call('h1pal_battle_make_background')
assert frame(scene)==shifted and data(scene)==crop(shifted)
m.write(g+gf['wScreenWave'],struct.pack('<H',255));call('h1pal_battle_make_background')
assert len(frame(scene))==360*204
call('h1pal_platform_present',scene)
# Mode changes still redraw a static battle immediately.
for mode,width in ((1,435),(2,320),(0,480)):
    m.physical_keys.add(19);call('h1pal_platform_pump');m.physical_keys.clear();call('h1pal_platform_pump')
    assert word(m.meta['symbols']['width'])==width
m.word(g+gf['fInBattle'],0)
assert call('h1pal_scene_pixels',scene)==0,'stale battle margins outside combat'
call('SDL_FreeSurface',scene);call('SDL_FreeSurface',bg);call('h1pal_scene_shutdown');call('h1pal_platform_close')
assert not m.allocations and not m.handles
r={'ok':True,'sha256':m.meta['sha256'],'background_scale':'9/8','display_scale':'4/3',
   'fullscreen':[480,272],'coordinate_grid_verified':True,'four_rle_variants_at_edge':True,
   'palette_shift':True,'max_wave':True,'modes':3,'clean_exit':True,'seconds':round(time.monotonic()-started,2)}
(ROOT/'build/verification/wide-battle.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
