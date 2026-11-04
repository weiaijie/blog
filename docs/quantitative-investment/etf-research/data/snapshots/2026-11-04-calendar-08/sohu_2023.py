import fetch,json
p=fetch.BASE/'sohu_2023_requests.json'
if p.exists():raise FileExistsError('Fresh snapshot required')
r=fetch.run(('sohu_511010_2023','https://q.stock.sohu.com/hisHq?code=cn_511010&start=20230101&end=20231231&stat=1&order=D&period=d&rt=json'))
p.write_text(json.dumps([r],ensure_ascii=False,indent=2));print(r['name'],r.get('status'),r.get('error',''),r['bytes'])
