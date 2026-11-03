# 官方分红核验：第二批及全集对账

2026-11-03，计划第3项：现有21条事件逐字段官方核验完成。

## 完成情况

新增15份上交所原始公告PDF全部HTTP 200，逐一核对登记日、除息日、现金红利发放日、每份现金额，60项比较全部一致。结合第一批6份公告，共21次、84项字段一致。510300共14次，511010共7次；完整账本及每条证据路径见reconciliation.json，保留第一批证据引用。

并非只凭搜索摘要：从上交所官网公告页面实际JavaScript定位commonQuery.do及sqlId=COMMON_PL_JJXX_JJGG_NEW_L，读取完整目录。2012-01-01至2026-11-03窗口，510300返回259份公告、511010返回230份，pageCount均1，实际行数等于total。按“分红”或“收益分配”筛出的14+7份公告，与21条已核验事件的原文URL集合完全一致。初期仅搜“分红”漏掉510300早期“收益分配公告”，改为完整目录检索后补齐。

该完整性结论限于当前上交所目录和这两种标题用语，不能排除上游未收录或异常命名公告；不把目录范围内一致性夸大为绝对完整。

## 实现与证据

- requests.json、older_requests.json：新增15份PDF的URL、抓取UTC、状态、字节数及SHA256。
- *_all_index.body及对应request.json：未加标题过滤的完整官方目录原始响应和请求。
- *_index.body、510300_older_index.body：保留探索阶段查询结果。
- query.py/query_older.py/query_all.py：接口复现；download_new.py/download_older.py/fetch.py：下载与pdftotext -layout转换。
- sse-index.html、sse-query.js：官方网页与查询脚本来源，URL分别为https://www.sse.com.cn/disclosure/fund/announcement/和https://www.sse.com.cn/xhtml/home/2021public/querySearch/search_fundInformation_2021.js；首次抓取的精确时间未记录，不补造。
- reconcile.py：重新解析15份原文文本，单位从元/10份转换为元/份，核对第一批账本内对应供应商记录并进行目录全集对账。
- 511010的2013公告在提取文本中表格换行，使用限定的两行布局解析，不手填金额。

## 验证

4项回归检查通过：原始证据通过；PDF损坏、发放日期被改、分红金额变为10倍均被拒绝。运行python test_reconcile.py；运行目录需与2026-11-03-official-01相邻（仓库结构已满足），脚本会复制到临时目录，不改写原始PDF。

复验脚本会更新派生JSON，冻结快照应先复制后运行。下载/查询应使用新的快照目录，不覆盖既有响应。初始份额折算沿用第一批已核实的两份基金报告。

## 下一步与限制

第3项完成的范围是现有两标的、21次现金分红与两项初始份额折算。未重新获取2026-11-03实时行情，不产生收益率。第4项继续核验复权、成交量和独立日历；全历史收益研究仍须等待数据口径及现金会计检查。
