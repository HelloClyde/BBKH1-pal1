"""Create a reviewable H1 installation ZIP; never includes saves or firmware."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resources',type=Path,required=True)
    ap.add_argument('--output',type=Path,help='optional separate installer filename')
    args=ap.parse_args();dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    bda=dist/'仙剑1.bda';meta=json.loads((dist/'H1PAL.build.json').read_text())
    assert sha(bda)==meta['sha256'] and not meta['regression']
    from palpak import verify_archive
    files=[(bda,'应用/程序/仙剑1.bda')]
    for name in ('PAL9588.PAK','PALVIDEO.PAK'):
        p=args.resources/name;verify_archive(p)
        files.append((p,'应用/数据/PAL/'+name))
    manifest={'version':meta['version'],'artwork_revision':meta['artwork_revision'],
        'title':meta['title'],'icon_sha256':meta['icon_sha256'],
        'target':'BBK H1 / Y100 V1.41','hardware_verified':False,
        'resource_profile':'steam-original' if (args.resources/'steam-resources.json').exists() else '9588-compact',
        'files':{name:{'size':p.stat().st_size,'sha256':sha(p)} for p,name in files}}
    target=args.output if args.output else dist/'H1PAL-install.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p,name in files:z.write(p,name)
        z.write(ROOT/'README.md','安装说明.md');z.write(ROOT/'NOTICE.md','NOTICE.md');z.write(ROOT/'LICENSE','LICENSE')
        z.write(ROOT/'UPSTREAM.json','UPSTREAM.json')
        for p in sorted((ROOT/'docs').rglob('*')):
            if p.is_file():z.write(p,p.relative_to(ROOT).as_posix())
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for p,name in files:assert hashlib.sha256(z.read(name)).hexdigest()==sha(p)
    manifest['archive']={'file':target.name,'size':target.stat().st_size,'sha256':sha(target)}
    manifest_path=target.with_suffix('.manifest.json') if args.output else dist/'install-manifest.json'
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    target.with_suffix('.zip.sha256').write_text(sha(target)+'  '+target.name+'\n')
    print(json.dumps(manifest['archive'],indent=2))
if __name__=='__main__':main()
