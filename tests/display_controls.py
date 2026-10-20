"""Check the six game controls, ignored shortcuts and fixed display geometry."""
from pathlib import Path
import importlib.util,json,struct
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
from unicorn.mips_const import UC_MIPS_REG_PC,UC_MIPS_REG_RA,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_V0
m=mod.PalMachine(ROOT/'build/release/H1PAL.bda',{},999999)
def call(name,*args):
    m.finished=False;m.uc.reg_write(UC_MIPS_REG_RA,0x80001ff0)
    for reg,arg in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),args):m.uc.reg_write(reg,arg)
    m.uc.emu_start(m.meta['symbols'][name],0,timeout=10_000_000,count=20_000_000)
    assert m.finished,name
    return m.uc.reg_read(UC_MIPS_REG_V0)
assert call('h1pal_platform_open')==1
# SDL 1.x compatibility structs are local to this port, with 32-bit pointers.
surface,fmt,palette,colors,pixels=0x81000000,0x81000100,0x81000200,0x81000300,0x81001000
m.write(colors,bytes([255,0,0,0])*256);m.write(palette,struct.pack('<II',256,colors))
m.write(fmt,struct.pack('<IBB',palette,8,1)+bytes(64))
m.write(surface,struct.pack('<IIIIH2xI',0,fmt,320,200,320,pixels)+bytes(64))
m.write(pixels,bytes(320*200));call('h1pal_platform_present',surface)
def pixel(x,y):return struct.unpack('<I',m.read(0x82000000+(y*480+x)*4,4))[0]
assert pixel(0,0)==0 and pixel(22,0)==0xff0000 and pixel(456,271)==0xff0000 and pixel(457,271)==0,'fixed artwork must preserve aspect ratio'
# Query native scancodes independently of the model's matrix table.
# Both event and held paths ignore all letter/space shortcuts.
query=m.game_key
raw_keys=set()
def raw_query(code,*args):return int(code in raw_keys)
for address,callback in list(m.callbacks.items()):
    if callback==query:m.callbacks[address]=raw_query
for raw,bit in ((103,1),(108,2),(105,4),(106,8),(28,16),(1,32)):
    raw_keys.add(raw);assert call('h1pal_platform_keys')==bit
    call('h1pal_platform_keys');assert call('h1pal_platform_keys')==bit
    raw_keys.clear();assert call('h1pal_platform_keys')==0
for raw,matrix in ((44,16),(45,17),(47,19),(57,23)):
    before=m.read(0x82000000,480*272*4)
    raw_keys.add(raw);m.events.extend([(9,matrix),(10,matrix)])
    for _ in range(4):
        m.ticks+=500;assert call('h1pal_platform_keys')==0
    assert m.read(0x82000000,480*272*4)==before,'unused key changed display'
    raw_keys.clear();assert call('h1pal_platform_keys')==0
for address,callback in list(m.callbacks.items()):
    if callback==raw_query:m.callbacks[address]=query
# AVI uses the same screen geometry, including the right/bottom endpoints.
m.write(pixels,struct.pack('<4H',0x7c00,0x03e0,0x001f,0x7fff))
call('h1pal_platform_present_rgb555',pixels,2,2,2)
assert [pixel(x,y) for x,y in ((22,0),(456,0),(22,271),(456,271))]==[0xff0000,0x00ff00,0x0000ff,0xffffff]
assert pixel(0,0)==0 and pixel(479,271)==0
# Tap inversion must agree with fixed artwork geometry.
touch=[0,0]
def get_touch(x,y,*a):
    m.write(x,struct.pack('<H',touch[0]));m.write(y,struct.pack('<H',touch[1]))
    m.uc.reg_write(UC_MIPS_REG_PC,m.uc.reg_read(UC_MIPS_REG_RA));return 0
fn=0x80001b80;m.callbacks[fn]=get_touch;m.word(0x80002000+0x6c0,fn)
m.write(fn,struct.pack('<6I',0x27bdffa8,0xafbf0050,0,0,0x00a0b821,0x0080b021))
for w,h,left,top in ((435,272,22,0),):
    touch[:]=[left+w-1,top+h-1];m.events.extend([(11,0),(8,0)]);call('h1pal_platform_pump')
    assert call('h1pal_platform_take_tap',surface,surface+4)==1
    assert struct.unpack('<2I',m.read(surface,8))==((w-1)*320//w,(h-1)*200//h)
# Exercise the engine-to-SDL path too: the game's whole 320x200 canvas must
# reach the whole LCD, including when the legacy SDL 1.x scaler is involved.
assert call('VIDEO_Startup')==0
screen=int.from_bytes(m.read(m.meta['symbols']['gpScreen'],4),'little')
screen_pixels=int.from_bytes(m.read(screen+20,4),'little')
m.write(screen_pixels,bytes([1])*(320*200))
engine_palette=0x81810000
m.write(engine_palette,bytes(4)+bytes([255,255,255,0])*255)
call('VIDEO_SetPalette',engine_palette)
call('VIDEO_UpdateScreen',0)
assert all(pixel(x,y)==0xffffff for x,y in ((22,0),(456,0),(22,271),(456,271))), 'engine added top/bottom bars'
call('VIDEO_Shutdown')
call('h1pal_platform_close');assert not m.gui_active and not m.handles
assert not m.allocations
r={'ok':True,'six_controls':True,'letter_space_shortcuts_ignored':True,'fixed_artwork_aspect':True,'engine_canvas_corners':True,'avi_corners':True,'touch_coordinates':True,'sha256':m.meta['sha256']}
(ROOT/'build/verification/display-controls.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
