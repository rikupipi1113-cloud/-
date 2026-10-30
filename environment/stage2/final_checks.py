from pathlib import Path
import json
from es_research.memory import Memory
from es_research.state import ROOT
p=ROOT
m=Memory(p/'research/memory-v2');s=m.load()
assert s['state']['status']=='pending' and not s['state']['bootstrap_approved']
config=json.loads((p/'automation/stage2/schedule.json').read_text())
assert not config['enabled'] and not config['integration_verified']
demo=Memory(p/'reports/stage2/three-cycle-final/memory');c=demo.context()
assert len(c['cycles'])==3 and len(c['records'])==10
assert not demo.confirmed()
print('production disabled; 3-cycle final history and all evidence readable; mock roundtrip only')
