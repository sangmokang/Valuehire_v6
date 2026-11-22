import subprocess, json, time, sys, urllib.request, os
S=os.path.dirname(os.path.abspath(__file__)); TAB=sys.argv[1]; OUT=S+'/rps_run.jsonl'
def js(code):
    p=subprocess.run(['osascript','-e','on run argv','-e','tell application "Aside" to execute tab id ((item 1 of argv) as integer) of window id 665806854 javascript (item 2 of argv)','-e','end run',TAB,code],capture_output=True,text=True,timeout=60)
    return p.stdout.strip()
def nav(u):
    subprocess.run(['osascript','-e','on run argv','-e','tell application "Aside" to set URL of tab id ((item 1 of argv) as integer) of window id 665806854 to (item 2 of argv)','-e','end run',TAB,u],timeout=30)
SCROLL='window.scrollBy(0,700);document.querySelectorAll("div").forEach(d=>{if(d.scrollHeight>d.clientHeight+50&&/auto|scroll/.test(getComputedStyle(d).overflowY))d.scrollTop+=700});1'
def scroll(n):
    for _ in range(n): js(SCROLL); time.sleep(0.6)
def post(url,title,text):
    body=json.dumps({'url':url,'pageTitle':title,'textContent':text,'capturedAt':time.strftime('%Y-%m-%dT%H:%M:%S%z')}).encode()
    r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:7777/api/archive',data=body,headers={'Content-Type':'application/json'}),timeout=60)
    return json.loads(r.read())
def log(d):
    open(OUT,'a').write(json.dumps(d,ensure_ascii=False)+'\n'); print(json.dumps(d,ensure_ascii=False)[:200],flush=True)
READ='JSON.stringify({u:location.href,t:document.title,x:(document.querySelector("main")||document.body).innerText,l:[...new Set([...document.querySelectorAll(\'a[href*="/talent/profile/"]\')].map(a=>a.href.split("?")[0]))]})'
NEXT='(function(){const b=document.querySelector(\'a[data-test-pagination-next], button[data-test-pagination-next], [aria-label="Go to next page"], a[title="Next"]\');if(!b)return "none";if(b.disabled||b.getAttribute("aria-disabled")==="true")return "disabled";b.click();return "clicked"})()'
mode=sys.argv[2]
if mode=='list':
    allp=[]; seen=set()
    for page in range(1,20):
        scroll(12); time.sleep(1)
        d=json.loads(js(READ)); new=[l for l in d['l'] if l not in seen]; seen.update(d['l']); allp+=new
        lu=d['u'] if 'start=' in d['u'] else d['u']+'&page=%d'%page
        r=post(lu+'#p%d'%page,d['t']+' [RPS 검색목록 p%d]'%page,d['x'])
        log({'kind':'list','page':page,'links':len(d['l']),'new':len(new),'id':r.get('id'),'dedup':r.get('deduped')})
        js('window.scrollTo(0,document.body.scrollHeight);1'); time.sleep(1)
        n=js(NEXT)
        if n!='clicked': log({'kind':'end','next':n}); break
        time.sleep(7)
    json.dump(allp,open(S+'/rps_profiles.json','w'))
    print('TOTAL',len(allp))
else:
    ps=json.load(open(S+'/rps_profiles.json')); done=set()
    if os.path.exists(OUT):
        for line in open(OUT):
            o=json.loads(line)
            if o.get('kind')=='profile' and o.get('ok'): done.add(o['url'])
    for i,u in enumerate(ps):
        if u in done: continue
        try:
            nav(u); time.sleep(6); scroll(4); time.sleep(1)
            d=json.loads(js(READ))
            if len(d['x'])<300: time.sleep(4); d=json.loads(js(READ))
            r=post(u,d['t'],d['x'])
            log({'kind':'profile','i':i,'url':u,'len':len(d['x']),'ok':bool(r.get('ok')),'id':r.get('id'),'dedup':r.get('deduped'),'title':d['t'][:60]})
        except Exception as e:
            log({'kind':'profile','i':i,'url':u,'ok':False,'err':str(e)[:200]})
