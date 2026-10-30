import subprocess, sys, json, datetime, base64
from pathlib import Path
p = Path(__file__).resolve().parent / "commands.jsonl"
r = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
b = r.stdout
encoding = "utf-16-le" if b"\x00" in b[:200] else "utf-8"
out = b.decode(encoding, errors="replace")
record = dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(), cwd=str(Path.cwd()), argv=sys.argv[1:], exit_code=r.returncode, encoding=encoding, output=out, raw_base64=base64.b64encode(b).decode())
with p.open("a") as f: f.write(json.dumps(record, ensure_ascii=False)+"\n")
print(out, end="")
raise SystemExit(r.returncode)
