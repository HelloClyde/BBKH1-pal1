"""Validate the public BDA and its byte identity with the firmware-tested build."""
from pathlib import Path
import hashlib,json,struct,sys

ROOT=Path(__file__).resolve().parents[1]

EXPECTED='0d95916daebcec5f70cac0bca37d9c5804dafac7fe8512aea566f877955ac20b'

def main():
    sys.path.insert(0,str(ROOT/'sdk'))
    from h1_bda.header import decode_header,read_c_string,TITLE_OFFSET,TITLE_SIZE
    from h1_bda.resources import RESOURCE_OFFSET,PAYLOAD_OFFSET,build_icon_resources
    from h1_bda.validate import validate_bda
    bda=ROOT/'dist/仙剑1.bda';data=bda.read_bytes()
    meta=json.loads((ROOT/'dist/H1PAL.build.json').read_text())
    digest=hashlib.sha256(data).hexdigest()
    assert digest==meta['sha256']==EXPECTED,'BDA differs from the recorded firmware-tested build'
    assert not meta['regression'] and meta['version']==(ROOT/'VERSION').read_text().strip()
    assert validate_bda(bda)['ok']
    header=decode_header(data)
    assert read_c_string(header[TITLE_OFFSET:TITLE_OFFSET+TITLE_SIZE])=='仙剑1'
    assert struct.unpack_from('<I',header,12)[0]==0x47
    assert data[RESOURCE_OFFSET:PAYLOAD_OFFSET]==build_icon_resources(ROOT/'assets/icon.png')
    assert data==(ROOT/'build/release/H1PAL.bda').read_bytes()
    result={'ok':True,'sha256':digest,'size':len(data),'version':meta['version'],
        'title':'仙剑1','sdk_commit':meta['sdk_commit'],'engine_commit':meta['engine_commit'],
        'byte_identical_to_firmware_tested_bda':True,'hardware_verified':False,
        'ci_scope':'BDA format, reproducibility and separate MIPS service-model tests; no full firmware execution in CI'}
    out=ROOT/'build/verification';out.mkdir(parents=True,exist_ok=True)
    (out/'release.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
