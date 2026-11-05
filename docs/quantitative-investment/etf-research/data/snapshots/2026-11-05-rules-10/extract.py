"""Extract official DOCX attachments without executing their contents."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,json,hashlib
root=Path(__file__).parent;records=json.loads((root/'attachment_requests.json').read_text())+json.loads((root/'history_attachment_requests.json').read_text());outputs=[]
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
for r in records:
 if '_attachment_' not in r['name'] or r.get('status')!=200:continue
 source=root/(r['name']+'.body')
 with zipfile.ZipFile(source) as archive:doc=ET.fromstring(archive.read('word/document.xml'))
 paragraphs=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in doc.findall('.//w:p',ns)]
 text='\n'.join(paragraphs)+'\n';path=root/(r['name']+'.txt');path.write_text(text)
 outputs.append({'source':source.name,'url':r['url'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'text':path.name,'text_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'paragraphs':len(paragraphs),'opening_lines':paragraphs[:4]})
(root/'extractions.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2)+'\n')
for x in outputs:print(x['source'],x['opening_lines'])
