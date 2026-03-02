/* eslint-disable */
const FULL_STATUS = {
    "_CONFIRMSTATUS": [
        {
            "value": "1",
            "label": "是"
        },
        {
            "value": "2",
            "label": "否"
        }
    ],
    "_SEX": [
        {
            "value": "0",
            "label": "未知"
        },
        {
            "value": "1",
            "label": "男性"
        },
        {
            "value": "2",
            "label": "女性"
        }
    ],
    "_STANDARDSTATUS": [
        {
            "value": "1",
            "label": "启用"
        },
        {
            "value": "2",
            "label": "禁用"
        }
    ],
    "_UAGESTATUS": [
        {
            "value": "1",
            "label": "在用"
        },
        {
            "value": "2",
            "label": "历史"
        }
    ],
    "_VALUETYPE": [
        {
            "value": "1",
            "label": "文本"
        },
        {
            "value": "2",
            "label": "数字"
        },
        {
            "value": "3",
            "label": "数字数组"
        },
        {
            "value": "4",
            "label": "布尔类型"
        },
        {
            "value": "5",
            "label": "文本数组"
        },
        {
            "value": "6",
            "label": "对象"
        }
    ],
    "TENANT_TABLECOLUMNSETTINGTYPE": [
        {
            "value": "1",
            "label": "CJKJ.Product.Tenant.TableColumnSettingType"
        },
        {
            "value": "2",
            "label": "CJKJ.Product.Tenant.TableColumnSettingType"
        }
    ],
    "QRCODE_ACTIONTYPE": [
        {
            "value": "1",
            "label": "接口调用"
        },
        {
            "value": "2",
            "label": "页面跳转"
        }
    ],
    "WORKFLOW_AUDITTYPE": [
        {
            "value": "1",
            "label": "全审"
        },
        {
            "value": "2",
            "label": "或审"
        },
        {
            "value": "3",
            "label": "抄送"
        }
    ],
    "WORKFLOW_HANDLERTYPE": [
        {
            "value": "1",
            "label": "指定人"
        },
        {
            "value": "2",
            "label": "部门领导"
        }
    ],
    "WORKFLOW_PROCESSNODESTATUS": [
        {
            "value": "1",
            "label": "待处理"
        },
        {
            "value": "2",
            "label": "已通过"
        },
        {
            "value": "3",
            "label": "已驳回"
        },
        {
            "value": "4",
            "label": "已抄送"
        }
    ],
    "WORKFLOW_PROCESSSTATUS": [
        {
            "value": "1",
            "label": "待提交"
        },
        {
            "value": "2",
            "label": "待审核"
        },
        {
            "value": "3",
            "label": "已通过"
        },
        {
            "value": "4",
            "label": "已驳回"
        }
    ],
    "WORKFLOW_WORKFLOWBIZTYPE": [
        {
            "value": "1",
            "label": "费用申请"
        },
        {
            "value": "2",
            "label": "发票申请"
        }
    ],
    "WAREHOUSE_ITEMSKUSTOCKADJUSTREASONTYPE": [
        {
            "value": "1",
            "label": "调整增加"
        },
        {
            "value": "2",
            "label": "调整减少"
        },
        {
            "value": "3",
            "label": "成本调整"
        },
        {
            "value": "4",
            "label": "成本差异"
        },
        {
            "value": "5",
            "label": "其他入库"
        },
        {
            "value": "6",
            "label": "其他出库"
        }
    ],
    "STORE_EMPLOYEETYPE": [
        {
            "value": "1",
            "label": "正式员工"
        },
        {
            "value": "2",
            "label": "实习员工"
        },
        {
            "value": "3",
            "label": "店长"
        }
    ],
    "STORE_STOREPIRCETYPE": [
        {
            "value": "1",
            "label": "折扣"
        },
        {
            "value": "2",
            "label": "立减"
        },
        {
            "value": "3",
            "label": "最终价格"
        }
    ],
    "STORE_STOREUSERSTATUS": [
        {
            "value": "1",
            "label": "在职"
        },
        {
            "value": "2",
            "label": "离职"
        }
    ],
    "PO_POACTION": [
        {
            "value": "1",
            "label": "提交审核"
        },
        {
            "value": "2",
            "label": "审核通过"
        },
        {
            "value": "3",
            "label": "审核拒绝"
        },
        {
            "value": "4",
            "label": "创建"
        },
        {
            "value": "5",
            "label": "取消"
        },
        {
            "value": "6",
            "label": "结束"
        },
        {
            "value": "7",
            "label": "WMS已接收"
        },
        {
            "value": "8",
            "label": "采购退货强制完成"
        },
        {
            "value": "9",
            "label": "结束采购行"
        },
        {
            "value": "10",
            "label": "最终审核通过"
        },
        {
            "value": "11",
            "label": "最终审核拒绝"
        }
    ],
    "PO_POACTIONSOUCE": [
        {
            "value": "1",
            "label": "采购单"
        },
        {
            "value": "2",
            "label": "采购退货"
        }
    ],
    "PO_POAUDITSTATUS": [
        {
            "value": "1",
            "label": "无需审核"
        },
        {
            "value": "2",
            "label": "待审核"
        },
        {
            "value": "3",
            "label": "审核完成"
        },
        {
            "value": "4",
            "label": "审核拒绝"
        }
    ],
    "PO_POFILELANG": [
        {
            "value": "1",
            "label": "中文"
        },
        {
            "value": "2",
            "label": "英语"
        },
        {
            "value": "3",
            "label": "日语"
        }
    ],
    "PO_POFUTURESINVENTORYSTATUS": [
        {
            "value": "1",
            "label": "采购中"
        },
        {
            "value": "2",
            "label": " 已完成"
        }
    ],
    "PO_POINVENTORYACTION": [
        {
            "value": "1",
            "label": "创建入库单"
        },
        {
            "value": "2",
            "label": "同步数据"
        },
        {
            "value": "3",
            "label": "手动收货"
        },
        {
            "value": "4",
            "label": "手动完成"
        },
        {
            "value": "5",
            "label": "手动强制完成"
        },
        {
            "value": "6",
            "label": "手动取消"
        },
        {
            "value": "7",
            "label": "WMS收货"
        },
        {
            "value": "8",
            "label": "WMS完成"
        },
        {
            "value": "9",
            "label": "WMS强制完成"
        },
        {
            "value": "10",
            "label": "WMS取消"
        }
    ],
    "PO_POMODES": [
        {
            "value": "1",
            "label": "缺货采购"
        },
        {
            "value": "2",
            "label": "计划采购"
        }
    ],
    "PO_POPRICETYPE": [
        {
            "value": "1",
            "label": "VIP采购价"
        },
        {
            "value": "2",
            "label": "标准采购价"
        }
    ],
    "PO_PORECEIVEDETAILSSTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": " 已完成"
        },
        {
            "value": "3",
            "label": "已取消"
        }
    ],
    "PO_PORETURNSTATUS": [
        {
            "value": "1",
            "label": "待审核"
        },
        {
            "value": "2",
            "label": "审核中"
        },
        {
            "value": "3",
            "label": "审核完成"
        },
        {
            "value": "4",
            "label": "审核拒绝"
        },
        {
            "value": "5",
            "label": "已取消"
        },
        {
            "value": "6",
            "label": "结束"
        }
    ],
    "PO_PORETURNTYPE": [
        {
            "value": "1",
            "label": "汇总退货"
        },
        {
            "value": "2",
            "label": "采购退货"
        }
    ],
    "PO_POSOUCE": [
        {
            "value": "1",
            "label": "内采"
        },
        {
            "value": "2",
            "label": "外采"
        }
    ],
    "PO_POSTATUS": [
        {
            "value": "1",
            "label": "草稿"
        },
        {
            "value": "2",
            "label": "交期待确认"
        },
        {
            "value": "3",
            "label": "交期确认完成"
        },
        {
            "value": "4",
            "label": "交期确认拒绝"
        },
        {
            "value": "5",
            "label": "已取消"
        },
        {
            "value": "6",
            "label": "已结束"
        }
    ],
    "PO_POSTORAGESTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "WMS已收到"
        },
        {
            "value": "3",
            "label": "处理完成"
        },
        {
            "value": "4",
            "label": "强制完成"
        },
        {
            "value": "5",
            "label": "取消"
        },
        {
            "value": "6",
            "label": "处理中"
        }
    ],
    "PO_POTYPE": [
        {
            "value": "1",
            "label": "国内"
        },
        {
            "value": "2",
            "label": "国外"
        }
    ],
    "ORDER_CONVERTORDERSTATUS": [
        {
            "value": "1",
            "label": "待审核"
        },
        {
            "value": "2",
            "label": "已审核"
        },
        {
            "value": "3",
            "label": "已完成"
        },
        {
            "value": "4",
            "label": "已取消"
        }
    ],
    "ORDER_DELIVERYTYPE": [
        {
            "value": "1",
            "label": "包装发货"
        },
        {
            "value": "2",
            "label": "整箱发货"
        },
        {
            "value": "3",
            "label": "散装发货"
        }
    ],
    "ORDER_EBANKTRANSSTATUS": [
        {
            "value": "1",
            "label": "成功"
        },
        {
            "value": "2",
            "label": "未支付"
        },
        {
            "value": "3",
            "label": "失败"
        }
    ],
    "ORDER_FUTUREORDERSTATUS": [
        {
            "value": "1",
            "label": "采购中"
        },
        {
            "value": "2",
            "label": "已入库"
        },
        {
            "value": "3",
            "label": "已取消"
        }
    ],
    "ORDER_HANDLETYPESTRUCT": [
        {
            "value": "1",
            "label": "新增"
        },
        {
            "value": "2",
            "label": "修改"
        },
        {
            "value": "3",
            "label": "审核"
        },
        {
            "value": "4",
            "label": "结束"
        },
        {
            "value": "5",
            "label": "删除"
        },
        {
            "value": "6",
            "label": "取消"
        },
        {
            "value": "7",
            "label": "挂起"
        },
        {
            "value": "8",
            "label": "取消挂起"
        }
    ],
    "ORDER_INVOICEBILLINGTYPE": [
        {
            "value": "1",
            "label": "按明细开票"
        },
        {
            "value": "2",
            "label": "按分类开票"
        }
    ],
    "ORDER_INVOICESOURCE": [
        {
            "value": "1",
            "label": "订单"
        },
        {
            "value": "2",
            "label": "退款"
        }
    ],
    "ORDER_ISNOTICEDENUM": [
        {
            "value": "1",
            "label": "是"
        },
        {
            "value": "2",
            "label": "否"
        }
    ],
    "ORDER_LINETYPESTRUCT": [
        {
            "value": "1",
            "label": "换出行"
        },
        {
            "value": "2",
            "label": "正常行"
        },
        {
            "value": "3",
            "label": "退货行"
        }
    ],
    "ORDER_ORDERALLOCATESTOCKNODE": [
        {
            "value": "1",
            "label": "不占用"
        },
        {
            "value": "2",
            "label": "下单占用"
        },
        {
            "value": "3",
            "label": "审核占用"
        }
    ],
    "ORDER_ORDERAUDITREASON": [
        {
            "value": "1",
            "label": "全部订单审核"
        },
        {
            "value": "2",
            "label": "月度预算超支"
        },
        {
            "value": "3",
            "label": "订单金额超出"
        },
        {
            "value": "4",
            "label": "年度预算超支"
        },
        {
            "value": "5",
            "label": "季度预算超支"
        }
    ],
    "ORDER_ORDERAUDITSTATUS": [
        {
            "value": "1",
            "label": "申请"
        },
        {
            "value": "2",
            "label": "审核通过"
        },
        {
            "value": "3",
            "label": "退回"
        },
        {
            "value": "4",
            "label": "取消"
        }
    ],
    "ORDER_ORDERCANCELREASONUSAGE": [
        {
            "value": "1",
            "label": "全部"
        },
        {
            "value": "2",
            "label": "内部"
        },
        {
            "value": "3",
            "label": "外部"
        }
    ],
    "ORDER_ORDERITEMSKUPAYSHARESTATUS": [
        {
            "value": "1",
            "label": "成功"
        },
        {
            "value": "2",
            "label": "取消"
        }
    ],
    "ORDER_ORDERITEMSKUSTOCKSTATUS": [
        {
            "value": "1",
            "label": "未分配"
        },
        {
            "value": "2",
            "label": "已分配"
        },
        {
            "value": "3",
            "label": "缺货"
        },
        {
            "value": "4",
            "label": "期货"
        },
        {
            "value": "5",
            "label": "已分配（部分缺货）"
        },
        {
            "value": "6",
            "label": "已分配（部分期货）"
        },
        {
            "value": "7",
            "label": "已分配（部分期货，部分缺货）"
        },
        {
            "value": "8",
            "label": "部分期货，部分缺货"
        }
    ],
    "ORDER_ORDERPAYSTATUS": [
        {
            "value": "1",
            "label": "成功"
        },
        {
            "value": "2",
            "label": "失败"
        },
        {
            "value": "3",
            "label": "未处理"
        },
        {
            "value": "4",
            "label": "取消"
        }
    ],
    "ORDER_ORDERPAYTRANSTYPE": [
        {
            "value": "1",
            "label": "帐户付款"
        },
        {
            "value": "2",
            "label": "付款"
        },
        {
            "value": "3",
            "label": "退货"
        },
        {
            "value": "4",
            "label": "取消"
        }
    ],
    "ORDER_ORDERSEARCHTYPE": [
        {
            "value": "1",
            "label": "全部"
        },
        {
            "value": "2",
            "label": "待付款"
        },
        {
            "value": "3",
            "label": "待发货"
        },
        {
            "value": "4",
            "label": "待收货"
        },
        {
            "value": "5",
            "label": "已取消"
        },
        {
            "value": "6",
            "label": "子订单待审"
        },
        {
            "value": "7",
            "label": "已完成"
        },
        {
            "value": "8",
            "label": "备货中"
        }
    ],
    "ORDER_ORDERSOURCETYPE": [
        {
            "value": "1",
            "label": "全部"
        },
        {
            "value": "2",
            "label": "内部"
        },
        {
            "value": "3",
            "label": "外部"
        }
    ],
    "ORDER_OUTOFSTOCKORDERSTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "已完成"
        },
        {
            "value": "3",
            "label": "已取消"
        },
        {
            "value": "4",
            "label": "已分配"
        }
    ],
    "ORDER_OUTOFSTOCKORDERTYPE": [
        {
            "value": "1",
            "label": "缺货"
        },
        {
            "value": "2",
            "label": "期货"
        }
    ],
    "ORDER_PACKINGABOVEQUOTACHANGETYPE": [
        {
            "value": "1",
            "label": "任务挂起"
        },
        {
            "value": "2",
            "label": "任务释放"
        }
    ],
    "ORDER_PACKINGSLIPHANDLETYPE": [
        {
            "value": "1",
            "label": "预选"
        },
        {
            "value": "2",
            "label": "装箱"
        },
        {
            "value": "3",
            "label": "发货"
        },
        {
            "value": "4",
            "label": "回单确认"
        },
        {
            "value": "5",
            "label": "反预选"
        },
        {
            "value": "6",
            "label": "仓库内部处理"
        },
        {
            "value": "7",
            "label": "快递公司外部处理"
        }
    ],
    "ORDER_PACKINGSLIPITEMSKUSTOCKSTATUS": [
        {
            "value": "1",
            "label": "分配"
        },
        {
            "value": "2",
            "label": "缺货"
        },
        {
            "value": "3",
            "label": "未分配"
        }
    ],
    "ORDER_PACKINGSLIPSTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "装箱"
        },
        {
            "value": "3",
            "label": "发货"
        },
        {
            "value": "4",
            "label": "回单确认"
        },
        {
            "value": "5",
            "label": "反预选"
        }
    ],
    "ORDER_PAYTYPEGROUP": [
        {
            "value": "1",
            "label": "月结支付"
        },
        {
            "value": "2",
            "label": "线下支付"
        },
        {
            "value": "3",
            "label": "账户支付"
        },
        {
            "value": "4",
            "label": "在线支付"
        }
    ],
    "ORDER_PAYTYPEINFO": [
        {
            "value": "1",
            "label": "月结支付"
        },
        {
            "value": "2",
            "label": "转账付款"
        }
    ],
    "ORDER_REASONTYPESTRUCT": [
        {
            "value": "1",
            "label": "有商品缺货"
        },
        {
            "value": "2",
            "label": "运费"
        },
        {
            "value": "3",
            "label": "超日购买频率"
        },
        {
            "value": "4",
            "label": "最大订单金额"
        },
        {
            "value": "5",
            "label": "超月购买频率"
        },
        {
            "value": "6",
            "label": "最大商品种类"
        },
        {
            "value": "7",
            "label": "最大商品总数量"
        },
        {
            "value": "8",
            "label": "送货地址为新地址"
        },
        {
            "value": "9",
            "label": "新客户"
        },
        {
            "value": "10",
            "label": "增票信息未审核"
        },
        {
            "value": "11",
            "label": "订单留言"
        },
        {
            "value": "12",
            "label": "订单开增票"
        },
        {
            "value": "13",
            "label": "其他"
        }
    ],
    "ORDER_RECEIVABLEBILLSEARCHTYPE": [
        {
            "value": "1",
            "label": "全部"
        },
        {
            "value": "2",
            "label": "应付"
        },
        {
            "value": "3",
            "label": "已付"
        },
        {
            "value": "4",
            "label": "超期"
        }
    ],
    "ORDER_RECEIVABLEBILLSTATUS": [
        {
            "value": "1",
            "label": "未支付"
        },
        {
            "value": "2",
            "label": "部分支付"
        },
        {
            "value": "3",
            "label": "全部支付"
        }
    ],
    "ORDER_RECEIVABLEBILLTYPE": [
        {
            "value": "1",
            "label": "发货单"
        },
        {
            "value": "2",
            "label": "退货单"
        }
    ],
    "ORDER_REFUNDBILLSTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "已处理"
        }
    ],
    "ORDER_REFUNDBILLTYPE": [
        {
            "value": "1",
            "label": "订单"
        },
        {
            "value": "2",
            "label": "订单行"
        },
        {
            "value": "3",
            "label": "支付记录"
        },
        {
            "value": "4",
            "label": "退货"
        }
    ],
    "ORDER_RETURNAPPLYLABEL": [
        {
            "value": "1",
            "label": "全部拒收"
        },
        {
            "value": "2",
            "label": "退换货"
        },
        {
            "value": "3",
            "label": "部分拒收"
        }
    ],
    "ORDER_RETURNAPPLYSTATUS": [
        {
            "value": "1",
            "label": "申请中"
        },
        {
            "value": "2",
            "label": "已审核"
        },
        {
            "value": "3",
            "label": "已结束"
        },
        {
            "value": "4",
            "label": "已取消"
        }
    ],
    "ORDER_RETURNHANDLETYPE": [
        {
            "value": "1",
            "label": "申请"
        },
        {
            "value": "2",
            "label": "拒绝"
        },
        {
            "value": "3",
            "label": "处理"
        },
        {
            "value": "4",
            "label": "处理结束"
        },
        {
            "value": "5",
            "label": "删除"
        }
    ],
    "ORDER_RETURNREASONUSAGE": [
        {
            "value": "1",
            "label": "客服取消用"
        },
        {
            "value": "2",
            "label": "客户自己取消使用"
        },
        {
            "value": "3",
            "label": "全部"
        }
    ],
    "ORDER_DELIVERYORDERTYPE": [
        {
            "value": "1",
            "label": "普通交货单(有价格)"
        },
        {
            "value": "2",
            "label": "特殊交货单(无价格)"
        },
        {
            "value": "3",
            "label": "不打印交货单"
        }
    ],
    "ORDER_DROPSHIPTYPE": [
        {
            "value": "1",
            "label": "非供应商发货"
        },
        {
            "value": "2",
            "label": "混合发货"
        },
        {
            "value": "3",
            "label": "供应商发货"
        }
    ],
    "ORDER_ORDERHEADERSTATUS": [
        {
            "value": "1",
            "label": "待审核"
        },
        {
            "value": "2",
            "label": "未处理"
        },
        {
            "value": "3",
            "label": "部分发货"
        },
        {
            "value": "4",
            "label": "已发货"
        },
        {
            "value": "5",
            "label": "已结束"
        },
        {
            "value": "6",
            "label": "已取消"
        },
        {
            "value": "7",
            "label": "已受理"
        }
    ],
    "ORDER_ORDERITEMSKUSTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "部分发货"
        },
        {
            "value": "3",
            "label": "发货"
        },
        {
            "value": "4",
            "label": "结束"
        },
        {
            "value": "5",
            "label": "取消"
        },
        {
            "value": "6",
            "label": "已受理"
        }
    ],
    "ORDER_ORDERTYPE": [
        {
            "value": "1",
            "label": "常规订单"
        },
        {
            "value": "2",
            "label": "样品订单"
        },
        {
            "value": "3",
            "label": "横持订单"
        },
        {
            "value": "4",
            "label": "转换订单"
        }
    ],
    "ORDER_STOCKALLOCATESTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "预选"
        },
        {
            "value": "3",
            "label": "发货"
        },
        {
            "value": "4",
            "label": "取消"
        }
    ],
    "ORDER_STOCKALLOCATETYPE": [
        {
            "value": "1",
            "label": "实际库存"
        },
        {
            "value": "2",
            "label": "期货库存"
        },
        {
            "value": "3",
            "label": "缺货库存"
        }
    ],
    "ORDER_TRANSFERORDERSTATUS": [
        {
            "value": "1",
            "label": "待审核"
        },
        {
            "value": "2",
            "label": "已审核"
        },
        {
            "value": "3",
            "label": "已完成"
        },
        {
            "value": "4",
            "label": "已取消"
        }
    ],
    "ORDER_TRANSFERORDERTYPE": [
        {
            "value": "1",
            "label": "正常横持"
        },
        {
            "value": "2",
            "label": "京东横持"
        }
    ],
    "ORDER_ORDERWRITEOFFSTATUS": [
        {
            "value": "1",
            "label": "待核销"
        },
        {
            "value": "2",
            "label": "已核销"
        }
    ],
    "INVOICEAPPLIES_OAINVOICETYPE": [
        {
            "value": "1",
            "label": "普票"
        },
        {
            "value": "2",
            "label": "专票"
        }
    ],
    "COSTAPPLIES_COSTTYPE": [
        {
            "value": "1",
            "label": "报销"
        },
        {
            "value": "2",
            "label": "预支"
        }
    ],
    "MARKET_BATCHASSIGNTYPE": [
        {
            "value": "1",
            "label": "按用户发放"
        },
        {
            "value": "2",
            "label": "按会员发放"
        }
    ],
    "MARKET_CONSUMERCOUPONSTATUS": [
        {
            "value": "1",
            "label": "待使用"
        },
        {
            "value": "2",
            "label": "已使用"
        },
        {
            "value": "3",
            "label": "已作废"
        },
        {
            "value": "4",
            "label": "已过期"
        }
    ],
    "MARKET_COUPONEXPIRETYPE": [
        {
            "value": "1",
            "label": "单个过期"
        },
        {
            "value": "2",
            "label": "整体过期"
        }
    ],
    "MARKET_COUPONSTATUS": [
        {
            "value": "1",
            "label": "待发放"
        },
        {
            "value": "2",
            "label": "已分配"
        },
        {
            "value": "3",
            "label": "已使用"
        },
        {
            "value": "4",
            "label": "已作废"
        },
        {
            "value": "5",
            "label": "已过期"
        }
    ],
    "MARKET_GENERATESTATUS": [
        {
            "value": "1",
            "label": "未生成"
        },
        {
            "value": "2",
            "label": "生成中"
        },
        {
            "value": "3",
            "label": "生成完成"
        }
    ],
    "MARKET_GIFTCHOOSETYPE": [
        {
            "value": "1",
            "label": "固定"
        },
        {
            "value": "2",
            "label": "可选择"
        }
    ],
    "MARKET_PROMOTIONLIMITTYPE": [
        {
            "value": "1",
            "label": "商品"
        },
        {
            "value": "2",
            "label": "商品Sku"
        },
        {
            "value": "3",
            "label": "分类"
        },
        {
            "value": "4",
            "label": "品牌"
        },
        {
            "value": "5",
            "label": "会员"
        }
    ],
    "MARKET_PROMOTIONMINUSTYPE": [
        {
            "value": "1",
            "label": "累计立减"
        },
        {
            "value": "2",
            "label": "梯度立减"
        }
    ],
    "MARKET_PROMOTIONTYPE": [
        {
            "value": "1",
            "label": "送券"
        },
        {
            "value": "2",
            "label": "打折"
        },
        {
            "value": "3",
            "label": "赠品"
        },
        {
            "value": "4",
            "label": "立减"
        },
        {
            "value": "5",
            "label": "送积分"
        }
    ],
    "MARKET_PROMOTIONUSETYPE": [
        {
            "value": "1",
            "label": "自动使用"
        },
        {
            "value": "2",
            "label": "优惠券使用"
        },
        {
            "value": "3",
            "label": "展会使用"
        }
    ],
    "MARKET_WAREHOUSETYPE": [
        {
            "value": "1",
            "label": "订单仓库"
        },
        {
            "value": "2",
            "label": "期货仓库"
        }
    ],
    "GOODS_ADJUSTITEMSTOKTYPE": [
        {
            "value": "1",
            "label": "入库"
        },
        {
            "value": "2",
            "label": "出库"
        },
        {
            "value": "3",
            "label": "库存调整"
        }
    ],
    "GOODS_BOTYPE": [
        {
            "value": "1",
            "label": "可以下单"
        },
        {
            "value": "2",
            "label": "不允许下单"
        }
    ],
    "GOODS_DISCOUNTTYPE": [
        {
            "value": "1",
            "label": "折扣"
        },
        {
            "value": "2",
            "label": "指定价格"
        }
    ],
    "GOODS_HIERARCHYBIZTYPE": [
        {
            "value": "1",
            "label": "CJKJ.Product.Goods.HierarchyBizType"
        }
    ],
    "GOODS_ITEMAUDITEDPART": [
        {
            "value": "1",
            "label": "基础信息"
        },
        {
            "value": "2",
            "label": "销售信息"
        },
        {
            "value": "3",
            "label": "产品属性"
        },
        {
            "value": "4",
            "label": "商品文本"
        },
        {
            "value": "5",
            "label": "包装信息"
        }
    ],
    "GOODS_ITEMHIERARCHYPARENTTYPE": [
        {
            "value": "0",
            "label": "内部"
        },
        {
            "value": "1",
            "label": "外部"
        }
    ],
    "GOODS_ITEMIMPORTPART": [
        {
            "value": "1",
            "label": "商品信息"
        },
        {
            "value": "2",
            "label": "装箱信息"
        },
        {
            "value": "3",
            "label": "商品转换信息"
        },
        {
            "value": "4",
            "label": "商品零件信息"
        }
    ],
    "GOODS_ITEMSALESLEVEL": [
        {
            "value": "1",
            "label": "A"
        },
        {
            "value": "2",
            "label": "B"
        },
        {
            "value": "3",
            "label": "C"
        }
    ],
    "GOODS_ITEMSALESTYPE": [
        {
            "value": "1",
            "label": "销售中"
        },
        {
            "value": "2",
            "label": "售完为止"
        },
        {
            "value": "3",
            "label": "停止销售"
        }
    ],
    "GOODS_ITEMSKUSTATUS": [
        {
            "value": "1",
            "label": "上架"
        },
        {
            "value": "2",
            "label": "下架"
        },
        {
            "value": "3",
            "label": "作废"
        }
    ],
    "GOODS_ITEMSKUSTOCKADJUSTSTATUS": [
        {
            "value": "1",
            "label": "申请中"
        },
        {
            "value": "2",
            "label": "已审核"
        }
    ],
    "GOODS_ITEMSKUSTOCKADJUSTTYPE": [
        {
            "value": "1",
            "label": "调增"
        },
        {
            "value": "2",
            "label": "调减"
        }
    ],
    "GOODS_ITEMSTATUS": [
        {
            "value": "1",
            "label": "上架"
        },
        {
            "value": "2",
            "label": "下架"
        },
        {
            "value": "3",
            "label": "编辑"
        },
        {
            "value": "4",
            "label": "作废"
        }
    ],
    "GOODS_OTHERITEMSTOCKSTATUS": [
        {
            "value": "1",
            "label": "申请"
        },
        {
            "value": "2",
            "label": "审核"
        },
        {
            "value": "3",
            "label": "取消"
        }
    ],
    "GOODS_OTHERSTOCKREASONTYPE": [
        {
            "value": "1",
            "label": "入库原因"
        },
        {
            "value": "2",
            "label": "出库原因"
        }
    ],
    "GOODS_OTHERSTOCKTYPE": [
        {
            "value": "1",
            "label": "入库"
        },
        {
            "value": "2",
            "label": "出库"
        }
    ],
    "GOODS_PURCHASETYPE": [
        {
            "value": "1",
            "label": "CB品-外部工厂"
        },
        {
            "value": "2",
            "label": "NB品"
        },
        {
            "value": "3",
            "label": "代理品"
        },
        {
            "value": "4",
            "label": "贩促品"
        },
        {
            "value": "5",
            "label": "CB品-自社工厂"
        }
    ],
    "GOODS_SAPDEPARTMENTCODE": [
        {
            "value": "1",
            "label": "EB上海：9411"
        },
        {
            "value": "2",
            "label": "ST上海营业：9413"
        },
        {
            "value": "3",
            "label": "EB上海工厂：9441"
        },
        {
            "value": "4",
            "label": "EB北京：9421"
        }
    ],
    "GOODS_SAPFACTORY": [
        {
            "value": "1",
            "label": "EB上海（9411）"
        },
        {
            "value": "2",
            "label": "桃浦仓库（H510）"
        },
        {
            "value": "3",
            "label": "直送仓库（H511）"
        },
        {
            "value": "4",
            "label": "ST上海营业（9413）"
        },
        {
            "value": "5",
            "label": "青浦仓库（H520）"
        },
        {
            "value": "6",
            "label": "直送仓库（H521）"
        },
        {
            "value": "7",
            "label": "EB北京（9421）"
        },
        {
            "value": "8",
            "label": "北京仓库（H540）"
        },
        {
            "value": "9",
            "label": "北京直送仓库（H541）"
        },
        {
            "value": "10",
            "label": "ST上海工厂（9441）"
        },
        {
            "value": "11",
            "label": "工厂直贩仓库（H530）"
        }
    ],
    "GOODS_SAPMATERIALGROUP": [
        {
            "value": "1",
            "label": "EB"
        },
        {
            "value": "2",
            "label": "ST"
        }
    ],
    "GOODS_SAPMATERIALTYPE": [
        {
            "value": "1",
            "label": "一般品：Z001"
        },
        {
            "value": "2",
            "label": "折扣品：Z002"
        }
    ],
    "GOODS_SAPPICKINGTYPE": [
        {
            "value": "1",
            "label": "小商品：01"
        },
        {
            "value": "2",
            "label": "大商品：02"
        }
    ],
    "GOODS_SAPPROFITCENTER": [
        {
            "value": "1",
            "label": "9415020000：上海EB共通（9411）"
        },
        {
            "value": "2",
            "label": "9415030000：上海ST共通（9413）"
        },
        {
            "value": "3",
            "label": "9425020000：北京EB共通（9421）"
        },
        {
            "value": "4",
            "label": "9445030000：工厂ST共通（9441）"
        }
    ],
    "GOODS_SAPPURCHASEWAREHOUSE": [
        {
            "value": "1",
            "label": "青浦仓库：H520"
        },
        {
            "value": "2",
            "label": "直送仓库：H521"
        },
        {
            "value": "3",
            "label": "工厂直贩仓库：H530 "
        }
    ],
    "GOODS_SAPTAXTYPE": [
        {
            "value": "1",
            "label": "0：免税"
        },
        {
            "value": "2",
            "label": "1：必须上税"
        }
    ],
    "GOODS_SPECVALUETYPE": [
        {
            "value": "1",
            "label": "文本"
        },
        {
            "value": "2",
            "label": "日期"
        },
        {
            "value": "3",
            "label": "月份"
        },
        {
            "value": "4",
            "label": "数值"
        },
        {
            "value": "5",
            "label": "选项"
        }
    ],
    "GOODS_SUPPLIERITEMPRICEADJUSTTYPE": [
        {
            "value": "1",
            "label": "标准价"
        },
        {
            "value": "2",
            "label": "梯度价"
        }
    ],
    "GOODS_SUPPLIERSETTLETYPE": [
        {
            "value": "1",
            "label": "货到付款"
        },
        {
            "value": "2",
            "label": "帐期"
        },
        {
            "value": "3",
            "label": "月结"
        },
        {
            "value": "4",
            "label": "款到发货"
        }
    ],
    "GOODS_SUPPLIERTYPE": [
        {
            "value": "1",
            "label": "内采"
        },
        {
            "value": "2",
            "label": "外采"
        }
    ],
    "EXHIBITION_EXHIBITIONCONSUMERPRESENT": [
        {
            "value": "1",
            "label": "在场"
        },
        {
            "value": "2",
            "label": "在线"
        },
        {
            "value": "3",
            "label": "离场"
        },
        {
            "value": "4",
            "label": "未到场"
        }
    ],
    "EXHIBITION_EXHIBITIONORDERISDELETED": [
        {
            "value": "1",
            "label": "是"
        },
        {
            "value": "2",
            "label": "否"
        }
    ],
    "EXHIBITION_EXHIBITIONORDERITEMSTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "取消"
        }
    ],
    "EXHIBITION_EXHIBITIONORDERSTATUS": [
        {
            "value": "1",
            "label": "未处理"
        },
        {
            "value": "2",
            "label": "已提交"
        },
        {
            "value": "3",
            "label": "已审核"
        },
        {
            "value": "4",
            "label": "已取消"
        },
        {
            "value": "5",
            "label": "生成订单"
        }
    ],
    "EXHIBITION_EXHIBITIONPLATFORMSTRUCT": [
        {
            "value": "1",
            "label": "分销商"
        },
        {
            "value": "2",
            "label": "得力总部"
        },
        {
            "value": "3",
            "label": "分公司"
        }
    ],
    "EXHIBITION_EXHIBITIONPOWERAPPLIEDSTATUS": [
        {
            "value": "1",
            "label": "待审核"
        },
        {
            "value": "2",
            "label": "通过"
        },
        {
            "value": "3",
            "label": "驳回"
        }
    ],
    "EXHIBITION_EXHIBITIONPROMOTIONTYPE": [
        {
            "value": "1",
            "label": "打折促销"
        },
        {
            "value": "2",
            "label": "立减促销"
        },
        {
            "value": "3",
            "label": "赠品促销"
        }
    ],
    "EXHIBITION_EXHIBITIONSTATUS": [
        {
            "value": "1",
            "label": "正在开展"
        },
        {
            "value": "2",
            "label": "未开始"
        },
        {
            "value": "3",
            "label": "已结束"
        }
    ],
    "DATATRANSFER_TRANSFERTYPE": [
        {
            "value": "1",
            "label": "数据进系统"
        },
        {
            "value": "2",
            "label": "数据出系统"
        }
    ],
    "COMMON_DECIMALDEALINGSTRUCT": [
        {
            "value": "1",
            "label": "ENUM:RoundDown"
        },
        {
            "value": "2",
            "label": "ENUM:Rounding"
        },
        {
            "value": "3",
            "label": "ENUM:RoundUp"
        }
    ],
    "COMMON_JOBSTATUS": [
        {
            "value": "0",
            "label": "CJKJ.Product.Common.JobStatus"
        },
        {
            "value": "1",
            "label": "CJKJ.Product.Common.JobStatus"
        },
        {
            "value": "2",
            "label": "CJKJ.Product.Common.JobStatus"
        },
        {
            "value": "3",
            "label": "CJKJ.Product.Common.JobStatus"
        }
    ],
    "BASESUPPORT_KEYTYPE": [
        {
            "value": "1",
            "label": "CJKJ.Product.BaseSupport.KeyType"
        },
        {
            "value": "2",
            "label": "CJKJ.Product.BaseSupport.KeyType"
        },
        {
            "value": "3",
            "label": "CJKJ.Product.BaseSupport.KeyType"
        }
    ],
    "BASESUPPORT_BATCHTASKDETAILSTATUS": [
        {
            "value": "1",
            "label": "待处理"
        },
        {
            "value": "2",
            "label": "校验中"
        },
        {
            "value": "3",
            "label": "校验失败"
        },
        {
            "value": "4",
            "label": "校验完成"
        },
        {
            "value": "5",
            "label": "处理完成"
        }
    ],
    "BASESUPPORT_BATCHTASKSTATUS": [
        {
            "value": "1",
            "label": "待处理"
        },
        {
            "value": "2",
            "label": "校验中"
        },
        {
            "value": "3",
            "label": "校验失败"
        },
        {
            "value": "4",
            "label": "校验完成"
        },
        {
            "value": "5",
            "label": "处理完成"
        }
    ],
    "BASESUPPORT_BATCHTASKTYPE": [
        {
            "value": "1",
            "label": "京东订单导入"
        }
    ],
    "BASESUPPORT_ELASTICSEARCHSINDEXTYPE": [
        {
            "value": "1",
            "label": "商品索引"
        },
        {
            "value": "2",
            "label": "商品索引"
        },
        {
            "value": "3",
            "label": "缺货报表"
        },
        {
            "value": "4",
            "label": "账款报表"
        },
        {
            "value": "5",
            "label": "展会报表"
        }
    ],
    "BASESUPPORT_MARKETCHANNELSTRUCT": [
        {
            "value": "1",
            "label": "仓储管理系统"
        },
        {
            "value": "2",
            "label": "淘宝"
        },
        {
            "value": "3",
            "label": "京东"
        },
        {
            "value": "4",
            "label": "拼多多"
        }
    ],
    "BASESUPPORT_NOTICEBIZTYPE": [
        {
            "value": "0",
            "label": "无关联订单"
        },
        {
            "value": "1",
            "label": "下单"
        },
        {
            "value": "2",
            "label": "订单审核通过"
        },
        {
            "value": "3",
            "label": "订单审核取消"
        },
        {
            "value": "4",
            "label": "订单支付成功"
        },
        {
            "value": "5",
            "label": "订单发货"
        },
        {
            "value": "6",
            "label": "订单取消"
        },
        {
            "value": "7",
            "label": "展会邀请"
        },
        {
            "value": "8",
            "label": "展会授权"
        },
        {
            "value": "9",
            "label": "订单退款"
        },
        {
            "value": "10",
            "label": "退货申请"
        }
    ],
    "BASESUPPORT_NOTICETYPE": [
        {
            "value": "1",
            "label": "下单"
        },
        {
            "value": "2",
            "label": "订单审核通过"
        },
        {
            "value": "3",
            "label": "订单审核取消"
        },
        {
            "value": "4",
            "label": "订单支付成功"
        },
        {
            "value": "5",
            "label": "订单发货"
        },
        {
            "value": "6",
            "label": "订单取消"
        },
        {
            "value": "7",
            "label": "展会邀请"
        },
        {
            "value": "8",
            "label": "展会授权"
        }
    ],
    "BASESUPPORT_PAGEAREATYPE": [
        {
            "value": "1",
            "label": "轮播"
        },
        {
            "value": "2",
            "label": "单张图片"
        },
        {
            "value": "3",
            "label": "商品列表"
        },
        {
            "value": "4",
            "label": "多标签"
        },
        {
            "value": "5",
            "label": "新闻列表"
        },
        {
            "value": "6",
            "label": "文字模块"
        },
        {
            "value": "7",
            "label": "多图平铺"
        }
    ],
    "BASESUPPORT_PRINTTEMPLATEOPTIONTYPE": [
        {
            "value": "0",
            "label": "ENUM:PrintTemplateOption_Text"
        },
        {
            "value": "1",
            "label": "ENUM:PrintTemplateOption_Image"
        },
        {
            "value": "2",
            "label": "ENUM:PrintTemplateOption_LongText"
        },
        {
            "value": "3",
            "label": "ENUM:PrintTemplateOption_Table"
        }
    ],
    "BASESUPPORT_PRINTTEMPLATETYPE": [
        {
            "value": "0",
            "label": "ENUM:PrintTemplateType_PO"
        }
    ],
    "BASESUPPORT_REASONUSAGE": [
        {
            "value": "1",
            "label": "全部"
        },
        {
            "value": "2",
            "label": "客服取消用"
        },
        {
            "value": "3",
            "label": "客户自己取消使用"
        }
    ],
    "BASESUPPORT_RECEIVERTYPE": [
        {
            "value": "1",
            "label": "公共消息"
        },
        {
            "value": "2",
            "label": "内部消息"
        }
    ],
    "BASESUPPORT_TODOSTATUS": [
        {
            "value": "0",
            "label": "CJKJ.Product.BaseSupport.TodoStatus"
        },
        {
            "value": "1",
            "label": "CJKJ.Product.BaseSupport.TodoStatus"
        },
        {
            "value": "2",
            "label": "CJKJ.Product.BaseSupport.TodoStatus"
        },
        {
            "value": "3",
            "label": "CJKJ.Product.BaseSupport.TodoStatus"
        }
    ],
    "BASESUPPORT_TODOTYPE": [
        {
            "value": "1",
            "label": "发货单同步给RSAR"
        },
        {
            "value": "2",
            "label": "退货单同步给RSAR"
        },
        {
            "value": "3",
            "label": "获取WMS库存"
        },
        {
            "value": "4",
            "label": "客户数据推送AR"
        },
        {
            "value": "5",
            "label": "Sku信息推送WMS"
        },
        {
            "value": "6",
            "label": "商品转换关系推送WMS"
        },
        {
            "value": "7",
            "label": "商品同步PM"
        },
        {
            "value": "8",
            "label": "商品同步PMStore"
        },
        {
            "value": "9",
            "label": "订单提交发送邮件"
        },
        {
            "value": "10",
            "label": "订单取消发送邮件"
        },
        {
            "value": "11",
            "label": "生成发货单发送邮件"
        },
        {
            "value": "12",
            "label": "生成备货单发送邮件"
        },
        {
            "value": "13",
            "label": "PO发送邮件"
        },
        {
            "value": "14",
            "label": "PO发送审核邮件"
        },
        {
            "value": "15",
            "label": "采购单审核完成后交期变动"
        },
        {
            "value": "16",
            "label": "商品默认交期修改"
        },
        {
            "value": "17",
            "label": "缺货提前到货发送邮件"
        },
        {
            "value": "18",
            "label": "交期变更发送邮件"
        },
        {
            "value": "19",
            "label": "PO提前结束"
        }
    ],
    "FREIGHTCHARGE_ANDORTYPE": [
        {
            "value": "1",
            "label": "与"
        },
        {
            "value": "2",
            "label": "或"
        }
    ],
    "FREIGHTCHARGE_FREESHIPPINGTYPE": [
        {
            "value": "1",
            "label": "无条件包邮"
        },
        {
            "value": "2",
            "label": "按金额"
        },
        {
            "value": "3",
            "label": "按计量单位"
        },
        {
            "value": "4",
            "label": "按计量单位和金额"
        }
    ],
    "FREIGHTCHARGE_FREIGHTCALCRULETYPE": [
        {
            "value": "1",
            "label": "重量"
        },
        {
            "value": "2",
            "label": "件数"
        },
        {
            "value": "3",
            "label": "金额"
        },
        {
            "value": "4",
            "label": "体积"
        }
    ],
    "FREIGHTCHARGE_FREIGHTCHARGERULETYPE": [
        {
            "value": "1",
            "label": "会员等级"
        },
        {
            "value": "2",
            "label": "有价格表"
        },
        {
            "value": "3",
            "label": "重量"
        },
        {
            "value": "4",
            "label": "件数"
        },
        {
            "value": "5",
            "label": "体积"
        }
    ],
    "FREIGHTCHARGE_PRODUCTSUPERPOSITIONTYPE": [
        {
            "value": "1",
            "label": "不同商品运费叠加"
        },
        {
            "value": "2",
            "label": "不同商品按总重量/件数计费"
        }
    ],
    "FREIGHTCHARGE_RULEOPERATORTYPE": [
        {
            "value": "1",
            "label": "等于"
        },
        {
            "value": "2",
            "label": "大于等于"
        },
        {
            "value": "3",
            "label": "小于等于"
        }
    ],
    "FREIGHTCHARGE_TEMPLATETYPE": [
        {
            "value": "1",
            "label": "按店铺"
        },
        {
            "value": "2",
            "label": "按商品"
        }
    ],
    "ACCOUNT_PAYTYPECLASSSTRUCT": [
        {
            "value": "1",
            "label": "补款"
        },
        {
            "value": "2",
            "label": "帐户余额"
        },
        {
            "value": "3",
            "label": "信用卡"
        },
        {
            "value": "4",
            "label": "分期付款"
        },
        {
            "value": "5",
            "label": "月结"
        },
        {
            "value": "6",
            "label": "货到付款"
        },
        {
            "value": "7",
            "label": "现金"
        },
        {
            "value": "8",
            "label": "网上支付"
        }
    ],
    "CUSTOMER_ADJUSTTYPESTRUCT": [
        {
            "value": "1",
            "label": "增加"
        },
        {
            "value": "2",
            "label": "减少"
        }
    ],
    "CUSTOMER_ACCOUNTBIZTYPE": [
        {
            "value": "1",
            "label": "手工调增"
        },
        {
            "value": "2",
            "label": "手工调减"
        },
        {
            "value": "3",
            "label": "订单奖励"
        },
        {
            "value": "4",
            "label": "订单使用"
        },
        {
            "value": "5",
            "label": "订单奖励（退）"
        },
        {
            "value": "6",
            "label": "订单使用（退）"
        },
        {
            "value": "7",
            "label": "活动奖励"
        },
        {
            "value": "8",
            "label": "活动使用"
        },
        {
            "value": "9",
            "label": "活动奖励（退）"
        },
        {
            "value": "10",
            "label": "活动使用（退）"
        },
        {
            "value": "11",
            "label": "预充值奖励"
        },
        {
            "value": "12",
            "label": "预充值奖励（退）"
        },
        {
            "value": "13",
            "label": "订单退货（退）"
        }
    ],
    "CUSTOMER_ADDRESSTYPE": [
        {
            "value": "1",
            "label": "家"
        },
        {
            "value": "2",
            "label": "公司"
        },
        {
            "value": "3",
            "label": "其他"
        }
    ],
    "CUSTOMER_AUDITSTATUS": [
        {
            "value": "1",
            "label": "待审核"
        },
        {
            "value": "2",
            "label": "审核通过"
        },
        {
            "value": "3",
            "label": "审核未通过"
        }
    ],
    "CUSTOMER_CHILDSTATUS": [
        {
            "value": "1",
            "label": "处理中"
        },
        {
            "value": "2",
            "label": "审核通过"
        },
        {
            "value": "3",
            "label": "审核未通过"
        }
    ],
    "CUSTOMER_CONSUMERACCOUNTTYPE": [
        {
            "value": "1",
            "label": "余额"
        },
        {
            "value": "2",
            "label": "积分"
        }
    ],
    "CUSTOMER_CONSUMERCREDITADJUSTTYPE": [
        {
            "value": "1",
            "label": "手工调增永久额度"
        },
        {
            "value": "2",
            "label": "手工调减永久额度"
        },
        {
            "value": "3",
            "label": "手工调增临时额度"
        },
        {
            "value": "4",
            "label": "手工调减临时额度"
        }
    ],
    "CUSTOMER_CONSUMERINVOICETYPE": [
        {
            "value": "1",
            "label": "增值税普通发票"
        },
        {
            "value": "2",
            "label": "增值税专用发票"
        }
    ],
    "CUSTOMER_CONSUMERPRICEITEMSALETYPE": [
        {
            "value": "1",
            "label": "原价立减"
        },
        {
            "value": "2",
            "label": "原价折扣"
        },
        {
            "value": "3",
            "label": "自定义价格"
        }
    ],
    "CUSTOMER_CONSUMERPRICEITEMTYPE": [
        {
            "value": "1",
            "label": "商品SPU"
        },
        {
            "value": "2",
            "label": "商品SKU"
        },
        {
            "value": "3",
            "label": "品牌"
        },
        {
            "value": "4",
            "label": "商品大分类"
        },
        {
            "value": "5",
            "label": "商品中分类"
        },
        {
            "value": "6",
            "label": "商品小分类"
        }
    ],
    "CUSTOMER_CONSUMERPRICERANGETYPE": [
        {
            "value": "1",
            "label": "客户"
        },
        {
            "value": "2",
            "label": "会员等级"
        }
    ],
    "CUSTOMER_CONSUMERPURCHASETYPE": [
        {
            "value": "1",
            "label": "批发"
        },
        {
            "value": "2",
            "label": "零售"
        }
    ],
    "CUSTOMER_CONSUMERRELATIONSHIPTYPE": [
        {
            "value": "0",
            "label": "无"
        },
        {
            "value": "1",
            "label": "子账号"
        },
        {
            "value": "2",
            "label": "父账号"
        },
        {
            "value": "3",
            "label": "双向绑定"
        }
    ],
    "CUSTOMER_CONSUMERSOURCECLIENT": [
        {
            "value": "0",
            "label": "无来源"
        },
        {
            "value": "1",
            "label": "微信小程序"
        },
        {
            "value": "2",
            "label": "支付宝小程序"
        },
        {
            "value": "3",
            "label": "Pc网页"
        },
        {
            "value": "4",
            "label": "H5网页"
        },
        {
            "value": "5",
            "label": "AndroidApp"
        },
        {
            "value": "6",
            "label": "AppleApp"
        },
        {
            "value": "7",
            "label": "国誉pos"
        }
    ],
    "CUSTOMER_CREDITAMOUNTADJUSTTYPE": [
        {
            "value": "1",
            "label": "手工调增"
        },
        {
            "value": "2",
            "label": "手工调减"
        },
        {
            "value": "3",
            "label": "启用信用额度"
        },
        {
            "value": "4",
            "label": "禁用信用额度"
        }
    ],
    "CUSTOMER_CREDITCONDITION": [
        {
            "value": "0",
            "label": "无"
        },
        {
            "value": "1",
            "label": "EOD10-15(ED11)"
        },
        {
            "value": "2",
            "label": "EOD10-15(ED14)"
        }
    ],
    "CUSTOMER_CREDITSETTLEORDERTYPE": [
        {
            "value": "1",
            "label": "退换货"
        },
        {
            "value": "2",
            "label": "折扣"
        },
        {
            "value": "3",
            "label": "当日发货"
        },
        {
            "value": "4",
            "label": "发货单（未发货）"
        }
    ],
    "CUSTOMER_CREDITUSAGE": [
        {
            "value": "1",
            "label": "采购"
        },
        {
            "value": "2",
            "label": "销售"
        },
        {
            "value": "9",
            "label": "未知"
        }
    ],
    "CUSTOMER_FAVORITEOBJECTTYPE": [
        {
            "value": "1",
            "label": "商品"
        },
        {
            "value": "2",
            "label": "文章"
        }
    ],
    "CUSTOMER_INVOICESENDTYPE": [
        {
            "value": "1",
            "label": "单独寄送"
        },
        {
            "value": "2",
            "label": "随箱配送"
        }
    ],
    "CUSTOMER_INVOICETYPE": [
        {
            "value": "1",
            "label": "增值税普通发票(电票)"
        },
        {
            "value": "2",
            "label": "增值税专业发票(电票)"
        }
    ],
    "CUSTOMER_MESSAGESTATUS": [
        {
            "value": "1",
            "label": "未读"
        },
        {
            "value": "2",
            "label": "已读"
        }
    ],
    "CUSTOMER_OVERCREDITHANDLETYPE": [
        {
            "value": "0",
            "label": "不处理"
        },
        {
            "value": "1",
            "label": "下单提示"
        },
        {
            "value": "2",
            "label": "禁止下单"
        }
    ],
    "CUSTOMER_OVERDUEOREXCESSOPERATION": [
        {
            "value": "1",
            "label": "不处理"
        },
        {
            "value": "2",
            "label": "下单提示"
        },
        {
            "value": "3",
            "label": "禁止下单"
        }
    ],
    "CUSTOMER_RECHARGEORDERSTATUS": [
        {
            "value": "1",
            "label": "待审核"
        },
        {
            "value": "2",
            "label": "已通过"
        },
        {
            "value": "3",
            "label": "已驳回"
        },
        {
            "value": "4",
            "label": "已作废"
        },
        {
            "value": "5",
            "label": "已反审核"
        }
    ],
    "CUSTOMER_SETTLETYPE": [
        {
            "value": "1",
            "label": "转账"
        },
        {
            "value": "2",
            "label": "月结"
        }
    ],
    "CUSTOMER_UNIONLOGINTYPE": [
        {
            "value": "1",
            "label": "微信小程序"
        },
        {
            "value": "2",
            "label": "平台"
        }
    ]
}

/**
 * 通用状态
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const STATUS = [{
  label: '启用', value: '1'
}, {
  label: '禁用', value: '2'
}]

/**
 * 性别
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const SEX = [{
  label: '未知', value: '0'
}, {
  label: '男性', value: '1'
}, {
  label: '女性', value: '2'
}]

/**
 * 结算方式
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const SETTLE_TYPE = [{
  label: '现结', value: '1'
}, {
  label: '月结', value: '2'
}, {
  label: '货到付款', value: '3'
}]

/**
 * 超出账期或超出信用额度处理方式
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const OVER_CREDIT_HANDLE_TYPE = [{
  label: '不处理', value: '0'
}, {
  label: '下单提示', value: '1'
}, {
  label: '禁止下单', value: '2'
}]

/**
 * 账户类型
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const ACCOUNT_TYPE = [{
  label: '余额账户', value: '1'
}, {
  label: '积分账户', value: '2'
}]

/**
 * 账户操作业务类型
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const ACCOUNT_BIZ_TYPE = [{
  label: '手工调增', value: '1'
}, {
  label: '手工调减', value: '2'
}]

/**
 * 预充值状态
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const RECHARGE_STATUS = [{
  label: '待审核', value: '1'
}, {
  label: '已通过', value: '2'
}, {
  label: '已驳回', value: '3'
}, {
  label: '已作废', value: '4'
}, {
  label: '已反审核', value: '5'
}]

/**
 * 商品缺货可购买状态
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const BO_TYPE = [{
  label: '缺货可购', value: '1'
}, {
  label: '缺货不可购', value: '2'
}]

/**
 * 展示状态
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const SHOW_TYPE = [{
  label: '是', value: '1'
}, {
  label: '否', value: '2'
}]

/**
 * 展会客户是否在场
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const EXHIBITION_CONSUMER_SITUATION = [{
  label: '在场', value: '1'
}, {
  label: '在线', value: '2'
}, {
  label: '离场', value: '3'
}, {
  label: '未到场', value: '4'
}]

/**
 * 优惠券过期类型
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const COUPON_EXPIRE_TYPE = [{
  label: '单个过期', value: '1'
}, {
  label: '整体过期', value: '2'
}]

/**
 * 优惠券生成状态
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const COUPON_GENERATE_STATUS = [{
  label: '未生成', value: '1'
}, {
  label: '生成中', value: '2'
}, {
  label: '生成完成', value: '3'
}]

/**
 * 产品属性类型
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const SPEC_TEMPLATE_VALUE_TYPE = [{
  label: '文本', value: '1'
}, {
  label: '日期', value: '2'
}, {
  label: '月份', value: '3'
}, {
  label: '数值', value: '4'
}, {
  label: '选项', value: '5'
}]

/**
 * 月份
 * @type {string[]}
 */
const MONTH = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']

/**
 * 支付状态
 * @type {{}}
 */
const PAY_STATUS = [{
  label: '已支付', value: true
}, {
  label: '未支付', value: false
}]

/**
 * 订单状态
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}, null]}
 */
const ORDER_STATUS = [{
  label: '未处理', value: '1'
}, {
  label: '待审核', value: '2'
}, {
  label: '子账户订单待审核', value: '3'
}, {
  label: '发货', value: '4'
}, {
  label: '结束', value: '5'
}, {
  label: '取消', value: '6'
}]

/**
 * 开票方式
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const INVOICE_BILLING_TYPE = [{
  label: '按明细开票', value: '1'
}, {
  label: '按分类开票', value: '2'
}]

/**
 * 通用类型
 * @type {[{label: string, value: string}, {label: string, value: string}]}
 */
const COMMON_TYPE = [{
  label: '是', value: '1'
}, {
  label: '否', value: '2'
}]

/**
 * 通用类型
 * @type {[{label: string, value: boolean}, {label: string, value: boolean}]}
 */
const COMMON_TYPE_BOOLEAN = [{
  label: '是', value: true
}, {
  label: '否', value: false
}]

/**
 * 通用类型
 * @type {[{label: string, value: string},{label: string, value: string}]}
 */
const COMMON_TYPE_BOOLEAN_STRING = [{
  label: '是', value: 'true'
}, {
  label: '否', value: 'false'
}]

/**
 * 取消原因用途
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const CANCEL_REASON_USAGE = [{
  label: '全部', value: '1'
}, {
  label: '内部', value: '2'
}, {
  label: '外部', value: '3'
}]

/**
 * 地址类型
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const ADDRESS_TYPE = [{
  label: '家', value: '1'
}, {
  label: '公司', value: '2'
}, {
  label: '其他', value: '3'
}]

/**
 * 展会订单状态
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const EXHIBITION_ORDER_STATUS = [{
  label: '未处理', value: '1'
}, {
  label: '已提交', value: '2'
}, {
  label: '已审核', value: '3'
}, {
  label: '取消', value: '4'
}, {
  label: '生成订单', value: '5'
}]

/**
 * 产品税率
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const PRODUCT_TAX_RATE = [{
  label: '0.13', value: '0.13'
}, {
  label: '0.09', value: '0.09'
}, {
  label: '0.06', value: '0.06'
}, {
  label: '0.04', value: '0.04'
}, {
  label: '0.03', value: '0.03'
}, {
  label: '0', value: '0'
}]

/**
 * 操作类型
 * @type {[{label: string, value: string}, {label: string, value: string}, {label: string, value: string}]}
 */
const CHANGE_TYPE = [{
  label: '新建', value: '0'
}, {
  label: '修改', value: '1'
}, {
  label: '删除', value: '2'
}]

export default {
  STATUS,
  SEX,
  SETTLE_TYPE,
  OVER_CREDIT_HANDLE_TYPE,
  ACCOUNT_TYPE,
  ACCOUNT_BIZ_TYPE,
  RECHARGE_STATUS,
  BO_TYPE,
  SHOW_TYPE,
  EXHIBITION_CONSUMER_SITUATION,
  COUPON_EXPIRE_TYPE,
  COUPON_GENERATE_STATUS,
  SPEC_TEMPLATE_VALUE_TYPE,
  MONTH,
  PAY_STATUS,
  ORDER_STATUS,
  INVOICE_BILLING_TYPE,
  COMMON_TYPE,
  COMMON_TYPE_BOOLEAN,
  COMMON_TYPE_BOOLEAN_STRING,
  CANCEL_REASON_USAGE,
  ADDRESS_TYPE,
  EXHIBITION_ORDER_STATUS,
  PRODUCT_TAX_RATE,
  CHANGE_TYPE,
  ...FULL_STATUS
}
