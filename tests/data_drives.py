"""Run the real MIPS filesystem with two volumes and synthetic, copyright-free PAKs."""
from pathlib import Path
import importlib.util,json,sys,tempfile
from unicorn.mips_const import UC_MIPS_REG_RA,UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3,UC_MIPS_REG_V0

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from palpak import pack_directory
spec=importlib.util.spec_from_file_location('pal_machine',ROOT/'tests/mips_smoke.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
DIR=':\\应用\\数据\\PAL\\'

def archive(name,data):
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);source=root/'data';source.mkdir();(source/name).write_bytes(data)
        pack_directory(source,root/'test.pak')
        return (root/'test.pak').read_bytes()

class DriveMachine(mod.PalMachine):
    def __init__(self,files):
        self.opens=[];super().__init__(ROOT/'build/release/H1PAL.bda',files,999999)
    def fopen(self,path,mode,*args):
        self.opens.append((self.string(path),self.string(mode)))
        return super().fopen(path,mode,*args)
    def call(self,name,*args):
        self.finished=False;self.uc.reg_write(UC_MIPS_REG_RA,0x80001ff0)
        for reg,value in zip((UC_MIPS_REG_A0,UC_MIPS_REG_A1,UC_MIPS_REG_A2,UC_MIPS_REG_A3),args):self.uc.reg_write(reg,value)
        self.uc.emu_start(self.meta['symbols'][name],0,timeout=10_000_000,count=20_000_000)
        assert self.finished,name
        return self.uc.reg_read(UC_MIPS_REG_V0)
    def open_data(self,name,mode='rb'):
        self.write(0x81800000,name.encode('ascii')+b'\0');self.write(0x81800100,mode.encode()+b'\0')
        return self.call('h1pal_fopen_data',0x81800000,0x81800100)
    def read_data(self,name):
        f=self.open_data(name)
        if not f:return None
        count=self.call('fread',0x81800200,1,100,f);result=self.read(0x81800200,count)
        self.call('fclose',f);return result

def path(drive,name):return (drive+DIR+name).lower()
main={d:archive('probe.dat',(d+'-main').encode()) for d in ('A','B')}
video={d:archive('1.avi',(d+'-video').encode()) for d in ('A','B')}
cases=[('A only',{'A'}, {'A'},'A'),('B only',{'B'},{'B'},'B'),
       ('A wins',{'A','B'},{'A','B'},'A'),('A folder without main',{'B'},{'A','B'},'B'),
       ('B ignores A video',{'B'},{'A'},'B'),('missing both',set(),set(),'A')]
results=[]
for label,drives,videos,selected in cases:
    files={path(d,'PAL9588.PAK'):main[d] for d in drives}
    files.update({path(d,'PALVIDEO.PAK'):video[d] for d in videos})
    files[path('A','sdlpal.cfg')]=b'old-A-config'
    m=DriveMachine(files)
    assert m.call('h1pal_select_data_path')==bool(drives)
    assert m.string(m.meta['symbols']['h1pal_data_path'])==selected+DIR
    probes=[p[0][0] for p in m.opens if p[0].lower().endswith('pal9588.pak')]
    assert probes==(['A'] if 'A' in drives else ['A','B']),(label,probes)
    assert not m.handles,'volume probes must not retain raw handles'
    assert m.read_data('probe.dat')==((selected+'-main').encode() if drives else None)
    assert m.read_data('1.avi')==((selected+'-video').encode() if selected in videos else None)
    if drives:
        for name,data in [('2.rpg',b'save-roundtrip'),('sdlpal.cfg',b'config-roundtrip'),('H1PAL.LOG',b'log-roundtrip')]:
            f=m.open_data(name,'wb');assert f,(label,name)
            m.write(0x81800300,data);assert m.call('fwrite',0x81800300,1,len(data),f)==len(data)
            m.call('fclose',f);assert m.read_data(name)==data
            assert m.files[path(selected,name)]==data
        if selected=='B':
            assert m.files[path('A','sdlpal.cfg')]==b'old-A-config'
            assert path('A','2.rpg') not in m.files and path('A','H1PAL.LOG') not in m.files
    m.call('h1pal_files_close');assert not m.handles and not m.allocations
    results.append({'case':label,'selected':selected,'ok':True})

# Presence, not archive validity, decides priority. A damaged A pack must not
# silently switch the player's session onto B and its independent save files.
m=DriveMachine({path('A','PAL9588.PAK'):b'broken',path('B','PAL9588.PAK'):main['B']})
assert m.call('h1pal_select_data_path')==1
assert m.string(m.meta['symbols']['h1pal_data_path']).startswith('A:')
assert m.read_data('probe.dat') is None
assert not any(p[0].startswith('B:') for p in m.opens)
m.call('h1pal_files_close');assert not m.handles and not m.allocations
results.append({'case':'damaged A is not replaced with B','selected':'A','ok':True})
out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
report={'ok':True,'sha256':m.meta['sha256'],'kind':'actual MIPS filesystem with modeled H1 A/B volumes','cases':results,
        'selected_volume_saves_config_log':True,'video_stays_on_selected_volume':True,'clean_handles':True}
(out/'data-drives.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
