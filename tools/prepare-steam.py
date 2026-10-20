"""Pack owner-supplied Steam data, with H1-friendly H.264 Baseline video."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,struct,subprocess
from palpak import pack_directory,verify_archive
ROOT=Path(__file__).resolve().parents[1]
CORE='0.RPG ABC.MKF BALL.MKF DATA.MKF F.MKF FBP.MKF FIRE.MKF GOP.MKF MAP.MKF MGO.MKF MIDI.MKF MUS.MKF PAT.MKF RGM.MKF RNG.MKF SSS.MKF VOC.MKF M.MSG WORD.DAT WOR16.ASC wor16.FON'.split()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def video_hash(p):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-f','hash','-hash','sha256','-'],text=True).strip()

def audio_hash(p):
    return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-'],text=True).strip()

def video_info(p):
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,profile,width,height,r_frame_rate,nb_frames','-of','json',str(p)],text=True))
    return info['streams'][0]

def transcode_h264(source,destination,crf=18):
    # Single reference, no CABAC/B frames/deblocking, full-pixel motion search.
    # This keeps decoding practical on H1's scalar MIPS CPU at the original fps.
    subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(source),'-map','0:v:0','-map','0:a:0',
        '-map_metadata','-1','-c:v','libx264','-profile:v','baseline','-level','1.3','-preset','veryfast',
        '-tune','fastdecode','-crf',str(crf),'-pix_fmt','yuv420p','-refs','1','-bf','0','-g','30','-threads','1',
        '-x264-params','subme=0:repeat-headers=1:aud=1','-c:a','copy',str(destination)],check=True)
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
    ap.add_argument('--video-codec',choices=('h264','original'),default='h264')
    ap.add_argument('--crf',type=int,default=18,choices=range(12,29),metavar='12..28')
    args=ap.parse_args();out=args.output.resolve();core=out/'core';video=out/'video'
    if out.is_relative_to(args.steam_root.resolve()):raise ValueError('Output must be outside the original Steam installation')
    for d in (core,video):d.mkdir(parents=True,exist_ok=True)
    dos=args.steam_root/'PAL_DOS';pal98=args.steam_root/'PAL98'
    inputs={p.name.lower():p for p in dos.iterdir() if p.is_file()}
    for name in CORE:shutil.copyfile(inputs[name.lower()],core/name)
    spec=importlib.util.spec_from_file_location('prepare_avi',ROOT/'tools/prepare-pal-avi.py')
    normalizer=importlib.util.module_from_spec(spec);spec.loader.exec_module(normalizer)
    reports=[]
    for i in range(1,7):
        src=pal98/f'{i}.AVI';dest=video/f'{i}.avi'
        if args.video_codec=='h264':transcode_h264(src,dest,args.crf)
        else:shutil.copyfile(src,dest)
        prepared=normalizer.prepare(dest)
        # The decoder has a bounded chunk buffer. Check actual payloads too.
        data=dest.read_bytes();movi=data.index(b'movi');end=movi+struct.unpack_from('<I',data,movi-4)[0]
        largest=largest_payload(data,movi+4,end)
        if not largest or largest>prepared['suggested_buffer_after']:
            raise ValueError(f'{src.name}: original AVI chunks exceed the playback buffer')
        before,after=video_info(src),video_info(dest)
        for key in ('width','height','r_frame_rate','nb_frames'):
            if before[key]!=after[key]:raise ValueError(f'{src.name}: {key} changed')
        if audio_hash(src)!=audio_hash(dest):raise ValueError(f'{src.name}: original audio samples changed')
        if args.video_codec=='original' and video_hash(src)!=video_hash(dest):raise ValueError(f'{src.name}: original video changed')
        subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','NUL'],check=True)
        report={'source':str(src),'source_sha256':sha(src),'sha256':sha(dest),'video_info':after,
            'video_bit_exact':args.video_codec=='original','video_reencoded':args.video_codec=='h264','audio_bit_exact':True,
            'crf':args.crf if args.video_codec=='h264' else None,'largest_chunk':largest,**prepared}
        reports.append(report);print(src.name,args.video_codec,'bytes',dest.stat().st_size,flush=True)
    for source,name in ((core,'PAL9588.PAK'),(video,'PALVIDEO.PAK')):
        pack_directory(source,out/name);verify_archive(out/name)
    report={'steam_root':str(args.steam_root),'core_files':len(CORE),'videos':reports,
        'packages':{name:{'size':(out/name).stat().st_size,'sha256':sha(out/name)} for name in ('PAL9588.PAK','PALVIDEO.PAK')}}
    (out/'steam-resources.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['packages'],indent=2))
if __name__=='__main__':main()
