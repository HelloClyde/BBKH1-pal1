"""Build the native H1 SDLPAL BDA from the pinned core and checked H1 overrides."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse, hashlib, json, os, subprocess, sys, shutil
ROOT=Path(__file__).resolve().parents[1]
ENGINE_COMMIT='224cb0a0cc839e0e8ecaa299cd480b02b372b9f7'
SDK_COMMIT='067fe072477861dfc8949d7b1a55279fb92d2548'
H264_COMMIT='42bcb5d753ad86d84903354bf3c68423c28adb7b'
# GCC's __DATE__ is visible in SDLPAL's about string. Match the tested build.
BUILD_EPOCH='1792368000'
def run(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,
        env={**os.environ,'SOURCE_DATE_EPOCH':BUILD_EPOCH})
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--regression',action='store_true',help='enable marker-driven save/battle/video tests in an isolated data directory')
    ap.add_argument('--sdk',type=Path,default=ROOT/'sdk')
    ap.add_argument('--toolchain',type=Path,default=Path(os.environ.get('H1_GNU_BIN',ROOT/'.tools/toolchain/bin')))
    args=ap.parse_args();sdk=args.sdk.resolve();core=ROOT/'third_party/sdlpal';tc=args.toolchain.resolve()
    from source_identity import dependency
    dependency('third_party/sdlpal',ENGINE_COMMIT)
    if sdk!=ROOT/'sdk':raise ValueError('Use the pinned sdk/ submodule')
    dependency('sdk',SDK_COMMIT)
    dependency('third_party/h264bsd',H264_COMMIT)
    mode='regression' if args.regression else 'release';build=ROOT/'build'/mode;build.mkdir(parents=True,exist_ok=True)
    includes=[ROOT/'src/libc/include',ROOT/'src/compat',ROOT/'src/port',sdk/'sdk/include',core,ROOT/'third_party/h264bsd/src']
    flags=['-EL','-march=mips32','-mabi=32','-msoft-float','-mno-abicalls','-G0','-fno-pic','-O2',
        '-ffreestanding','-fno-builtin','-fno-stack-protector','-ffunction-sections','-fdata-sections',
        '-fsigned-char','-fno-strict-aliasing','-g','-DPAL_CLASSIC','-DPAL_HAS_PLATFORM_SPECIFIC_UTILS=1',
        f'-DH1PAL_REGRESSION={int(args.regression)}',f'-ffile-prefix-map={ROOT}=h1-pal']
    flags += [v for p in includes for v in ('-I',str(p))]
    sources=[ROOT/'src'/p for p in ('runtime/entry.S','runtime/startup.c','runtime/setjmp.S','runtime/cxx_runtime.cpp',
        'libc/runtime.c','compat/mini_sdl.c','port/platform.c','port/native_audio.c','port/app.c',
        'port/autopath.c','port/audio_stub.c','port/avi_9588.c','port/h264_video.c','port/keymap.c','port/settings.c','port/pal_utils.c','port/regression.c','port/bda_main.c','port/wide_scene.c','port/wide_battle.c','port/wide_ui.c')]
    names='audio aviplay battle ending fight font game global input itemmenu magicmenu main map midi palette palcfg palcommon play res rngplay scene script text resampler sound ui uibattle uigame util video yj1'.split()
    from core_overrides import generate
    overrides=generate(core,build/'core')
    sources += [overrides.get(n+'.c',core/(n+'.c')) for n in names]+[core/'adplug/fmopl.c',core/'rixplay.cpp']
    sources += [core/'adplug'/(n+'.cpp') for n in 'binfile binio dbemuopl dbopl demuopl dosbox_opl emuopl fprovide player rix surroundopl'.split()]
    sources += sorted((ROOT/'third_party/h264bsd/src').glob('*.c'))
    headers=hashlib.sha256(b''.join(p.read_bytes() for d in includes for p in sorted(d.rglob('*.h')))).digest()
    def compile(item):
        i,source=item;cpp=source.suffix=='.cpp';obj=build/f'{i:02d}-{source.stem}.o'
        extra=['-std=gnu++11','-fno-exceptions','-fno-rtti','-fno-threadsafe-statics','-fno-use-cxa-atexit'] if cpp else ['-std=gnu11']
        rename={'main.c':['-Dmain=sdlpal_main'],'aviplay.c':['-DPAL_PlayAVI=H1PAL_InternalPlayAVI','-DVIDEO_DrawSurfaceToScreen=H1PAL_DrawAVISurface'],
            'game.c':['-DPAL_GameMain=H1PAL_InternalGameMain'],'play.c':['-DPAL_StartFrame=H1PAL_InternalStartFrame'],
            'palcommon.c':['-DPAL_FBPBlitToSurface=H1PAL_InternalFBPBlit',
                '-DPAL_RLEBlitToSurface=H1PAL_InternalRLE','-DPAL_RLEBlitToSurfaceWithShadow=H1PAL_InternalRLEShadow',
                '-DPAL_RLEBlitWithColorShift=H1PAL_InternalRLEShift','-DPAL_RLEBlitMonoColor=H1PAL_InternalRLEMono']}
        if source.parent==core:extra+=rename.get(source.name,[])
        if source==overrides.get('aviplay.c'):extra+=rename['aviplay.c']
        if args.regression and source==core/'main.c':extra+=['-DUNIT_TEST','-DUNIT_TEST_GAME_INIT']
        cmd=[tc/('mipsel-none-elf-g++.exe' if cpp else 'mipsel-none-elf-gcc.exe'),*flags,*extra,'-c',source,'-o',obj]
        digest=hashlib.sha256(BUILD_EPOCH.encode()+str(cmd).encode()+source.read_bytes()+headers).hexdigest();stamp=obj.with_suffix('.sha256')
        if not obj.exists() or not stamp.exists() or stamp.read_text()!=digest:run(cmd);stamp.write_text(digest)
        return obj
    with ThreadPoolExecutor(max_workers=6) as pool:objects=list(pool.map(compile,enumerate(sources)))
    elf=build/'H1PAL.elf';raw=build/'H1PAL.bin';bda=build/'H1PAL.bda'
    run([tc/'mipsel-none-elf-g++.exe',*flags,'-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none',
        f'-Wl,-T,{ROOT/"src/runtime/h1.ld"}',f'-Wl,-Map,{build/"H1PAL.map"}','-o',elf,*objects,'-lgcc'])
    run([tc/'mipsel-none-elf-objcopy.exe','-O','binary',elf,raw])
    sys.path.insert(0,str(sdk))
    from h1_bda.header import HeaderFields,encode_header
    from h1_bda.resources import PAYLOAD_OFFSET,RESOURCE_OFFSET,RESOURCE_SIZES,build_icon_resources
    from h1_bda.validate import validate_bda
    payload=raw.read_bytes();pad=(-(PAYLOAD_OFFSET+len(payload)))&3
    header=HeaderFields(category=0x47,file_size_minus_4=PAYLOAD_OFFSET+len(payload)+pad-4,payload_offset=PAYLOAD_OFFSET,resource_offset=RESOURCE_OFFSET,resource_sizes=RESOURCE_SIZES)
    data=encode_header(header,title='仙剑1',build_time='2026-10-19 00:00:00')+build_icon_resources(ROOT/'assets/icon.png')+payload+bytes(pad)
    bda.write_bytes(data);assert validate_bda(bda)['ok']
    symbols={f[2]:int(f[0],16) for line in run([tc/'mipsel-none-elf-nm.exe',elf]).splitlines() if len(f:=line.split())==3}
    meta={'version':(ROOT/'VERSION').read_text().strip(),'artwork_revision':'2026-10-20','title':'仙剑1','filename':'仙剑1.bda',
        'icon_sha256':hashlib.sha256((ROOT/'assets/icon.png').read_bytes()).hexdigest(),'source_date_epoch':int(BUILD_EPOCH),
        'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'regression':args.regression,
        'engine_commit':ENGINE_COMMIT,'sdk_commit':SDK_COMMIT,
        'h264_commit':H264_COMMIT,
        'reference_commit':'10532f74ced55061b6147538dee80797527fb203','symbols':symbols,'hardware_verified':False,
        'sources':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for d in (ROOT/'src',ROOT/'tools') for p in sorted(d.rglob('*')) if p.is_file() and p.suffix in ('.c','.h','.S','.cpp','.py','.ld')}}
    bda.with_suffix('.build.json').write_text(json.dumps(meta,indent=2)+'\n')
    if not args.regression:
        dist=ROOT/'dist';dist.mkdir(exist_ok=True)
        for f in (bda,bda.with_suffix('.build.json')):shutil.copyfile(f,dist/f.name)
        shutil.copyfile(bda,dist/'仙剑1.bda')
        (dist/'仙剑1.bda.sha256').write_text(meta['sha256']+'  仙剑1.bda\n',encoding='utf-8')
        (dist/'H1PAL.bda.sha256').write_text(meta['sha256']+'  H1PAL.bda\n')
    print(json.dumps({k:meta[k] for k in ('version','sha256','size')},indent=2));print(run([tc/'mipsel-none-elf-size.exe',elf]))
if __name__=='__main__':main()
