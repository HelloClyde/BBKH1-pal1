"""Package public program-only assets and complete pinned source, never game data."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,io,json,subprocess,zipfile

ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def git(repo,*args):return subprocess.check_output(['git','-c','safe.directory=*','-C',str(repo),*args])
def safe(name):return bool(name) and not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and '\\' not in name and ':' not in name
def add(z,name,data):
    assert safe(name),name
    info=zipfile.ZipInfo(name,(2026,10,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
    z.writestr(info,data)
def json_bytes(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def source(destination,dependencies,commit):
    assert Path(git(ROOT,'rev-parse','--show-toplevel').decode().strip()).resolve()==ROOT
    assert not git(ROOT,'status','--porcelain').strip(),'Commit release sources before packaging'
    files={}
    for relative,expected in [('',commit)]+[(d['path'],d['commit']) for d in dependencies.values()]:
        repo=ROOT/relative
        assert git(repo,'rev-parse','HEAD').decode().strip()==expected
        assert not git(repo,'status','--porcelain','--untracked-files=no').strip()
        if relative:assert git(ROOT,'rev-parse','HEAD:'+relative).decode().strip()==expected
        with zipfile.ZipFile(io.BytesIO(git(repo,'archive','--format=zip','HEAD'))) as archive:
            for item in archive.infolist():
                if item.is_dir():continue
                if relative=='third_party/h264bsd' and item.filename not in ('LICENSE.md','README.md') and not item.filename.startswith('src/'):continue
                name=(relative+'/' if relative else '')+item.filename
                # Unused upstream 3DS artwork binaries and WinRT signing samples
                # are not needed to build this port or its complete source archive.
                if name.endswith(('.pfx','.bin')):continue
                assert safe(name) and name not in files,name
                assert not any(p in {'.git','.tools','__pycache__'} for p in PurePosixPath(name).parts)
                assert PurePosixPath(name).suffix.lower() not in {'.pak','.mkf','.rpg','.raw','.nand','.bda','.exe','.dll','.pyc','.o'},name
                files[name]=archive.read(item)
    manifest={'application_commit':commit,'dependencies':dependencies,'files':{n:sha(d) for n,d in sorted(files.items())},
        'omitted_unused_upstream_files':'3DS .bin artwork, WinRT .pfx samples and h264bsd platform demos/test media; no H1 build inputs omitted'}
    prefix='BBKH1-pal1-v'+(ROOT/'VERSION').read_text().strip()+'/'
    with zipfile.ZipFile(destination,'w') as z:
        for name,data in sorted(files.items()):add(z,prefix+name,data)
        add(z,prefix+'SOURCE-MANIFEST.json',json_bytes(manifest))

def verify(out,tag=None,commit=None):
    version=(ROOT/'VERSION').read_text().strip();manifest=read(out/'release-manifest.json')
    if tag:assert tag=='v'+version
    if commit:assert manifest['application_commit']==commit
    from verify_release import EXPECTED
    assert manifest['version']==version and manifest['bda_sha256']==EXPECTED
    expected={'PAL1.bda','H1PAL.build.json','RELEASE-NOTES.md','release-manifest.json',
        f'BBKH1-pal1-v{version}-install.zip',f'BBKH1-pal1-v{version}-source.zip'}
    sums={}
    for line in (out/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        digest,name=line.split('  ',1);assert safe(name) and '/' not in name and name not in sums
        assert sha((out/name).read_bytes())==digest,name;sums[name]=digest
    assert set(sums)==expected and {p.name for p in out.iterdir()}==expected|{'SHA256SUMS.txt'}
    assert sums['PAL1.bda']==manifest['bda_sha256']
    for name in expected:
        if not name.endswith('.zip'):continue
        with zipfile.ZipFile(out/name) as z:
            assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
            assert all(safe(n) for n in z.namelist())
            if name.endswith('-install.zip'):
                assert sha(z.read('应用/程序/仙剑1.bda'))==manifest['bda_sha256']
                assert not any(PurePosixPath(n).suffix.lower() in {'.pak','.rpg','.mkf','.raw'} for n in z.namelist())
            else:
                prefix=f'BBKH1-pal1-v{version}/';m=json.loads(z.read(prefix+'SOURCE-MANIFEST.json'))
                assert m['application_commit']==manifest['application_commit'] and m['dependencies']==manifest['dependencies']
                assert set(z.namelist())=={prefix+n for n in m['files']}|{prefix+'SOURCE-MANIFEST.json'}
                for n,digest in m['files'].items():assert sha(z.read(prefix+n))==digest,n
    print('PASS public BDA, install layout, complete source and SHA256SUMS')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--tag');ap.add_argument('--commit')
    args=ap.parse_args();out=ROOT/'dist/release'
    if args.verify:verify(out,args.tag,args.commit);return
    from verify_release import main as check
    check();version=(ROOT/'VERSION').read_text().strip();meta=read(ROOT/'dist/H1PAL.build.json')
    commit=git(ROOT,'rev-parse','HEAD').decode().strip()
    if args.commit:assert commit==args.commit
    if args.tag:assert args.tag=='v'+version
    deps={k:v for k,v in read(ROOT/'UPSTREAM.json').items() if 'path' in v}
    reports={}
    for name in ('release','wide-ui','wide-battle','display-controls','keymap','music','h264-video','missing','data-drives'):
        r=read(ROOT/f'build/verification/{name}.json');assert r['ok'] and r['sha256']==meta['sha256'];reports[name]=r
    for name,digest in meta['sources'].items():assert sha((ROOT/name).read_bytes())==digest,'Rebuild after source changes: '+name
    out.mkdir(parents=True,exist_ok=True)
    source(out/f'BBKH1-pal1-v{version}-source.zip',deps,commit)
    bda=(ROOT/'dist/仙剑1.bda').read_bytes();(out/'PAL1.bda').write_bytes(bda)
    (out/'H1PAL.build.json').write_bytes((ROOT/'dist/H1PAL.build.json').read_bytes())
    (out/'RELEASE-NOTES.md').write_bytes((ROOT/f'docs/release-v{version}.md').read_bytes())
    manifest={'version':version,'application_commit':commit,'dependencies':deps,'bda_sha256':meta['sha256'],
        'full_firmware_in_ci':False,'hardware_verified':False,'exact_bda_full_firmware_checked':True,
        'full_firmware_scope':'H1 V1.41 exact BDA: title, old-save map, quit/settings/keymap, remap confirm/cancel, clean quit, application relaunch reload and restore defaults; mapping A/B persistence, input, synthetic RIX and H.264 in MIPS service model',
        'download_filename':'PAL1.bda','install_filename':'仙剑1.bda',
        'game_resources_included':False,'checks':reports}
    (out/'release-manifest.json').write_bytes(json_bytes(manifest))
    install={'应用/程序/仙剑1.bda':bda,'安装说明.md':(ROOT/'README.md').read_bytes(),
        'LICENSE':(ROOT/'LICENSE').read_bytes(),'NOTICE.md':(ROOT/'NOTICE.md').read_bytes(),
        'UPSTREAM.json':(ROOT/'UPSTREAM.json').read_bytes()}
    for name,path in [('SDLPAL-GPL.txt','third_party/sdlpal/gpl.txt'),('H1-SDK-LICENSE.txt','sdk/LICENSE'),('H1-SDK-NOTICE.txt','sdk/NOTICE')]:
        install['LICENSES/'+name]=(ROOT/path).read_bytes()
    install['LICENSES/H264BSD-LICENSE.md']=(ROOT/'third_party/h264bsd/LICENSE.md').read_bytes()
    for p in (ROOT/'docs').rglob('*'):
        if p.is_file():install[p.relative_to(ROOT).as_posix()]=p.read_bytes()
    with zipfile.ZipFile(out/f'BBKH1-pal1-v{version}-install.zip','w') as z:
        for name,data in sorted(install.items()):add(z,name,data)
    (out/'SHA256SUMS.txt').write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.name!='SHA256SUMS.txt'),encoding='utf-8')
    verify(out,args.tag,commit)

if __name__=='__main__':main()
