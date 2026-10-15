import subprocess, json, time, os, base64, urllib.request, sys
S=os.path.dirname(os.path.abspath(__file__)); W='665806861'; T='665806862'; CG='171241'; OUT=S+'/sr_run.jsonl'
def js(code):
    p=subprocess.run(['osascript','-e','on run argv','-e','tell application "Aside" to execute tab id ((item 1 of argv) as integer) of window id ((item 2 of argv) as integer) javascript (item 3 of argv)','-e','end run',T,W,code],capture_output=True,text=True,timeout=60)
    return p.stdout.strip()
def nav(u):
    subprocess.run(['osascript','-e','on run argv','-e','tell application "Aside" to set URL of tab id ((item 1 of argv) as integer) of window id ((item 2 of argv) as integer) to (item 3 of argv)','-e','end run',T,W,u],timeout=30)
def log(d):
    open(OUT,'a').write(json.dumps(d,ensure_ascii=False)+'\n'); print(json.dumps(d,ensure_ascii=False)[:200],flush=True)
meta={}
for p in json.load(open(S+'/saramin_lists.json'))['pages']:
    for r in p['list']: meta.setdefault(r['res_idx'],dict(r,q=p['q']))
ids=json.load(open(S+'/saramin_ids.json')); done=set()
if os.path.exists(OUT):
    for l in open(OUT):
        o=json.loads(l)
        if o.get('ok'): done.add(o['id'])
INFO='JSON.stringify((()=>{const m=document.querySelector("main");const t=document.body.innerText;const c=t.indexOf("방금 본 이력서와");return {vis:document.visibilityState,h:m?m.scrollHeight:0,ch:m?m.clientHeight:0,t:document.title,x:c>0?t.slice(0,c):t,lim:(()=>{const e=[...document.querySelectorAll("main *")].find(e=>e.childElementCount===0&&/방금 본 이력서와/.test(e.textContent));return e?e.getBoundingClientRect().top+m.scrollTop:0})()}})())'
for n,rid in enumerate(ids):
    if rid in done: continue
    url=f'https://hiring.saramin.co.kr/applicant-view/position/resume/{rid}?t_ref=search'
    try:
        nav(url); time.sleep(6)
        info=json.loads(js(INFO))
        if info['h']<1500: time.sleep(4); info=json.loads(js(INFO))
        end=info['lim'] or info['h']; step=max(600,info['ch']-120); shots=[]; y=0; i=0
        while y<end and i<10:
            js(f'document.querySelector("main").scrollTop={y};1'); time.sleep(1.2)
            f=f'{S}/sr_shot.jpg'
            subprocess.run(['screencapture','-x','-o','-l',CG,'-t','jpg',f],timeout=30)
            subprocess.run(['sips','-Z','1600','-s','formatOptions','70',f],capture_output=True)
            shots.append({'dataUrl':'data:image/jpeg;base64,'+base64.b64encode(open(f,'rb').read()).decode(),'sequence':i,'scrollY':y,'viewportHeight':info['ch'],'reason':'auto'})
            y+=step; i+=1
        m=meta.get(rid,{})
        head=f"[사람인 인재풀 | 검색어 {m.get('q','')}] res_idx {rid} | {m.get('name','')} | {m.get('age','')}세 | 경력 {m.get('career','')} | {m.get('school','')} {m.get('major','')} | {m.get('title','')} | 키워드 {m.get('kw','')}\n\n"
        body=json.dumps({'url':url,'pageTitle':info['t']+f" - {m.get('name','')} {m.get('title','')}"[:200],'textContent':head+info['x'],'screenshots':shots}).encode()
        r=json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:7777/api/archive',data=body,headers={'Content-Type':'application/json'}),timeout=180).read())
        log({'n':n,'id':rid,'ok':bool(r.get('ok')),'aid':r.get('id'),'dedup':r.get('deduped'),'shots':len(shots),'vis':info['vis'],'h':info['h']})
    except Exception as e:
        log({'n':n,'id':rid,'ok':False,'err':str(e)[:200]})
