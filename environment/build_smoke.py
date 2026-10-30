import os
import subprocess
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='es-build-') as d:
 p=Path(d)
 (p/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.16)\nproject(smoke LANGUAGES C CXX)\nadd_executable(c_check main.c)\nadd_executable(cpp_check main.cpp)\n')
 (p/'main.c').write_text('int main(void) { return (4*1*2*2 == 2*(1*2+1*2+2*2)) ? 0 : 1; }\n')
 (p/'main.cpp').write_text('int main() { static_assert(4*1*2*2 == 2*(1*2+1*2+2*2)); return 0; }\n')
 cmake=str(Path(__file__).resolve().parents[1]/'.venv/bin/cmake')
 for cmd in [[cmake,'-S',d,'-B',str(p/'build')],[cmake,'--build',str(p/'build'),'--parallel','2'],[str(p/'build/c_check')],[str(p/'build/cpp_check')]]:
  print('COMMAND',cmd,flush=True);subprocess.run(cmd,check=True)
 print('C and C++ configure/build/run: PASS')
