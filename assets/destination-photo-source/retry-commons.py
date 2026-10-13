from pathlib import Path
import re,json,urllib.parse,urllib.request,time,html,sys
root=Path(__file__).resolve().parents[2];out=root/'assets'/'destinations';src=(root/'main.js').read_text(encoding='utf-8')
m=re.search(r'const districtPlaces=(\{.*?\});\nconst cats=',src,re.S);places=json.loads(m.group(1).replace("'",'"'))
manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8')); credits=json.loads((out/'credits.json').read_text(encoding='utf-8'));report=json.loads((out/'download-report.json').read_text(encoding='utf-8'))
headers={'User-Agent':'SamvedTripExplores/1.0 (Karnataka tourism photo sourcing; contact: samvedtripexplores@gmail.com)','Accept':'application/json'};api='https://commons.wikimedia.org/w/api.php';used={x['sourceUrl'] for x in credits};skip=re.compile(r'\b(map|diagram|logo|coat.of.arms|flag|seal|infographic|illustration|drawing|line.art|icon|vector|plan|sketch|chart|poster|stamp|painting|screenshot|watermark)\b',re.I)
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=35) as r:return r.read()
def slug(x):return re.sub(r'[^a-z0-9]+','-',x.lower()).strip('-')
def meta(m,k):
 v=(m.get(k) or {}).get('value','');return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',v))).strip()
fail=[]
for rec in report['failed']:
 district,spot=rec['district'],rec['spot'];folder=out/slug(district);folder.mkdir(parents=True,exist_ok=True)
 for phrase in (f'filetype:bitmap "{spot}"',f'filetype:bitmap {spot} {district} Karnataka'):
  params={'action':'query','generator':'search','gsrsearch':phrase,'gsrnamespace':6,'gsrlimit':30,'prop':'imageinfo','iiprop':'url|extmetadata|mime|size','iiurlwidth':1200,'format':'json'}
  try:data=json.loads(get(api+'?'+urllib.parse.urlencode(params)))
  except Exception as e:print('API ERROR',spot,str(e),flush=True);continue
  pages=list(data.get('query',{}).get('pages',{}).values());pages.sort(key=lambda p:p.get('index',999))
  for page in pages:
   info=(page.get('imageinfo') or [{}])[0];md=info.get('extmetadata') or {};mime=info.get('mime','').lower();w=info.get('width',0);h=info.get('height',0);lic=meta(md,'LicenseShortName');title=page.get('title','');url=info.get('thumburl','')
   if mime not in ('image/jpeg','image/png','image/webp') or w<620 or h<390 or max(w/h,h/w)>2.5 or skip.search(title) or not url or not lic or re.search(r'non.?commercial|\bNC\b',lic,re.I) or url in used:continue
   artist=meta(md,'Artist') or meta(md,'Credit') or 'Unknown';sourceurl=info.get('descriptionurl','')
   # Prefer images whose indexed file title/description names the exact landmark.
   used.add(url);ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[mime]; existing={int(re.search(r'-(\d+)\.',p.name).group(1)) for p in folder.glob(slug(district)+'-*.jpg') if re.search(r'-(\d+)\.',p.name)}|{int(re.search(r'-(\d+)\.',p.name).group(1)) for p in folder.glob(slug(district)+'-*.png') if re.search(r'-(\d+)\.',p.name)}
   slot=next((n for n in range(1,13) if n not in existing),len(existing)+1);name=f'{slug(district)}-{slot:02d}.{ext}';path=folder/name
   try:path.write_bytes(get(url))
   except Exception as e:print('DL ERROR',spot,str(e),flush=True);continue
   entry={'spot':spot,'src':'./assets/destinations/'+slug(district)+'/'+name,'alt':f'{spot}, {district} district, Karnataka','credit':artist,'license':lic,'licenseUrl':meta(md,'LicenseUrl'),'sourceUrl':sourceurl}
   manifest.setdefault(district,[]).append(entry);credits.append({'district':district,'spot':spot,'filename':str(path.relative_to(root)).replace('\\','/'),'credit':artist,'attribution':meta(md,'Attribution'),'license':lic,'licenseUrl':meta(md,'LicenseUrl'),'sourceUrl':sourceurl,'imagePageTitle':title})
   print('ADDED',district,'|',spot,'|',title,'|',lic,flush=True);break
  if any(x.get('spot')==spot and x.get('district')==district for x in credits):break
 else:fail.append(rec);print('STILL MISSING',district,spot,flush=True)
 time.sleep(.06)
# maintain a unique, curated order according to the district attraction list
for district,arr in manifest.items():arr.sort(key=lambda x:places.get(district,[]).index(x['spot']) if x['spot'] in places.get(district,[]) else 99)
report['downloaded']=len(credits);report['failed']=fail
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(out/'credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2),encoding='utf-8');(out/'download-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('RETRY COMPLETE',len(credits),'total photos; unresolved',len(fail),flush=True)
