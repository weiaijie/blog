import fetch,json,concurrent.futures
jobs=[('sse_rules_2020','https://www.sse.com.cn/lawandrules/sselawsrules/repeal/rules/c/c_20230217_5716494.shtml'),('csrc_first_listing_2023','https://www.csrc.gov.cn/shanghai/c105566/c7402810/content.shtml'),('sse_first_listing_plan_2023','https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20230404_5719112.shtml')]
if (fetch.BASE/'history_requests.json').exists():raise FileExistsError('Fresh snapshot required')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:r=list(ex.map(fetch.run,jobs))
(fetch.BASE/'history_requests.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for x in r:print(x['name'],x.get('status'),x.get('error',''),x['bytes'])
