"""Validate a manually returned diagnostic. Does not authorize research or schedules."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from es_research.state import digest

def validate_probe(request,response,confirmed=False):
    body={k:v for k,v in request.items() if k!='request_sha256'}
    if digest(body)!=request['request_sha256']:raise ValueError('request hash mismatch')
    schema=json.loads((Path(__file__).parent/'response.schema.json').read_text())
    Draft202012Validator(schema).validate(response)
    if not confirmed:raise ValueError('operator source confirmation required')
    if response['challenge_id']!=request['challenge_id'] or response['request_sha256']!=request['request_sha256']:raise ValueError('old or different diagnostic response')
    n,x,y,z=request['fixture']
    if (response['lhs'],response['rhs'])!=(4*x*y*z,n*(x*y+x*z+y*z)):raise ValueError('incorrect arithmetic')
    return dict(protocol_matched=True,arithmetic_correct=True,source_attested_by_operator=True,responder=response['responder'],research_authorized=False,schedule_enabled=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('request');p.add_argument('response');p.add_argument('--confirm-source',action='store_true');a=p.parse_args()
    try:r=validate_probe(json.loads(Path(a.request).read_text()),json.loads(Path(a.response).read_text()),a.confirm_source)
    except Exception as e:print(json.dumps(dict(blocked=True,reason=str(e)),ensure_ascii=False));raise SystemExit(2)
    print(json.dumps(r,ensure_ascii=False,indent=2))
