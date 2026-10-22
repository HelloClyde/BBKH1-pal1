"""Pixel checks for full-width UI, without rescaling baked-in menu artwork."""
from pathlib import Path
import importlib.util,json,struct,time
from unicorn.mips_const import UC_MIPS_REG_RA,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_SP,UC_MIPS_REG_V0
from scaling_reference import sample,close
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
def pixels(surface):return word(surface+20)
def crop(frame):return b''.join(frame[(y+2)*360+20:(y+2)*360+340] for y in range(200))
start=time.monotonic();assert call('h1pal_platform_open')==1
s=call('SDL_CreateRGBSurface',0,320,200,8,0,0,0,0)
backup=call('SDL_CreateRGBSurface',0,320,200,8,0,0,0,0)
palette=0x81800000;m.write(palette,bytes(v for i in range(256) for v in (i,255-i,i^85,0)))
call('SDL_SetPalette',s,3,palette,0,256);call('SDL_SetPalette',backup,3,palette,0,256)
raw=bytes((x+3*y)%256 for y in range(200) for x in range(320))
for cover in (0,1):
    m.write(pixels(s),raw);call('h1pal_ui_background',s,cover)
    frame_address=call('h1pal_scene_pixels',s);assert frame_address
    frame=m.read(frame_address,360*204)
    if not cover:
        assert m.read(pixels(s),64000)==raw and crop(frame)==raw,'status/portrait/slot artwork changed'
        for x,y in ((0,0),(359,203),(5,60),(355,70)):
            sy=max(0,min(199,y-2));sx=312+((x-20+320)&7)
            assert frame[y*360+x]==raw[sy*320+sx]
    else:
        expected=bytes(raw[((y*8+84)//9)*320+x*8//9] for y in range(204) for x in range(360))
        assert frame==expected and m.read(pixels(s),64000)==crop(expected)
    call('h1pal_platform_present',s)
    assert word(m.meta['symbols']['width'])==480 and word(m.meta['symbols']['height'])==272
    for x,y in ((0,0),(479,0),(0,271),(479,271),(240,136)):
        colors=[(i,255-i,i^85) for i in range(256)]
        expected=sample(raw,320,200,colors,x,y,480,300,14) if cover else sample(frame,360,204,colors,x,y)
        assert close(word(0x82000000+(y*480+x)*4),expected),'sharp/single-pass cover mismatch'
    call('h1pal_scene_copy',s,backup)
    assert m.read(call('h1pal_scene_pixels',backup),360*204)==frame
    assert call('h1pal_scene_battle_pixels',s)==0,'menu misclassified as battle background'
# A square icon remains 8x8 and can draw into the new UI margin.
rle=0x81810000;m.write(rle,struct.pack('<HHB',8,8,64)+bytes([77])*64)
call('PAL_RLEBlitToSurface',rle,s,(30<<16)|0xfffb)
frame=m.read(call('h1pal_scene_pixels',s),360*204)
assert all(frame[y*360+x]==77 for y in range(32,40) for x in range(15,23))
assert m.read(pixels(s)+30*320,3)==bytes([77])*3
# Selection markers stay in the left gutter, centred on a 16-pixel text row.
for text_x,text_y in ((35,54),(15,12),(122,72),(215,90)):
    m.write(pixels(s),bytes([17])*64000)
    call('h1pal_ui_cursor',s,text_x,text_y)
    image=m.read(pixels(s),64000)
    white=[(x,y) for y in range(200) for x in range(320) if image[y*320+x]==63]
    assert len(white)==16 and min(x for x,y in white)==text_x-6 and max(x for x,y in white)==text_x-3
    assert min(y for x,y in white)==text_y+4 and max(y for x,y in white)==text_y+10
    assert all(image[y*320+x]==17 for y in range(text_y,text_y+16) for x in range(text_x,text_x+80)),'cursor overlapped text'
# Unused letter keys cannot change a full-screen UI/battle.
for key in (16,17,19,23):
    m.physical_keys.add(key);call('h1pal_platform_pump')
    assert word(m.meta['symbols']['width'])==480
    m.physical_keys.clear();call('h1pal_platform_pump')
call('SDL_FreeSurface',backup);call('SDL_FreeSurface',s);call('h1pal_scene_shutdown');call('h1pal_platform_close')
assert not m.allocations and not m.handles
r={'ok':True,'sha256':m.meta['sha256'],'fullscreen':[480,272],'central_status_pixels_identical':True,
   'title_uniform_cover':True,'portrait_slot_geometry_preserved':True,'uniform_display':'4/3',
   'backup_restore':True,'icon_at_new_edge':True,'cursor_no_text_overlap':True,'fixed_fullscreen':True,'clean_exit':True,'seconds':round(time.monotonic()-start,2)}
(ROOT/'build/verification/wide-ui.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
