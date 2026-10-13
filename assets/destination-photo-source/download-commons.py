from pathlib import Path
import re,json,urllib.parse,urllib.request,time,sys,html
root=Path(__file__).resolve().parents[2]
source=(root/'main.js').read_text(encoding='utf-8')
m=re.search(r'const districtPlaces=(\{.*?\});\nconst cats=',source,re.S)
if not m: raise SystemExit('Could not read district attraction list')
places=json.loads(m.group(1).replace("'",'"'))
out=root/'assets'/'destinations'; out.mkdir(parents=True,exist_ok=True)
api='https://commons.wikimedia.org/w/api.php'
headers={'User-Agent':'SamvedTripExplores/1.0 (Karnataka tourism photo sourcing; contact: samvedtripexplores@gmail.com)','Accept':'application/json'}
used=set(); manifest={}; credits=[]; failures=[]
skip=re.compile(r'\b(map|diagram|logo|coat.of.arms|flag|seal|infographic|illustration|drawing|line.art|icon|vector|plan|sketch|chart|poster|stamp|painting|screenshot|watermark|location.map|route.map)\b',re.I)
def request(url):
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=35) as resp:return resp.read()
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def safe_meta(meta,key):
    value=(meta.get(key) or {}).get('value','')
    return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',value))).strip()
def get_candidate(spot,district):
    for phrase in (f'filetype:bitmap "{spot}"',f'filetype:bitmap {spot} {district} Karnataka'):
      params={'action':'query','generator':'search','gsrsearch':phrase,'gsrnamespace':6,'gsrlimit':30,'prop':'imageinfo','iiprop':'url|extmetadata|mime|size','iiurlwidth':1200,'format':'json'}
      try:data=json.loads(request(api+'?'+urllib.parse.urlencode(params)))
      except Exception as e:print('API ERROR',district,spot,str(e),flush=True);continue
      pages=list(data.get('query',{}).get('pages',{}).values());pages.sort(key=lambda p:p.get('index',999))
      for page in pages:
       title=page.get('title',''); info=(page.get('imageinfo') or [{}])[0];meta=info.get('extmetadata') or {}
       mime=info.get('mime','').lower(); width=info.get('width',0);height=info.get('height',0);lic=safe_meta(meta,'LicenseShortName')
       if mime not in ('image/jpeg','image/png','image/webp') or width<620 or height<390 or max(width/height,height/width)>2.5:continue
       if skip.search(title) or not info.get('thumburl') or not lic:continue
       if re.search(r'non.?commercial|\bNC\b',lic,re.I):continue
       url=info['thumburl']
       if url in used:continue
       # On the fallback query, insist on a recognizable local/place name in title or description metadata.
       tokens=[t.lower() for t in re.findall(r'[a-zA-Z0-9]+',spot) if len(t)>3]
       local=[t.lower() for t in re.findall(r'[a-zA-Z0-9]+',district) if len(t)>3]
       identity=' '.join([title,safe_meta(meta,'ImageDescription'),safe_meta(meta,'ObjectName')]).lower()
       if phrase.startswith('filetype:bitmap "') and tokens and not any(t in identity for t in tokens):continue
       if not phrase.startswith('filetype:bitmap "') and not any(t in identity for t in tokens+local):continue
       return page,info,meta,lic
      time.sleep(.12)
    return None
for di,(district,spots) in enumerate(places.items(),1):
 folder=out/slug(district);folder.mkdir(parents=True,exist_ok=True);manifest[district]=[]
 print(f'[{di}/{len(places)}] {district}',flush=True)
 for i,spot in enumerate(spots,1):
  found=get_candidate(spot,district)
  if not found:
   failures.append({'district':district,'spot':spot,'reason':'No matching licensed photograph found after exact-place and district searches'});print('  MISS',spot,flush=True);continue
  page,info,meta,license=found;url=info['thumburl'];ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[info['mime'].lower()];filename=f'{slug(district)}-{i:02d}.{ext}';path=folder/filename
  try:
   req=urllib.request.Request(url,headers=headers)
   with urllib.request.urlopen(req,timeout=45) as resp:path.write_bytes(resp.read())
   if path.stat().st_size<12000:raise ValueError('photo payload too small')
  except Exception as e:
   failures.append({'district':district,'spot':spot,'reason':str(e)});print('  DL ERROR',spot,str(e),flush=True);continue
  used.add(url);artist=safe_meta(meta,'Artist') or safe_meta(meta,'Credit') or 'Unknown';license_url=safe_meta(meta,'LicenseUrl');description=info.get('descriptionurl','')
  entry={'spot':spot,'src':'./assets/destinations/'+slug(district)+'/'+filename,'alt':f'{spot}, {district} district, Karnataka','credit':artist,'license':license,'licenseUrl':license_url,'sourceUrl':description}
  manifest[district].append(entry)
  credits.append({'district':district,'spot':spot,'filename':str(path.relative_to(root)).replace('\\','/'),'credit':artist,'attribution':safe_meta(meta,'Attribution'),'license':license,'licenseUrl':license_url,'sourceUrl':description,'imagePageTitle':page.get('title','')})
  print('  PHOTO',spot,'|',license,'|',filename,flush=True);time.sleep(.08)
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'download-report.json').write_text(json.dumps({'requested':sum(map(len,places.values())),'downloaded':len(credits),'failed':failures},ensure_ascii=False,indent=2),encoding='utf-8')
print('COMPLETE',len(credits),'photos from',sum(map(len,places.values())),'attractions; misses',len(failures),flush=True)
