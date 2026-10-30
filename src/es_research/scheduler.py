"""JST schedule design and gated dispatcher. No OS/app schedule is registered."""
from datetime import timedelta
from contextlib import contextmanager
from zoneinfo import ZoneInfo
from .memory import Blocked, utc, moment

JST=ZoneInfo('Asia/Tokyo')
RESEARCH_HOURS=(0,6,12,18)
REVIEW_HOURS=(5,11,17,23)

def slot_for(at,phase):
    if at.tzinfo is None: raise Blocked('timezone required')
    local=at.astimezone(JST)
    hours=RESEARCH_HOURS if phase=='research' else REVIEW_HOURS if phase=='review' else ()
    if local.hour not in hours or local.minute>=5: raise Blocked('outside start window; no catch-up')
    return local.replace(minute=0,second=0,microsecond=0).isoformat()

@contextmanager
def dispatch(memory,config,transport,ack,at=None):
    at=at or utc()
    if config.get('enabled') is not True: raise Blocked('schedule disabled')
    if config.get('timezone')!='Asia/Tokyo': raise Blocked('wrong timezone')
    if config.get('mode')!=memory.load()['state']['mode']: raise Blocked('execution mode mismatch')
    slot=slot_for(at,'research')
    with memory.lock('worker'):
        revision=memory.load()['state']['revision']
        # Research deadline is anchored to scheduled hour, even after a late dispatch.
        start=moment(slot)
        current=memory.start(revision,slot,'cycle-'+start.strftime('%Y%m%d-%H%M'),transport,ack,at=at,deadline_at=start+timedelta(hours=5))
        yield current

def review_ready(memory,at=None):
    slot=slot_for(at or utc(),'review')
    c=memory.load()
    if c['state']['status']!='awaiting_review': raise Blocked('research report is not ready')
    start=moment(c['state']['cycles'][-1]['slot'])
    if moment(slot)!=start+timedelta(hours=5): raise Blocked('review slot does not match cycle')
    return dict(slot=slot,memory_head=c['head'],report_sha256=c['state']['cycles'][-1]['report'])


@contextmanager
def resume_session(memory,transport,ack,at=None):
    with memory.lock('worker'):
        s=memory.load()['state']
        yield memory.resume(s['revision'],ack,transport,at=at)
