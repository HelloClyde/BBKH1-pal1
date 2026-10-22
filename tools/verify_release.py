"""Validate BDA format and reproducible bytes against the recorded build."""
from pathlib import Path
import hashlib,json,struct,sys

ROOT=Path(__file__).resolve().parents[1]

VERSION=(ROOT/'VERSION').read_text().strip()
EVIDENCE_PATH=ROOT/'docs/evidence/current-build.json'
if not EVIDENCE_PATH.exists():EVIDENCE_PATH=ROOT/f'docs/evidence/release-v{VERSION}.json'
EVIDENCE=json.loads(EVIDENCE_PATH.read_text(encoding='utf-8'))
assert EVIDENCE['version']==VERSION,'Recorded build version differs from VERSION'
EXPECTED=EVIDENCE['bda_sha256']

def main():
    sys.path.insert(0,str(ROOT/'sdk'))
    from h1_bda.header import decode_header,read_c_string,TITLE_OFFSET,TITLE_SIZE
    from h1_bda.resources import RESOURCE_OFFSET,PAYLOAD_OFFSET,build_icon_resources
    from h1_bda.validate import validate_bda
    bda=ROOT/'dist/仙剑1.bda';data=bda.read_bytes()
    meta=json.loads((ROOT/'dist/H1PAL.build.json').read_text())
    digest=hashlib.sha256(data).hexdigest()
    assert digest==meta['sha256']==EXPECTED,'BDA differs from the recorded reproducible build'
    assert not meta['regression'] and meta['version']==(ROOT/'VERSION').read_text().strip()
    assert validate_bda(bda)['ok']
    header=decode_header(data)
    assert read_c_string(header[TITLE_OFFSET:TITLE_OFFSET+TITLE_SIZE])=='仙剑1'
    assert struct.unpack_from('<I',header,12)[0]==0x47
    assert data[RESOURCE_OFFSET:PAYLOAD_OFFSET]==build_icon_resources(ROOT/'assets/icon.png')
    assert data==(ROOT/'build/release/H1PAL.bda').read_bytes()
    result={'ok':True,'sha256':digest,'size':len(data),'version':meta['version'],
        'title':'仙剑1','sdk_commit':meta['sdk_commit'],'engine_commit':meta['engine_commit'],
        'byte_identical_to_firmware_tested_bda':EVIDENCE['exact_bda_full_firmware_checked'],
        'hardware_verified':EVIDENCE.get('hardware_verified',False),
        'hardware_scope':EVIDENCE.get('hardware_scope','not tested'),
        'evidence':EVIDENCE_PATH.relative_to(ROOT).as_posix(),
        'ci_scope':'BDA format, reproducibility and separate MIPS service-model tests; no full firmware execution in CI'}
    out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
    (out/'release.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
