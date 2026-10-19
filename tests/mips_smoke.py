"""Execute the real H1PAL BDA with modeled H1 tables; separate from full firmware QA."""
from pathlib import Path
import argparse,io,json,struct,sys,time
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent
sys.path.insert(0,str(ROOT/'tests'))
from h1_model import Machine
from unicorn.mips_const import UC_MIPS_REG_PC
from PIL import Image
DATA='A:\\应用\\数据\\PAL\\'
class PalMachine(Machine):
    def __init__(self,bda,files,limit=140):
        self.meta=json.loads(bda.with_suffix('.build.json').read_text())
        self.limit=limit;self.last_injected=0;self.fseek_calls=0
        super().__init__(bda,files=files,path=None)
    def fopen(self,path,mode,*a):
        p,m=self.string(path).lower(),self.string(mode)
        if 'w' not in m and 'a' not in m and p not in self.files:return 0
        handle=self.next_handle;self.next_handle+=1
        f=io.BytesIO(b'' if 'w' in m else self.files.get(p,b''))
        if 'a' in m:f.seek(0,2)
        self.handles[handle]=(p,m,f);return handle
    def fclose(self,h,*a):
        p,m,f=self.handles.pop(h)
        if any(c in m for c in 'wa+'):self.files[p]=f.getvalue()
        return 0
    def fread(self,ptr,size,count,h,*a):
        assert size==1
        return super().fread(ptr,size,count,h,*a)
    def fseek(self,*a):self.fseek_calls+=1;return super().fseek(*a)
    def stats(self):return struct.unpack('<8I',self.read(self.meta['symbols']['h1pal_stats'],32))
    def event(self,code,key,*a):
        frames=self.stats()[2]
        if frames>=self.limit and self.last_injected!=99999:self.events.append((9,41));self.last_injected=99999
        elif frames>=5 and self.last_injected==0:self.events.extend([(9,25),(10,25)]);self.last_injected=1
        e=self.events.pop(0) if self.events else (-1,-1)
        self.word(code,e[0]);self.word(key,e[1]);return 0
    def clock(self,*a):
        # Read-only raw tick and ms timer are distinct firmware interfaces.
        return super().clock(*a)
    def image(self):
        rgb=self.read(0x82000000,480*272*4);return Image.frombytes('RGB',(480,272),rgb,'raw','BGRX')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--missing',action='store_true');ap.add_argument('--limit',type=int,default=140)
    args=ap.parse_args();files={}
    if not args.missing:files[(DATA+'PAL9588.PAK').lower()]=(ROOT/'build/resources/PAL9588.PAK').read_bytes()
    out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
    m=PalMachine(ROOT/'build/release/H1PAL.bda',files,args.limit)
    start=time.monotonic()
    if args.missing:
        # Missing resources show a native dialog and still return without leaks.
        from unicorn.mips_const import UC_MIPS_REG_SP,UC_MIPS_REG_V0
        m.uc.emu_start(0x83c00020,0,timeout=60_000_000,count=100_000_000)
        assert m.finished and m.dialogs
        assert not m.handles and not m.allocations
        assert not m.gui_active and m.gui_opens==m.gui_closes
    else:
        try:m.run()
        except Exception:
            print('stats',m.stats(),'ticks',m.ticks,'log',m.files.get((DATA+'H1PAL.LOG').lower()),flush=True)
            m.image().save(out/'mips-incomplete.png')
            raise
        assert m.stats()[2]>=args.limit,m.stats()
        assert m.audio_submissions and m.audio_observed
        # This bounded trademark-screen run checks DMA ownership and cleanup.
        # Music content and continuous playback are checked in full firmware.
        m.image().save(out/'mips-game.png')
    report={'ok':True,'kind':'cross-compiled MIPS with modeled H1 services','missing':args.missing,'stats':m.stats(),
        'seconds':round(time.monotonic()-start,2),'seeks':m.fseek_calls,'sha256':m.meta['sha256'],'leaked_handles':len(m.handles),'leaked_allocations':len(m.allocations)}
    (out/('missing.json' if args.missing else 'mips-smoke.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
