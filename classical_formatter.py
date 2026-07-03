#!/usr/bin/env python3
"""Apple Music Classical Track Formatter v4 — with capitalization normalization"""
import sys, re, argparse, tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

CATALOG_RE=re.compile(r'(BWV\s*\d+|Op\.?\s*\d+|M\.?\s*\d+|K\.?\s*\d+|HWV\s*\d+|D\.?\s*\d+|S\.?\s*\d+|Wq\.?\s*\d+|F\.?\s*\d+|L\.?\s*\d+|RV\s*\d+|RCT\s*\d+)',re.IGNORECASE)
CN_NUM={'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
ARABIC_TO_CN={v:k for k,v in CN_NUM.items() if v!=0}
def c2a(s):
    s=s.strip()
    if s in CN_NUM: return CN_NUM[s]
    if '十' in s:
        p=s.split('十'); t=CN_NUM.get(p[0],1) if p[0] else 1; u=CN_NUM.get(p[1],0) if len(p)>1 and p[1] else 0
        return t*10+u
    return 0
def a2c(n):
    if n in ARABIC_TO_CN: return ARABIC_TO_CN[n]
    if 11<=n<=19:
        r='十'
        if n%10: r+=ARABIC_TO_CN.get(n%10,'')
        return r
    return str(n)
ROMAN_MAP={'I':1,'II':2,'III':3,'IV':4,'V':5,'VI':6,'VII':7,'VIII':8,'IX':9,'X':10,'XI':11,'XII':12,'XIII':13,'XIV':14,'XV':15}
FW_ROMAN=dict(zip('ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ','I II III IV V VI VII VIII IX X'.split()))
def norm_roman(r): return ''.join(FW_ROMAN.get(c,c) for c in r.strip().upper())
MM=re.compile(r'\b(Sonata|Concerto|Symphony|Quartet|Quintet|Trio|Duet|Duo|Fantasie|Fantasia|Overture|Rondo|Prelude|Fugue)\b',re.IGNORECASE)
MP=re.compile(r'\b(Suite|Etudes|Études|Preludes|Nocturnes|Waltzes|Impromptus|Ballades|Scherzos|Mazurkas|Polonaises|Fantastic\s*Dances)\b',re.IGNORECASE)

# ── Capitalization normalization ──────────────────────────────────
CAT_CAPS = {
    'bwv':'BWV','hwv':'HWV','rct':'RCT','rv':'RV',
    'op':'Op.','m':'M.','k':'K.','d':'D.','s':'S.','f':'F.','l':'L.','wq':'Wq',
}

def norm_cat(s):
    """Normalize catalog abbreviation casing in a string."""
    def repl(m):
        raw=m.group(0)
        key=raw.rstrip('.').lower()
        if key in CAT_CAPS:
            target=CAT_CAPS[key]
            if '.' in raw and '.' not in target:
                target+='.'
            if '.' not in raw and '.' in target:
                target=target.rstrip('.')
            return target
        return raw
    for abbr in CAT_CAPS:
        s=re.sub(r'\b'+abbr+r'\.?\b', repl, s, flags=re.IGNORECASE)
    return s

def cap_word(s):
    """Capitalize first letter of the first word, normalize rest to lowercase."""
    if not s: return s
    words=s.split()
    if not words: return s
    # First word: capitalize first letter, lowercase rest (for single-word fixes like aLlegretto)
    first=words[0]
    # Check if it's an all-caps abbreviation
    if first.upper()!=first or len(first)<=2:
        words[0]=first[0].upper()+first[1:].lower() if len(first)>1 else first.upper()
    return ' '.join(words)

LOW = ['a','an','the','and','but','or','for','nor','on','at','to','from','by','in','of','with','de','du','des','da','di','del','le','la','les','el']
def cap_title(s):
    """Apply Title Case: capitalize first/last word + significant words."""
    if not s: return s
    ws = s.split()
    if not ws: return s
    rs = []
    for i,w in enumerate(ws):
        clean = w.lstrip('"\'')
        if not clean:
            rs.append(w)
            continue
        if clean.upper() == clean and len(clean) > 1 and clean.isalpha():
            rs.append(w)
            continue
        prefix = w[:len(w) - len(clean)]
        if i == 0 or i == len(ws) - 1 or clean.lower() not in LOW:
            rs.append(prefix + clean[0].upper() + clean[1:].lower())
        else:
            rs.append(w.lower())
    return ' '.join(rs)

# ── ZH ──
ZR=re.compile('第([一二三四五六七八九十百]+)(首|乐章)[\.\u3002\s]*(.*)')
ZD=re.compile(r'\s+(第[一二三四五六七八九十百]+[首乐章曲])')
def pz(l):
    l=l.strip()
    if not l: return None
    wp=l; mp=None; arr=''
    # Normalize fullwidth/halfwidth punctuation differences
    l=l.replace(':', '：').replace(',', '，')
    if '：' in l:
        p=l.split('：',1); f=p[0].strip(); s=p[1].strip()
        if ZR.match(s): wp,mp=f,s
        else:
            sclean=re.sub(r'[（(][^）)]*[）)]','',s).strip()
            arr_m=re.search(r'[（(][^）)]*[）)]',s)
            if arr_m: arr=arr_m.group(0)
            mm=ZR.search(sclean)
            if mm:
                mtxt=mm.group(0)
                pos=s.find(mtxt)
                if pos>=0:
                    pre=s[:pos].strip()
                    if pre and pre[0] in "（(":
                        wp=(f+' '+pre).strip() if f else pre
                    else:
                        wp=pre
                    if arr_m and arr_m.start() >= pos:
                        arr=''
                    mp=s[pos:].strip()
                else:
                    wp=s[:mm.start()].strip()
                    mp=sclean[mm.start():].strip()
            else:
                wp=s; mm=ZD.search(wp)
                if mm: mp=wp[mm.start():].strip(); wp=wp[:mm.start()].strip()
                else: mp=None
    else:
        mm=ZD.search(wp)
        if mm: mp=wp[mm.start():].strip(); wp=wp[:mm.start()].strip()
        else: mp=None
    wt=wp; cat=''; cm=CATALOG_RE.search(wt)
    if cm: cat=norm_cat(cm.group(1).strip()); wt=wt[:cm.start()].rstrip(' ,，')
    if mp:
        mm=ZR.match(mp)
        if mm: return {'wt':wt,'cat':cat,'mt':mm.group(2),'mn':c2a(mm.group(1)),'mv':mm.group(3).strip(),'arr':arr}
        return None
    return {'wt':wt,'cat':cat,'mt':None,'mn':None,'mv':None,'arr':''}

def fz(p, ec=None):
    wd=(p['wt']+' '+(norm_cat(ec or p['cat'] or ''))).rstrip()
    if p['mn'] is None:
        return wd + (p.get('arr') or '')
    mv=p['mv'] or ''
    def cj(m): return ' - '+m.group(1) if re.match(r'^[\u4e00-\u9fff]+$',m.group(1)) else m.group(0)
    mv=mv.lstrip('-\u2013\u2014').strip()
    mv=re.sub(r'\(([^)]*)\)',cj,mv)
    mv=mv.replace('\u2500',' - ').replace('\uff0d',' - ').replace('，',' - ')
    mv=re.sub(r',(?:\s*)(?!\s*$)',' - ',mv)
    # Convert remaining spaces between Chinese characters to dash
    mv=re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])',' - ',mv)
    suffix=(p.get('arr') or '')+('No. '+str(p['mn'])+'・' if p['mt']=='首' else '第'+a2c(p['mn'])+'乐章・')
    return wd+'：'+suffix+mv
def fzt(ls): return [l if pz(l) is None else fz(pz(l)) for l in ls]

# ── EN ──
ES='^(.*?)\\s+[\\-'+chr(0x2013)+chr(0x2014)+']\\s+([ivxlcdmIVXLCDM'+chr(0x2160)+'-'+chr(0x217F)+']+)\\.\\s+(.*)$'
ED='^(.*?)\\s+([ivxlcdmIVXLCDM'+chr(0x2160)+'-'+chr(0x217F)+']+)\\.\\s+(.*)$'
EC='^(.*?),\\s*([A-Z]+\\.?\\s*\\d+)\\s*,\\s*(No\\.\\s*\\d+|V\\.?\\s*[ivxlcdmIVXLCDM'+chr(0x2160)+'-'+chr(0x217F)+']+)[,\\.]?\\s+(.*)$'
EN_SR=re.compile(ES); EN_DIRECT=re.compile(ED); EN_COLL=re.compile(EC,re.IGNORECASE)
KP=re.compile(r'\b([a-g])([-\s]?(?:flat|sharp|b|#))?\s+(minor|major)\b', re.IGNORECASE)
def nk(t):
    def rp(m):
        n=m.group(1).upper(); a=m.group(2) or ''; a=a.strip().lstrip('-').lstrip()
        if a.lower() in ('flat','b'): a='-Flat'
        elif a.lower() in ('sharp','#'): a='-Sharp'
        elif a: a='-'+a.capitalize()
        return n+a+' '+('Minor' if m.group(3).lower()=='minor' else 'Major')
    return KP.sub(rp,t)
def sc(tp):
    for s in['：',':']:
        if s in tp:
            p=tp.split(s,1); a=p[1].strip()
            if a and a[0].isupper(): return a
    return tp
def ic(ts):
    c=' '.join(t['tl'] for t in ts if t)
    if MM.search(c): return False
    if MP.search(c): return True
    return True


def pe(l):
    l=l.strip()
    if not l: return None
    l=l.replace('，',',').replace('：',':').replace('（','(').replace('）',')')
    l=re.sub(r',([A-Z])',r', \1',l)
    # Try direct : match first (preserves spacing)
    m2=re.match(r'^(.*?)'+chr(0xFF1A)+r'\s+([IVXLCDMivxlcdm\u2160-\u217F]+)\.\s+(.*)$',l)
    if not m2:
        m2=re.match(r'^(.*?):\s+([IVXLCDMivxlcdm\u2160-\u217F]+)\.\s+(.*)$',l)
    if m2:
        tp,rn,mn=m2.group(1).strip(),m2.group(2).strip(),m2.group(3).strip()
        rn=norm_roman(rn)
        tp=sc(tp); tp=nk(tp); tp=norm_cat(tp)
        cat=''; cm=CATALOG_RE.search(tp)
        if cm: cat=norm_cat(cm.group(1).strip())
        mv=cap_word(mn.strip())
        return {'tl':re.sub(r'\s+',' ',tp),'rn':rn,'r2':ROMAN_MAP.get(rn,0),'mv':re.sub(r'\s+',' ',mv).strip(),'cat':cat,'fmt':'std_dir'}
    # Fall back to dash-separated match
    l2=re.sub(r'\s*:\s+(?=[IVXLCDMivxlcdm\u2160-\u217F]+\.)',' - ',l)
    m=EN_SR.match(l2)
    if m:
        tp,rn,mn=m.group(1).strip(),m.group(2).strip(),m.group(3).strip()
        tp=sc(tp); tp=nk(tp); tp=norm_cat(tp)
        cat=''; cm=CATALOG_RE.search(tp)
        if cm: cat=norm_cat(cm.group(1).strip())
        mv=cap_word(mn.strip())
        return {'tl':re.sub(r'\s+',' ',tp),'rn':rn,'r2':ROMAN_MAP.get(rn,0),'mv':re.sub(r'\s+',' ',mv).strip(),'cat':cat,'fmt':'std'}
    m3=EN_DIRECT.match(l2)
    if m3:
        tp,rn,mn=m3.group(1).strip(),m3.group(2).strip(),m3.group(3).strip()
        tp=sc(tp); tp=nk(tp); tp=norm_cat(tp)
        cat=''; cm=CATALOG_RE.search(tp)
        if cm: cat=norm_cat(cm.group(1).strip())
        mv=cap_word(mn.strip())
        return {'tl':re.sub(r'\s+',' ',tp),'rn':rn,'r2':ROMAN_MAP.get(rn,0),'mv':re.sub(r'\s+',' ',mv).strip(),'cat':cat,'fmt':'std_dir'}
    stripped=sc(l)
    m4=EN_COLL.match(stripped)
    if m4:
        tp,mcat,num,mn=m4.group(1).strip(),m4.group(2).strip(),m4.group(3).strip(),m4.group(4).strip()
        rn=norm_roman(num.replace('No.','').replace('.','').strip())
        na=int(rn) if rn.isdigit() else ROMAN_MAP.get(rn,0)
        ir=bool(re.match(r'[ivxlcdmIVXLCDM]+$',num.replace('.','').strip()))
        tp=sc(tp); tp=nk(tp); tp=norm_cat(tp)
        return {'tl':re.sub(r'\s+',' ',tp+', '+norm_cat(mcat)),'rn':rn,'r2':na,'mv':cap_word(mn.strip()),'cat':norm_cat(mcat),'fmt':'coll_r' if ir else 'coll'}
    tp=nk(sc(l)); cat=''; cm=CATALOG_RE.search(tp)
    if cm: cat=norm_cat(cm.group(1).strip())
    tp=norm_cat(tp)
    return {'tl':re.sub(r'\s+',' ',tp),'rn':'','r2':0,'mv':'','cat':cat,'fmt':'single'}
def fe(p,isc):
    t=nk(p['tl'])
    if p['fmt']=='single': return t
    if isc:
        if p['fmt'] in ('coll_r','std_dir'): return t+': '+p['rn']+'. '+p['mv']
        mv=p['mv']
        mv=re.sub(r'\s*[\-\u2013\u2014]\s+','. ',mv)
        mv=re.sub(r'\b([a-z]+)\.\s+(?=[A-Z])',r'\1 — ',mv)
        mv=re.sub(r'\b([a-z]+)\.\s+([a-z])',lambda m:m.group(1)+' — '+m.group(2).upper(),mv)
        mv=re.sub(r'\.\s*([a-z])',lambda m:'.' + chr(32) + m.group(1).upper(),mv)
        ps=mv.split('. ',1) if '. ' in mv else [mv]
        if len(ps)>1 and ps[1].strip(): return t+': No. '+str(p['r2'])+', '+ps[0].strip()+'. '+ps[1].strip()
        return t+': No. '+str(p['r2'])+', '+mv
    mv=p['mv']
    mv=re.sub(r'\b([a-z]+)\.\s+(?=[A-Z])',r'\1 — ',mv)
    mv=re.sub(r'\b([a-z]+)\.\s+([a-z])',lambda m:m.group(1)+' — '+m.group(2).upper(),mv)
    mv=re.sub(r'\.\s*([a-z])',lambda m:'.' + chr(32) + m.group(1).upper(),mv)
    return t+': '+p['rn']+'. '+mv

def fet(ls):
    ap=[pe(l) for l in ls]; gr,cur,ck=[],[],None
    for p in ap:
        if p is None:
            if cur: gr.append(cur); cur,ck=[],None; continue
        if ck is None or p['tl']==ck: ck,cur=p['tl'],cur+[p]
        else: gr.append(cur); ck,cur=p['tl'],[p]
    if cur: gr.append(cur)
    fm={g[0]['tl']:ic(g) for g in gr}
    return [fe(p,fm.get(p['tl'],True)) for p in ap if p is not None]

def fp(ls):
    out=[]; i=0
    while i<len(ls):
        if i+1>=len(ls):
            zp=pz(ls[i]); ep=pe(ls[i])
            if ep and zp and not any('\u4e00'<=c<='\u9fff' for c in zp.get('wt','')):
                out.extend(fet([ls[i]]) if ep['fmt']!='single' else [ls[i]])
            elif zp: out.append(fz(zp))
            elif ep: out.extend(fet([ls[i]]))
            else: out.append(ls[i])
            i+=1; continue
        zp=pz(ls[i]); ep=pe(ls[i+1])
        if zp and ep:
            out.append(fz(zp,ec=ep.get('cat',''))); out.append(fe(ep,ic([ep])))
        elif zp: out.append(fz(zp)); out.append(ls[i+1])
        elif ep: out.append(ls[i]); out.append(fe(ep,ic([ep])))
        else: out.append(ls[i]); out.append(ls[i+1])
        i+=2
    return out

def cli_main():
    ap=argparse.ArgumentParser(description='Apple Music Track Formatter')
    ap.add_argument('--lang',choices=['zh','en','paired'],required=True)
    ap.add_argument('input',nargs='?')
    a=ap.parse_args()
    if a.input:
        with open(a.input,'r',encoding='utf-8-sig') as f: ls=[l.rstrip('\n\r') for l in f]
    else: ls=[l.rstrip('\n\r') for l in sys.stdin]
    while ls and not ls[-1].strip(): ls.pop()
    r=fp(ls) if a.lang=='paired' else (fzt(ls) if a.lang=='zh' else fet(ls))
    for l in r: print(l)

class App:
    def __init__(s,r):
        s.root=r; r.title('Apple Music 古典乐曲目标题格式化'); r.geometry('820x760'); r.minsize(600,500)
        mf=ttk.Frame(r); mf.pack(fill='x',padx=10,pady=(10,5))
        ttk.Label(mf,text='模式：').pack(side='left')
        s.mode=tk.StringVar(value='paired')
        for t,v in [('中文','zh'),('英文','en'),('配对(中+英)','paired')]:
            ttk.Radiobutton(mf,text=t,variable=s.mode,value=v,command=s.on_mode_change).pack(side='left',padx=5)
        ttk.Label(mf,text='  |  一行一首  |').pack(side='left')
        s.mh=ttk.Label(mf,text='配对模式：中英文交替'); s.mh.pack(side='right')
        ttk.Label(r,text='输入：').pack(anchor='w',padx=10,pady=(5,0))
        s.inp=scrolledtext.ScrolledText(r,height=12,font=('Consolas',10),wrap='word')
        s.inp.pack(fill='both',padx=10,pady=(2,5),expand=True)
        bf=ttk.Frame(r); bf.pack(fill='x',padx=10,pady=2)
        ttk.Button(bf,text='▶ 开始格式化',command=s.process).pack(side='left',padx=2)
        ttk.Button(bf,text='复制输出',command=s.copy_out).pack(side='left',padx=2)
        ttk.Button(bf,text='清空',command=s.clear_all).pack(side='left',padx=2)
        s.lc=ttk.Label(bf,text='行数: 0'); s.lc.pack(side='right',padx=5)
        ttk.Label(r,text='输出：').pack(anchor='w',padx=10,pady=(5,0))
        s.out=scrolledtext.ScrolledText(r,height=12,font=('Consolas',10),wrap='word',state='disabled')
        s.out.pack(fill='both',padx=10,pady=(2,10),expand=True)
        s.st=ttk.Label(r,text='就绪',relief='sunken',anchor='w'); s.st.pack(fill='x',padx=10,pady=(0,5))
        s.inp.bind('<KeyRelease>',s.on_input_change); s.on_mode_change()
    def on_mode_change(s): s.mh.config(text={'zh':'中文模式','en':'英文模式','paired':'配对模式：中英文交替'}.get(s.mode.get(),''))
    def on_input_change(s,e=None): ln=[l.strip() for l in s.inp.get('1.0','end-1c').split('\n') if l.strip()]; s.lc.config(text='行数: '+str(len(ln)))
    def process(s):
        t=s.inp.get('1.0','end-1c'); ln=[l.rstrip('\n\r') for l in t.split('\n')]
        while ln and not ln[-1].strip(): ln.pop()
        nn=[l for l in ln if l.strip()]
        if not nn: messagebox.showinfo('提示','请先输入曲目名称'); return
        m=s.mode.get()
        try:
            if m=='paired':
                if len(nn)%2!=0: s.st.config(text='配对模式行数为奇数')
                r=fp(ln)
            elif m=='zh': r=fzt(ln)
            else: r=fet(ln)
            s.out.config(state='normal'); s.out.delete('1.0','end'); s.out.insert('1.0','\n'.join(r))
            s.out.config(state='disabled'); s.st.config(text='完成 - 输出 '+str(len(r))+' 行')
        except Exception as e: messagebox.showerror('错误',str(e)); s.st.config(text='出错')
    def copy_out(s):
        t=s.out.get('1.0','end-1c')
        if t.strip(): s.root.clipboard_clear(); s.root.clipboard_append(t); s.st.config(text='已复制')
    def clear_all(s):
        s.inp.delete('1.0','end'); s.out.config(state='normal'); s.out.delete('1.0','end')
        s.out.config(state='disabled'); s.st.config(text='已清空'); s.lc.config(text='行数: 0')
def gui_main(): root=tk.Tk(); App(root); root.mainloop()
if __name__=='__main__':
    gui_main() if len(sys.argv)<=1 else cli_main()


