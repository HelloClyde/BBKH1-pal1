"""Render isolated RIX music through the actual MIPS audio mixer, with no SFX.

The default fixture is an original one-note RIX, suitable for public CI.
--resources additionally exercises the owner's real title/map/battle tracks.
"""
from pathlib import Path
import argparse,json,math,struct,wave
from unicorn.mips_const import UC_MIPS_REG_RA,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_V0,UC_MIPS_REG_PC
from mips_smoke import PalMachine,DATA

ROOT=Path(__file__).resolve().parents[1]

def fixture():
    # Header, one two-operator instrument, then instrument/volume/note/delay.
    rix=bytearray(84)
    struct.pack_into('<H',rix,0,0x55aa)
    struct.pack_into('<H',rix,8,20)
    struct.pack_into('<H',rix,12,84)
    operator=[0,1,0,15,0,1,0,8,0,0,0,0,1]
    struct.pack_into('<28H',rix,20,*(operator+operator+[0,0]))
    rix+=bytes([0,0x90,127,0xb0,60,0xc0,0xff,0x7f,0,0x80])
    return struct.pack('<3I',12,12,12+len(rix))+rix

class MusicMachine(PalMachine):
    def call(self,name,*args):
        self.finished=False;self.uc.reg_write(UC_MIPS_REG_RA,0x80001ff0)
        for reg,arg in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),args):self.uc.reg_write(reg,arg)
        pc=self.meta['symbols'][name]
        for _ in range(20):
            self.uc.emu_start(pc,0,timeout=20_000_000,count=200_000_000)
            if self.finished:break
            pc=self.uc.reg_read(UC_MIPS_REG_PC)
        assert self.finished,name
        return self.uc.reg_read(UC_MIPS_REG_V0)
    def render(self):
        buffer=0x81810000
        self.call('AUDIO_FillBuffer',0,buffer,2048)
        return self.read(buffer,2048)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--resources',type=Path)
    args=ap.parse_args()
    files={(DATA+'PAL9588.PAK').lower():args.resources.read_bytes()} if args.resources else {(DATA+'mus.mkf').lower():fixture()}
    m=MusicMachine(ROOT/'build/release/H1PAL.bda',files,999999)
    # Follow the real startup sequence, including C++ static constructors.
    m.call('h1_run_init_array')
    m.call('PAL_LoadConfig',1);m.call('UTIL_Platform_Init',0,0)
    assert m.call('AUDIO_OpenDevice')==0
    assert not any(m.render()),'music must initially be silent'
    tracks=[]
    for track in ((4,31,37) if args.resources else (1,)):
        m.call('AUDIO_PlayMusic',0,0,0);m.render()
        m.call('AUDIO_PlayMusic',track,1,0)
        pcm=b''.join(m.render() for _ in range(24))
        samples=struct.unpack('<'+str(len(pcm)//2)+'h',pcm)
        peak=max(map(abs,samples));rms=math.sqrt(sum(v*v for v in samples)/len(samples))
        assert peak>100 and rms>10,(track,peak,rms)
        m.call('AUDIO_EnableMusic',0);assert not any(m.render()),'SFX-free mute must be silent'
        m.call('AUDIO_EnableMusic',1);assert any(m.render()),'music did not resume'
        tracks.append({'track':track,'peak':peak,'rms':round(rms,2)})
        if args.resources:
            with wave.open(str(ROOT/f'build/verification/music-{track}.wav'),'wb') as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(22050);f.writeframes(pcm)
    m.call('AUDIO_PlayMusic',0,0,0);assert not any(m.render())
    m.call('AUDIO_CloseDevice');m.call('PAL_FreeConfig');m.call('h1pal_files_close')
    # Match h1_app_main's final arena cleanup (upstream SOUND_Shutdown leaves
    # its outer SOUNDPLAYER allocation for the application to reclaim).
    m.call('h1pal_allocations_free')
    assert not m.handles and not m.allocations and not m.audio_active,(m.handles,[hex(p) for p in m.allocations],m.audio_active)
    report={'ok':True,'sha256':m.meta['sha256'],'kind':'actual MIPS RIX/DBOPL mixer; no sound effects',
            'fixture':'owner resources' if args.resources else 'original synthetic RIX',
            'tracks':tracks,'mute_resume_stop':True,'clean_exit':True}
    out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
    (out/('music-resources.json' if args.resources else 'music.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
