from pathlib import Path
import re,json,urllib.parse,urllib.request,time,html
root=Path(__file__).resolve().parents[2];out=root/'assets'/'destinations';manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'));credits=json.loads((out/'credits.json').read_text(encoding='utf-8'));headers={'User-Agent':'SamvedTripExplores/1.0 (Karnataka tourism photo sourcing; contact: samvedtripexplores@gmail.com)','Accept':'application/json'};api='https://commons.wikimedia.org/w/api.php';used={x['sourceUrl'] for x in credits};skip=re.compile(r'\b(map|diagram|logo|coat.of.arms|flag|seal|infographic|illustration|drawing|line.art|icon|vector|plan|sketch|chart|poster|stamp|painting|screenshot|watermark)\b',re.I)
alternatives={
'Ballari':['Sandur','Kumaraswamy Temple Sandur','Toranagallu','Siruguppa'],
'Belagavi':['Kapileshwara Temple Belagavi','Hooli Panchalingeshwara Temple','Military Mahadeva Temple Belagavi','Naviluteertha Dam'],
'Bengaluru Rural':['Chikka Tirupati Temple','Doddaballapur','Vijayapura Karnataka','Devanahalli Karnataka'],
'Bidar':['Chaubara Clock Tower Bidar','Mahmud Gawan Madrasa','Ashtur Tombs Bidar','Papnash Temple Bidar'],
'Davanagere':['Harihar Karnataka','Sulekere Davanagere','Uchangidurga','Anagodu Karnataka'],
'Dharwad':['Nuggikeri Hanuman Temple','Siddharoodha Matha','Amargol Temple Dharwad','Tapovan Dharwad'],
'Raichur':['Mudgal Fort','Hatti Gold Mines','Manvi Karnataka','Jaladurga Fort Raichur'],
'Tumakuru':['Mandaragiri Jain Temple','Kaidala Chennakeshava Temple','Markonahalli Dam','Sira Fort Karnataka'],
'Yadgiri':['Yadgir Fort','Shorapur Palace','Shorapur Karnataka','Jaladurga Fort Karnataka']}
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=35) as r:return r.read()
def slug(x):return re.sub(r'[^a-z0-9]+','-',x.lower()).strip('-')
def clean(meta,key):
 v=(meta.get(key) or {}).get('value','');return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',v))).strip()
for district,spots in alternatives.items():
 have=len(manifest.get(district,[]));print('GAP',district,have,flush=True)
 if have>=5:continue
 folder=out/slug(district);folder.mkdir(parents=True,exist_ok=True)
 for spot in spots:
  if len(manifest.get(district,[]))>=6:break
  phrase=f'filetype:bitmap "{spot}"';params={'action':'query','generator':'search','gsrsearch':phrase,'gsrnamespace':6,'gsrlimit':25,'prop':'imageinfo','iiprop':'url|extmetadata|mime|size','iiurlwidth':1200,'format':'json'}
  try:data=json.loads(get(api+'?'+urllib.parse.urlencode(params)))
  except Exception as e:print('API ERROR',spot,str(e),flush=True);continue
  pages=list(data.get('query',{}).get('pages',{}).values());pages.sort(key=lambda p:p.get('index',999));added=False
  for page in pages:
   info=(page.get('imageinfo') or [{}])[0];md=info.get('extmetadata') or {};mime=info.get('mime','').lower();w=info.get('width',0);h=info.get('height',0);lic=clean(md,'LicenseShortName');url=info.get('thumburl','');title=page.get('title','')
   if mime not in ('image/jpeg','image/png','image/webp') or w<620 or h<390 or max(w/h,h/w)>2.5 or skip.search(title) or not url or not lic or re.search(r'non.?commercial|\bNC\b',lic,re.I) or url in used:continue
   artist=clean(md,'Artist') or clean(md,'Credit') or 'Unknown';sourceurl=info.get('descriptionurl','');ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[mime];num=len(manifest.get(district,[]))+1;filename=f'{slug(district)}-{num:02d}.{ext}';path=folder/filename
   try:path.write_bytes(get(url))
   except Exception as e:print('DL ERROR',spot,str(e),flush=True);continue
   entry={'spot':spot,'src':'./assets/destinations/'+slug(district)+'/'+filename,'alt':f'{spot}, {district} district, Karnataka','credit':artist,'license':lic,'licenseUrl':clean(md,'LicenseUrl'),'sourceUrl':sourceurl}
   manifest.setdefault(district,[]).append(entry);credits.append({'district':district,'spot':spot,'filename':str(path.relative_to(root)).replace('\\','/'),'credit':artist,'attribution':clean(md,'Attribution'),'license':lic,'licenseUrl':clean(md,'LicenseUrl'),'sourceUrl':sourceurl,'imagePageTitle':title});used.add(url)
   print('ADDED',district,'|',spot,'|',title,'|',lic,flush=True);added=True;break
  time.sleep(.08)
  if added:continue
  print('MISS',district,'|',spot,flush=True)
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(out/'credits.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2),encoding='utf-8')
print('GAPS AFTER FILL', {k:len(manifest[k]) for k in alternatives},flush=True)
