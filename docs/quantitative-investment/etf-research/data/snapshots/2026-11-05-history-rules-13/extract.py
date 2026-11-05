from pathlib import Path
import subprocess
from html.parser import HTMLParser
BASE=Path(__file__).parent
class Text(HTMLParser):
 def __init__(self):super().__init__();self.out=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.hidden+=1
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.hidden=max(0,self.hidden-1)
 def handle_data(self,data):
  if not self.hidden and data.strip():self.out.append(data.strip())
for f in BASE.glob('*.body'):
 if f.read_bytes().startswith(b'%PDF'):subprocess.run(['pdftotext','-layout',str(f),str(f.with_suffix('.txt'))],check=True)
 elif b'<html' in f.read_bytes().lower():
  parser=Text();parser.feed(f.read_bytes().decode('utf-8'));f.with_suffix('.txt').write_text('\n'.join(parser.out)+'\n')
