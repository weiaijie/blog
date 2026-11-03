import fetch,json
if __name__=='__main__':
    r=fetch.fetch(('510300_2025_report','https://www.sse.com.cn/disclosure/fund/announcement/c/new/2025-08-30/510300_20250830_9SZQ.pdf'))
    (fetch.P/'extra_requests.json').write_text(json.dumps([r],ensure_ascii=False,indent=2))
