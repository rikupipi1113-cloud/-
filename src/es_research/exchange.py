"""Git-backed exchange. Production fetch is read-only; writes are local simulations only."""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from .memory import Blocked, Memory
from .state import canonical

class GitExchange:
    def __init__(self,remote,ref='refs/heads/research-memory',timeout=30):
        self.remote=str(remote);self.ref=ref;self.timeout=timeout
        if not ref.startswith('refs/heads/') or not all(c.isalnum() or c in '/-_' for c in ref): raise Blocked('unsafe Git ref')
    def git(self,directory,*args):
        cmd=['git','-c','core.hooksPath=/dev/null','-c','credential.interactive=false','-c','core.askPass=',*args]
        try:
            r=subprocess.run(cmd,cwd=directory,capture_output=True,text=True,timeout=self.timeout,
                             env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'})
        except (OSError,subprocess.TimeoutExpired) as e: raise Blocked('sync failed: '+type(e).__name__) from e
        if r.returncode: raise Blocked('sync failed: '+r.stderr.strip()[:500])
        return r.stdout.strip()
    def fetch_to(self,directory):
        self.git(directory,'init','-q')
        self.git(directory,'fetch','--quiet','--no-tags','--depth=1',self.remote,self.ref)
        return self.git(directory,'rev-parse','FETCH_HEAD')
    def read_handoff(self):
        with tempfile.TemporaryDirectory(prefix='es-reader-') as d:
            commit=self.fetch_to(d)
            text=self.git(d,'show',commit+':exchange/package.json')
            if len(text)>32*1024*1024: raise Blocked('exchange package too large')
            package=json.loads(text)
            if set(package)!={'protocol','handoff','context','files'} or package['protocol']!=2: raise Blocked('exchange protocol mismatch')
            dest=Path(d)/'validated-memory';dest.mkdir()
            for name,content in package['files'].items():
                parts=name.split('/')
                valid=(name=='latest.json' or len(parts)==2 and
                       ((parts[0]=='events' and len(parts[1])==13 and parts[1][:8].isdigit() and parts[1].endswith('.json')) or
                        (parts[0]=='objects' and len(parts[1])==64 and all(c in '0123456789abcdef' for c in parts[1]))))
                if not valid or not isinstance(content,str): raise Blocked('unsafe package file')
                target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
            mem=Memory(dest)
            if mem.handoff()!=package['handoff'] or mem.context()!=package['context']: raise Blocked('exchange handoff mismatch')
            return dict(commit=commit,handoff=package['handoff'],context=mem.context())
    def publish_local(self,memory,lab_root):
        """Never writes GitHub. A lab root and a local bare-repository path are mandatory."""
        remote=Path(self.remote)
        try: remote.resolve().relative_to(Path(lab_root).resolve())
        except ValueError: raise Blocked('simulation remote must be inside lab root') from None
        if not remote.is_absolute() or not (remote/'HEAD').is_file(): raise Blocked('local bare remote required')
        if memory.load()['state']['mode']!='mock': raise Blocked('only mock memory can be published by this helper')
        files={}
        for folder in ['events','objects']:
            for p in sorted((memory.root/folder).iterdir()):
                if p.is_file() and not p.name.endswith('.tmp'): files[folder+'/'+p.name]=p.read_text()
        files['latest.json']=(memory.root/'latest.json').read_text()
        package=dict(protocol=2,handoff=memory.handoff(),context=memory.context(),files=files)
        with tempfile.TemporaryDirectory(prefix='es-writer-') as d:
            self.git(d,'init','-q')
            refs=self.git(d,'ls-remote',self.remote,self.ref)
            if refs:
                commit=self.fetch_to(d);self.git(d,'checkout','-q','-B','exchange',commit)
            path=Path(d)/'exchange/package.json';path.parent.mkdir(exist_ok=True);path.write_bytes(canonical(package)+b'\n')
            self.git(d,'add','exchange/package.json')
            self.git(d,'-c','user.name=Research-Simulation','-c','user.email=simulation@localhost','commit','-q','-m','Mock research memory exchange')
            self.git(d,'push','--quiet',self.remote,'HEAD:'+self.ref)
        return self.read_handoff()
