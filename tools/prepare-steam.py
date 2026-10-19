"""Pack the owner's Steam data and preserve original AVI video without re-encoding."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,struct,subprocess
from palpak import pack_directory,verify_archive
ROOT=Path(__file__).resolve().parents[1]
CORE='0.RPG ABC.MKF BALL.MKF DATA.MKF F.MKF FBP.MKF FIRE.MKF GOP.MKF MAP.MKF MGO.MKF MIDI.MKF MUS.MKF PAT.MKF RGM.MKF RNG.MKF SSS.MKF VOC.MKF M.MSG WORD.DAT WOR16.ASC wor16.FON'.split()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def video_hash(p):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','hash','-hash','sha256','-'],text=True).strip()
def largest_payload(data,start,end):
    pos=start;largest=0
    while pos+8<=end:
        tag,length=struct.unpack_from('<4sI',data,pos);payload=pos+8
        if payload+length>end:raise ValueError('truncated AVI chunk')
        if tag==b'LIST':largest=max(largest,largest_payload(data,payload+4,payload+length))
        elif tag in (b'00dc',b'00db',b'01wb'):largest=max(largest,length)
        pos=payload+length+(length&1)
    if pos!=end:raise ValueError('invalid AVI chunk alignment')
    return largest
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--steam-root',type=Path,required=True,help='PAL folder containing PAL_DOS and PAL98')
    ap.add_argument('--output',type=Path,default=ROOT/'build/steam-resources')
    args=ap.parse_args();out=args.output.resolve();core=out/'core';video=out/'video'
    for d in (core,video):d.mkdir(parents=True,exist_ok=True)
    dos=args.steam_root/'PAL_DOS';pal98=args.steam_root/'PAL98'
    inputs={p.name.lower():p for p in dos.iterdir() if p.is_file()}
    for name in CORE:shutil.copyfile(inputs[name.lower()],core/name)
    spec=importlib.util.spec_from_file_location('prepare_avi',ROOT/'tools/prepare-pal-avi.py')
    normalizer=importlib.util.module_from_spec(spec);spec.loader.exec_module(normalizer)
    reports=[]
    for i in range(1,7):
        src=pal98/f'{i}.AVI';dest=video/f'{i}.avi';shutil.copyfile(src,dest)
        prepared=normalizer.prepare(dest)
        # The decoder has a bounded chunk buffer. Check actual payloads too.
        data=dest.read_bytes();movi=data.index(b'movi');end=movi+struct.unpack_from('<I',data,movi-4)[0]
        largest=largest_payload(data,movi+4,end)
        if not largest or largest>prepared['suggested_buffer_after']:
            raise ValueError(f'{src.name}: original AVI chunks exceed the playback buffer')
        decoded=video_hash(src)
        if decoded!=video_hash(dest):raise ValueError(f'{src.name}: video changed during normalization')
        report={'source':str(src),'source_sha256':sha(src),'sha256':sha(dest),'decoded_video_hash':decoded,
            'video_bit_exact':True,'video_reencoded':False,'largest_chunk':largest,**prepared}
        reports.append(report);print(src.name,'video unchanged, bytes',dest.stat().st_size,flush=True)
    for source,name in ((core,'PAL9588.PAK'),(video,'PALVIDEO.PAK')):
        pack_directory(source,out/name);verify_archive(out/name)
    report={'steam_root':str(args.steam_root),'core_files':len(CORE),'videos':reports,
        'packages':{name:{'size':(out/name).stat().st_size,'sha256':sha(out/name)} for name in ('PAL9588.PAK','PALVIDEO.PAK')}}
    (out/'steam-resources.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['packages'],indent=2))
if __name__=='__main__':main()
