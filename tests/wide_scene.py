"""Compare the expanded and original map using the actual MIPS renderer."""
from pathlib import Path
import importlib.util, json, struct, time
from unicorn import UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A0, UC_MIPS_REG_PC, UC_MIPS_REG_RA
from PIL import Image, ImageChops
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pal_machine', ROOT/'tests/mips_smoke.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
DATA = mod.DATA.lower()
files = {DATA+'pal9588.pak': (ROOT/'build/resources/PAL9588.PAK').read_bytes(),
         DATA+'1.rpg': (ROOT/'build/verification/native-1.rpg').read_bytes(),
         DATA+'porttest.view': b'1'}
m = mod.PalMachine(ROOT/'build/regression/H1PAL.bda', files, 999999)
m.last_injected = 1
shots = {}
touch = [0, 0]
def get_touch(x, y, *args):
    m.write(x, struct.pack('<H', touch[0])); m.write(y, struct.pack('<H', touch[1]))
    m.uc.reg_write(UC_MIPS_REG_PC, m.uc.reg_read(UC_MIPS_REG_RA)); return 0
touch_fn = 0x80001b80; m.callbacks[touch_fn] = get_touch
m.word(0x80002000+0x6c0, touch_fn)
m.write(touch_fn, struct.pack('<6I', 0x27bdffa8, 0xafbf0050, 0, 0, 0x00a0b821, 0x0080b021))
def word(address): return struct.unpack('<I', m.read(address, 4))[0]
def surface_pixels(surface):
    w, h, pitch, pixels = struct.unpack('<IIH2xI', m.read(surface+8, 16))
    return Image.frombytes('L', (w, h), m.read(pixels, pitch*h), 'raw', 'L', pitch)
def checkpoint(uc, address, size, user):
    phase = uc.reg_read(UC_MIPS_REG_A0)
    if 10 <= phase <= 20:
        if phase in (13, 16, 19): m.physical_keys.add(19)
        else: m.physical_keys.clear()
        if phase in (11, 14, 17, 20):
            touch[:] = {11: (479, 271), 14: (456, 271), 17: (399, 235), 20: (0, 0)}[phase]
            m.events.extend([(11, 0), (8, 0)])
        return
    screen = word(m.meta['symbols']['gpScreen'])
    fmt = word(screen + 4); palette = word(fmt); colors = word(palette + 4)
    shots[phase] = {'lcd': m.image(),
                    'legacy': surface_pixels(screen), 'palette': m.read(colors, 1024),
                    'wide': surface_pixels(word(m.meta['symbols']['wide']))}
fn = m.meta['symbols']['h1pal_view_checkpoint']
m.uc.hook_add(UC_HOOK_CODE, checkpoint, begin=fn, end=fn)
started = time.monotonic(); m.run()
assert set(shots) == set(range(1, 10)) | {21}, set(shots)
log = m.files[DATA+'porttest.log'].decode()
assert 'VIEW STATE PASS' in log and 'VIEW TAP PASS' in log and 'VIEW PASS' in log, log
assert shots[1]['wide'].size == (360, 204)
assert shots[1]['wide'].crop((20, 2, 340, 202)).tobytes() == shots[4]['legacy'].tobytes(), 'central view changed'
assert shots[1]['lcd'].tobytes() == shots[3]['lcd'].tobytes(), 'menu restore lost map margins'
assert shots[3]['lcd'].tobytes() == shots[21]['lcd'].tobytes(), 'partial UI refresh lost map margins'
assert shots[2]['lcd'].crop((0, 0, 22, 272)).getbbox() is None, 'fixed background stretched'
assert shots[1]['lcd'].crop((0, 0, 22, 272)).getbbox(), 'extra map columns missing'
indices = shots[1]['wide'].tobytes(); palette = shots[1]['palette']
expected = b''.join(palette[4*indices[(y*3//4)*360+x*3//4]:4*indices[(y*3//4)*360+x*3//4]+3]
                    for y in range(272) for x in range(480))
assert expected == shots[1]['lcd'].tobytes(), 'map was not uniformly scaled by 4/3'
assert shots[8]['lcd'].crop((0, 0, 22, 272)).getbbox() is None, 'battle reused map margins'
assert shots[9]['lcd'].crop((0, 5, 22, 265)).getbbox(), 'screen shake lost map margins'
npc_difference = ImageChops.difference(shots[5]['wide'], shots[6]['wide'])
assert npc_difference.crop((0, 0, 20, 204)).getbbox(), 'NPC outside old viewport was culled'
assert not m.allocations and not m.handles and not m.gui_active and not m.audio_active
out = ROOT/'build/verification'; out.mkdir(exist_ok=True)
shots[1]['lcd'].save(out/'expanded-map.png')
shots[4]['lcd'].save(out/'original-view.png')
shots[5]['lcd'].save(out/'expanded-npc.png')
shots[7]['lcd'].save(out/'expanded-wave.png')
shots[1]['wide'].save(out/'expanded-map-indices.png')
report = {'ok': True, 'sha256': m.meta['sha256'], 'logical_map': [360, 204],
          'uniform_scale': '4/3', 'legacy_crop_identical': True, 'world_state_unchanged': True,
          'menu_restore_identical': True, 'partial_ui_refresh': True, 'outside_npc_drawn': True, 'max_wave_rendered': True,
          'touch_all_modes_and_new_edges': True, 'uniform_pixels_verified': True, 'battle_margins_cleared': True,
          'seconds': round(time.monotonic()-started, 2), 'log': log,
          'leaked_allocations': len(m.allocations), 'leaked_handles': len(m.handles)}
(out/'wide-scene.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
