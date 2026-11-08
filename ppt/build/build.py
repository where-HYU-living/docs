# index.src.html + 표 조각 → ../index.html
#   python3 docs/ppt/build/build.py
import pathlib, subprocess, sys
here = pathlib.Path(__file__).resolve().parent
subprocess.run([sys.executable, str(here/'gen_tables.py')], check=True)
s = (here/'index.src.html').read_text()
s = s.replace('<!--SPEC-->', (here/'spec.html').read_text()).replace('<!--API-->', (here/'api.html').read_text())
s = s.replace('<ol class="steps">\n            <li class="fragment">', '<ol class="steps">\n            <li>')
(here.parent/'index.html').write_text(s)
print('index.html', len(s))
