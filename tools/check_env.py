import os, sys

def hex_preview(path, n=200):
    try:
        b = open(path, 'rb').read()
    except Exception as e:
        print('read error', e)
        return
    print(path, 'exists:', True)
    print('first', n, 'bytes (hex):', b[:n].hex())

print('--- ENV VARS ---')
for k in ('DATABASE_URL','PGPASSWORD','PGSERVICE'):
    print(k, '=>', repr(os.environ.get(k)))

appdata = os.environ.get('APPDATA', '')
pgpass = os.path.join(appdata, 'postgresql', 'pgpass.conf')
if os.path.exists(pgpass):
    hex_preview(pgpass)
else:
    print('pgpass not found at', pgpass)

print('--- SETTINGS.PY ENCODING ---')
sp = os.path.join('AiCooding', 'settings.py')
try:
    b = open(sp, 'rb').read()
    try:
        b.decode('utf-8')
        print('settings.py is valid UTF-8')
    except Exception as e:
        print('settings.py NOT utf-8:', e)
        print('settings.py first 200 bytes (hex):', b[:200].hex())
except Exception as e:
    print('cannot read settings.py:', e)

print('--- PYTHON ENCODING ---')
print('defaultencoding:', sys.getdefaultencoding())
print('filesystemencoding:', sys.getfilesystemencoding())

print('--- CHCP (console code page) ---')
try:
    import subprocess
    cp = subprocess.check_output(['chcp'], shell=True, text=True)
    print(cp.strip())
except Exception as e:
    print('chcp failed:', e)
