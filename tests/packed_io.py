"""Actual MIPS packed character I/O, shared-handle isolation and startup I/O budget."""
from pathlib import Path
import collections,json,sys,tempfile
from music import MusicMachine,fixture
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from palpak import pack_directory

class IOMachine(MusicMachine):
    def __init__(self,*args):
        self.native_reads=collections.Counter()
        super().__init__(*args)
    def fread(self,pointer,size,count,handle,*args):
        self.native_reads[size*count]+=1
        return super().fread(pointer,size,count,handle,*args)

def main():
    text=b'a'*4094+b'\r\n'+b'b'*6000+b'\n'+b'\x80\xff END'
    with tempfile.TemporaryDirectory() as temporary:
        directory=Path(temporary);source=directory/'source';source.mkdir()
        # A procedural RIX plus padding exercises the same upstream byte loop
        # as a large real music archive, without distributing game resources.
        (source/'mus.mkf').write_bytes(fixture()+bytes(512*1024))
        (source/'probe.txt').write_bytes(text)
        (source/'other.txt').write_bytes(b'Other stream\n')
        (source/'empty.txt').write_bytes(b'')
        pack_directory(source,directory/'test.pak');archive=(directory/'test.pak').read_bytes()
    path='B:\\应用\\数据\\PAL\\'
    m=IOMachine(ROOT/'build/release/H1PAL.bda',{(path+'PAL9588.PAK').lower():archive},999999)
    m.call('h1_run_init_array');assert m.call('h1pal_select_data_path')==1
    scratch=0x81800000;output=scratch+0x1000
    def open_file(name):
        m.write(scratch,name.encode()+b'\0');m.write(scratch+256,b'rb\0')
        handle=m.call('h1pal_fopen_data',scratch,scratch+256);assert handle;return handle
    def line(handle,expected):
        assert m.call('fgets',output,8192,handle)==output
        assert m.read(output,len(expected)+1)==expected+b'\0'
    before=len(m.allocations);a=open_file('probe.txt');b=open_file('other.txt')
    line(a,text[:4096]);assert m.call('ftell',a)==4096 and not m.call('feof',a)
    assert m.call('fgetc',b)==ord('O')
    assert m.call('fread',output,1,100,a)==100 and m.read(output,100)==b'b'*100
    assert m.call('fseek',a,(-100)&0xffffffff,1)==0
    line(a,b'b'*6000+b'\n');line(a,b'\x80\xff END')
    assert m.call('feof',a) and not m.call('fgets',output,8192,a)
    assert m.call('fseek',a,(-6)&0xffffffff,2)==0 and not m.call('feof',a)
    assert m.call('fgetc',a)==128 and m.call('fgetc',a)==255
    line(b,b'ther stream\n')
    m.call('fclose',a);m.call('fclose',b)
    empty=open_file('empty.txt');assert m.call('fgetc',empty)==0xffffffff and m.call('feof',empty)
    m.call('fclose',empty)
    reopened=open_file('other.txt');line(reopened,b'Other stream\n');m.call('fclose',reopened)
    assert len(m.allocations)==before,'character buffers were not freed on close'
    m.call('PAL_LoadConfig',1);m.call('UTIL_Platform_Init',0,0)
    m.native_reads.clear();seeks=m.fseek_calls
    assert m.call('AUDIO_OpenDevice')==0
    reads=sum(m.native_reads.values());one_byte=m.native_reads[1];seeks=m.fseek_calls-seeks
    assert one_byte==0 and reads<256 and seeks<256,(reads,seeks,one_byte)
    m.call('AUDIO_CloseDevice');m.call('PAL_FreeConfig');m.call('h1pal_files_close');m.call('h1pal_allocations_free')
    assert not m.handles and not m.allocations and not m.audio_active
    report={'ok':True,'sha256':m.meta['sha256'],'kind':'actual MIPS with modeled H1 services; synthetic B-drive PAK',
        'crosses_4096_byte_boundaries':True,'shared_archive_streams_independent':True,
        'bulk_and_character_reads_mix':True,'seek_and_eof':True,'unsigned_ff_character':True,
        'close_and_slot_reuse':True,'empty_member':True,'large_rix_startup_native_reads':reads,
        'large_rix_startup_native_seeks':seeks,'one_byte_native_reads':one_byte,'clean_exit':True}
    out=ROOT/'build/verification';out.mkdir(exist_ok=True)
    (out/'packed-io.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
