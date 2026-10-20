"""Decode an original synthetic H.264/PCM AVI through the real MIPS player."""
from pathlib import Path
import base64,hashlib,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.mips_const import UC_MIPS_REG_A0
from music import MusicMachine,DATA,ROOT

fixture=json.loads((ROOT/'tests/fixtures/h264-video.json').read_text())
avi=base64.b64decode(fixture['avi_base64'])

class VideoMachine(MusicMachine):
    def __init__(self,data,skip=0):
        self.skip=skip;self.skipped=False
        super().__init__(ROOT/'build/release/H1PAL.bda',{(DATA+'clip.avi').lower():data},999999)
        self.last_injected=1
    def event(self,code,key,*args):
        frame=int.from_bytes(self.read(self.meta['symbols']['g_presented_frames'],4),'little')
        if self.skip and frame>=self.skip and not self.skipped:
            self.skipped=True;self.events.extend([(9,24),(10,24)])
        return super().event(code,key,*args)

def run(data,*,skip=0,bad=False):
    m=VideoMachine(data,skip);shots=[]
    m.call('h1_run_init_array');m.call('PAL_LoadConfig',1);m.call('UTIL_Platform_Init',0,0)
    assert m.call('h1pal_platform_open')==1
    assert m.call('VIDEO_Startup')==0
    assert m.call('AUDIO_OpenDevice')==0
    m.call('PAL_AVIInit')
    def capture(uc,address,size,user):
        surface=uc.reg_read(UC_MIPS_REG_A0)
        w,h,pitch,pixels=struct.unpack('<IIH2xI',m.read(surface+8,16))
        assert (w,h,pitch)==(64,48,128)
        digest=hashlib.sha256(m.read(pixels,pitch*h)).hexdigest()
        assert digest==fixture['rgb555_sha256'][len(shots)%fixture['frames']]
        shots.append(digest)
    address=m.meta['symbols']['H1PAL_DrawAVISurface']
    m.uc.hook_add(UC_HOOK_CODE,capture,begin=address,end=address)
    filename=0x81800000;m.write(filename,b'clip.avi\0')
    result=m.call('PAL_PlayAVI',filename)
    if bad:
        assert not result and not shots and m.call('h1pal_h264_failed')
    else:
        assert result and len(shots)==(skip or fixture['frames'])
        assert int.from_bytes(m.read(m.meta['symbols']['g_exit_keys'],4),'little')==(1 if skip else 0)
        if not skip:
            assert m.call('PAL_PlayAVI',filename)==1
            assert len(shots)==fixture['frames']*2,'second movie retained old decoder state'
    m.call('PAL_AVIShutdown');m.call('AUDIO_CloseDevice');m.call('VIDEO_Shutdown')
    m.call('h1pal_platform_close');m.call('PAL_FreeConfig');m.call('h1pal_files_close');m.call('h1pal_allocations_free')
    assert not m.handles and not m.allocations and not m.audio_active and not m.gui_active
    if not skip and not bad:assert any(any(b) for b in m.audio_observed),'video audio was silent'
    return m.meta['sha256']

sha=run(avi);run(avi,skip=3)
# A high-profile SPS is outside the H1 encoder contract. Refuse it cleanly.
bad=bytearray(avi);sps=bad.index(b'\0\0\0\1\x67');bad[sps+5]=100
run(bad,bad=True)
report={'ok':True,'sha256':sha,'fixture':'original synthetic 64x48 H.264 Baseline and PCM sine',
        'decoded_rgb555_matches_reference':True,'frames':fixture['frames'],'reopen_movie':True,
        'skip_with_cancel':True,'unsupported_profile_clean_failure':True,'nonzero_audio':True,'clean_exit':True}
out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
(out/'h264-video.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
