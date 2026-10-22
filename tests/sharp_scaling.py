"""Test fused sharp scaling, cached original backgrounds and foreground ownership."""
from pathlib import Path
import json,struct,time
from unicorn.mips_const import UC_MIPS_REG_RA,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_V0,UC_MIPS_REG_SP
from music import MusicMachine
from scaling_reference import sample,close
ROOT=Path(__file__).resolve().parents[1]

def main():
    m=MusicMachine(ROOT/'build/release/H1PAL.bda',{},999999)
    def call(name,*args):
        m.finished=False;m.uc.reg_write(UC_MIPS_REG_RA,0x80001ff0)
        for reg,value in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),args):m.uc.reg_write(reg,value)
        sp=m.uc.reg_read(UC_MIPS_REG_SP)
        for i,value in enumerate(args[4:]):m.word(sp+16+i*4,value)
        m.uc.emu_start(m.meta['symbols'][name],0,timeout=20_000_000,count=100_000_000)
        assert m.finished,name
        return m.uc.reg_read(UC_MIPS_REG_V0)
    def word(address):return int.from_bytes(m.read(address,4),'little')
    def pixel(x,y):return word(0x82000000+(y*480+x)*4)
    scratch=0x81800000
    # Rational 4/3 phase: pure pixels at plateaus, quarter blends at boundaries.
    call('h1pal_scale_axis',scratch,480,360,480,0)
    assert [v[2] for v in struct.iter_unpack('<3H',m.read(scratch,24))]==[256,192,64,0]
    assert call('h1pal_platform_open')==1
    surface=call('SDL_CreateRGBSurface',0,320,200,8,0,0,0,0)
    backup=call('SDL_CreateRGBSurface',0,320,200,8,0,0,0,0)
    pixels=word(surface+20)
    colors=[(i,(i*7)%256,255-i) for i in range(256)]
    palette=scratch+0x1000;m.write(palette,bytes(v for c in colors for v in (*c,0)))
    call('SDL_SetPalette',surface,3,palette,0,256);call('SDL_SetPalette',backup,3,palette,0,256)
    raw=bytes((x*13+y*5)%256 for y in range(200) for x in range(320))
    m.write(pixels,raw);call('h1pal_ui_background',surface,1);call('h1pal_platform_present',surface)
    points=[(x,y) for y in (0,1,2,51,135,136,270,271) for x in (0,1,2,3,47,239,240,478,479)]
    for x,y in points:assert close(pixel(x,y),sample(raw,320,200,colors,x,y,480,300,14)),(x,y)
    builds=word(m.meta['symbols']['h1pal_cover_builds']);assert builds==1
    original=m.read(0x82000000,480*272*4)
    call('h1pal_platform_present',surface)
    assert word(m.meta['symbols']['h1pal_cover_builds'])==builds,'unchanged palette rebuilt background'
    # A nested menu saves only its rectangle, rather than the entire screen.
    part=call('SDL_CreateRGBSurface',0,64,40,8,0,0,0,0)
    rect=scratch+0x3000;m.write(rect,struct.pack('<hhHH',70,40,64,40))
    call('SDL_UpperBlit',surface,rect,part,0)
    call('SDL_FillRect',surface,rect,77);call('h1pal_platform_present',surface)
    call('SDL_UpperBlit',part,0,surface,rect);call('SDL_FreeSurface',part)
    call('h1pal_platform_present',surface)
    assert m.read(0x82000000,480*272*4)==original,'partial menu restore lost cover metadata'
    # Same-color paint must still own its whole foreground footprint.
    rle=scratch+0x2000
    # Use a compact single-run 8x8 RLE, well inside the canvas.
    m.write(rle,struct.pack('<HHB',8,8,64)+bytes([77])*64)
    call('PAL_RLEBlitToSurface',rle,surface,(80<<16)|100)
    call('h1pal_platform_present',surface)
    expected=(77<<16)|(colors[77][1]<<8)|colors[77][2]
    assert all(pixel(x,y)==expected for y in range(112,118) for x in range(163,169)),'sprite blended into original background'
    # Copies retain original art, masks and the shared cache; freeing either
    # surface cannot leave the other's cover image dangling.
    call('SDL_UpperBlit',surface,0,backup,0)
    call('SDL_FreeSurface',surface);call('h1pal_platform_present',backup)
    assert pixel(0,0)==int.from_bytes(original[:4],'little')
    colors2=[(255-r,g,b) for r,g,b in colors]
    m.write(palette,bytes(v for c in colors2 for v in (*c,0)))
    call('SDL_SetPalette',backup,3,palette,0,256);call('h1pal_platform_present',backup)
    assert word(m.meta['symbols']['h1pal_cover_builds'])==builds+1
    assert close(pixel(0,0),sample(raw,320,200,colors2,0,0,480,300,14))
    call('SDL_FreeSurface',backup);call('h1pal_scene_shutdown');call('h1pal_platform_close')
    assert not m.handles and not m.allocations and not m.gui_active
    report={'ok':True,'sha256':m.meta['sha256'],'kind':'actual MIPS with modeled H1 services; synthetic artwork',
        'filter':'fused nearest 2x prescale + bilinear, Q8, pixel-centred',
        'original_cover_sampled_once':True,'fullscreen':[480,272],'reference_points':len(points),
        'channel_isolation':True,'foreground_ownership':True,'palette_cache_invalidation':True,
        'shared_cover_lifetime':True,'partial_menu_restore':True,'clean_exit':True}
    out=ROOT/'build/verification';out.mkdir(exist_ok=True)
    (out/'sharp-scaling.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
