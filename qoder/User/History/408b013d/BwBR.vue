<template>
  <div class="order-detail-item-info">
    <div style="margin-left: 20px;line-height: 20px;margin-top: 10px;">客户总额度: {{ $formatter.moneyFormat(orderInfo && orderInfo.totalCreditAmount || 0) }}元</div>
    <div style="display: flex;justify-content: flex-start;flex-wrap: wrap;line-height: 20px;margin-left: 20px;margin-top: 10px;">
      <div style="margin-right: 20px;">行数: {{ $formatter.numberWithCommaFormat(orderInfo && orderInfo.totalLine || 0) }}</div>
      <div style="margin-right: 20px;">总件数: {{ $formatter.numberWithCommaFormat(orderInfo && orderInfo.totalQty || 0) }}</div>
      <div style="margin-right: 20px;">总金额：{{ $formatter.moneyFormat(orderInfo && orderInfo.totalAmount || 0) }}元</div>
      <div style="margin-right: 20px;">发货件数：{{ $formatter.numberWithCommaFormat(orderInfo && orderInfo.shippedQty || 0) }}</div>
      <div style="margin-right: 20px;">发货金额：{{ $formatter.moneyFormat(orderInfo && orderInfo.shippedTotalAmount || 0) }}元</div>
      <div style="margin-right: 20px;">缺货数量：{{ $formatter.numberWithCommaFormat(orderInfo && orderInfo.outOfStockQty || 0) }}</div>
      <div style="margin-right: 20px;">缺货金额：{{ $formatter.moneyFormat(orderInfo && orderInfo.outOfStockAmount || 0) }}元</div>
      <div style="margin-right: 20px;">期货数量：{{ $formatter.numberWithCommaFormat(orderInfo && orderInfo.futureStockQty || 0) }}</div>
      <div style="margin-right: 20px;">期货金额：{{ $formatter.moneyFormat(orderInfo && orderInfo.futureStockAmount || 0) }}元</div>
    </div>
    <table-list-card ref="dataListView"
                     table-name="order-item-info-item-list"
                     title="订单商品列表"
                     :table-data="orderItemList"
                     sortable="custom"
                     height="auto"
                     :highlight-current-row="false"
                     :columns="columns"
                     :show-setting="false"
                     :selection="isSelectionEnabled"
                     :reserve-selection="isSelectionEnabled"
                     paging
                     is-full-data-and-static-paging
                     :page-size="200"
                     :page-sizes="[50, 100, 200]"
                     :cell-class-name="tableCellClassName"
                     :row-selectable="rowSelectable"
                     @tableDataChange="tableDataChange"
                     @selectChange="getSelectChangeData">
      <template v-if="orderInfo && orderInfo.id" slot="button">
        <el-checkbox v-model="isFutureStockOnly" style="color: white;margin-right: 10px;">仅看期货</el-checkbox>
        <el-checkbox v-model="isOutOfStockOnly" style="color: white;margin-right: 10px;">仅看缺货</el-checkbox>
        <el-button v-if="!isViewMode"
                   type="mini"
                   :loading="saveItemLoading"
                   @click="handleSaveOrderItem">
          保存商品行
        </el-button>
        <el-button v-if="!isViewMode && shouldShowRefreshPriceButton"
                   type="mini"
                   :loading="refreshPriceLoading"
                   @click="handleRefreshPrice">
          刷新价格
        </el-button>
        <el-button v-if="!isViewMode"
                   type="mini"
                   @click="handleBatchCancelLine">
          批量取消
        </el-button>
        <el-button type="mini" @click="handleOrderStockAllocate">
          库存分配记录
        </el-button>
      </template>
      <template v-if="!isViewMode">
        <el-button v-if="
        $cp('Order.OrderHeader.Allocate') &&
        (orderInfo && (orderInfo.status < 4 || orderInfo.status === 7))"
                  slot="button"
                  type="mini"
                  :loading="allocateLoading"
                  @click="handleBackOrderAllocate">
                  分配库存
                </el-button>
        <el-button v-if="
        $cp('Order.OrderHeader.Update') &&
        (orderInfo && (orderInfo.status < 4 || orderInfo.status === 7))"
                  slot="button"
                  type="mini"
                  :loading="deallocateLoading"
                  @click="handleBackOrderDeallocate">
                  释放
                </el-button>
        <el-button v-if="
            (!orderInfo || orderInfo.status < 4 || orderInfo.status === 7)
            &&
            $cp('Order.OrderHeader.Update')
          "
                  slot="button"
                  type="mini"
                  @click="handleAddItem">
          添加商品
        </el-button>
        <el-button v-if="
            (!orderInfo || orderInfo.status < 4 || orderInfo.status === 7)
            &&
            $cp('Order.OrderHeader.Update')
          "
                  slot="button"
                  type="mini">
          <div v-if="!consumerId && !(orderInfo && orderInfo.consumerId)" @click="checkIsSelectedConsumer">导入</div>
          <el-upload v-else
                    :action="importUrl"
                    :name="'file'"
                    :headers="$headers"
                    :show-file-list="false"
                    style="display: inline"
                    :on-success="(response, file, fileList) => importSuccess && importSuccess(response, file, fileList)"
                    :on-error="(err, file, fileList) => importError && importError(err, file, fileList)"
                    :before-upload="(file)=>beforeUpload && beforeUpload(file)"
                    :limit="99"
                    class="menu-uploader">
            <div>
              <span>导入</span>
            </div>
          </el-upload>
        </el-button>
        <el-button v-if="
            (!orderInfo || orderInfo.status < 4 || orderInfo.status === 7)
            // &&
            // $cp('Order.OrderHeader.Update')
          "
                  slot="button"
                  type="mini"
        >
          <a :href="$getTemaplteFileUrl('/OrderItemImportTemplate.xlsx')"
            target="_blank">下载导入模板</a>
        </el-button>
      </template>
    </table-list-card>

    <select-item-sku-dialog ref="selectItemSkuDialog"
                            :is-package-ship="isPackageShip"
                            @save-success="handleSelectItemSku"></select-item-sku-dialog>
    <cancel-line-dialog ref="cancelLineDialog"
                        @save-success="handleCancelLineSuccess"></cancel-line-dialog>
    <order-stock-allocate-history ref="orderStockAllocateHistory"></order-stock-allocate-history>
    <packing-time-dialog ref="packingTimeDialog"></packing-time-dialog>
  </div>
</template>

<script>
import {
  // getConsumerAddressList,
  // getConsumerInvoiceList
} from '@/api/gens-api/crm'

// import { getOrderSource } from '@/api/gens-api/base-support'
// import { createOrderHeaderBackOrderAllocate, createOrderHeaderOrderItemSku } from '@/api/gens-api/order'
import {
  createOrderHeaderAllocate,
  createOrderHeaderDeallocate,
  createOrderHeaderRefreshPriceByOrderId
  // createOrderHeaderOrderItemSku
} from '@/api/gens-api/order'
import SelectItemSkuDialog from './SelectItemSkuDialog'
import CancelLineDialog from './CancelLineDialog'
import OrderStockAllocateHistory from '@/views/order/components/OrderStockAllocateHistory'
import PackingTimeDialog from './PackingTimeDialog'
export default {
  name: 'OrderItemInfo',
  components: { OrderStockAllocateHistory, SelectItemSkuDialog, CancelLineDialog, PackingTimeDialog },
  props: {
    orderInfo: {
      type: [Object, null],
      default: null
    },
    consumerId: {
      type: String,
      default: ''
    },
    isPackageShip: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isNeedInvoice: true,
      addressPopVisible: false,
      invoicePopVisible: false,
      searchLoading: false,
      isShowBackOrder: false,
      selectChangeData: [],
      orderItemList: [], // 当前显示在表格中的数据（可能是部分数据或全部数据）
      fullOrderItemList: [], // 存储完整的订单商品数据（用于分批加载策略）
      consumerList: [],
      addressList: [],
      invoiceList: [],
      isOutOfStockOnly: false,
      isFutureStockOnly: false,
      isLoadingMoreItems: false, // 是否正在加载更多数据的标记
      batchSize: 20, // 每批加载的数据量，首屏显示的数据条数，可根据实际情况调整
      loadingTimeout: null, // 用于存储加载超时ID
      refreshPriceLoading: false, // 刷新价格按钮的加载状态
      saveItemLoading: false, // 保存商品行按钮的加载状态
      allocateLoading: false, // 库存分配操作的加载状态
      deallocateLoading: false // 释放操作的加载状态
    }
  },
  computed: {
    importUrl() {
      return `${process.env[`VUE_APP_EXHIBITION_API`]}/api/order/order-header/import-order-item-sku/${this.consumerId}`
    },
    columns() {
      return [
        // {
        //   label: '图片',
        //   prop: 'picUrl',
        //   width: 70,
        //   type: 'image-view',
        //   align: 'left'
        // },
        { label: '', prop: 'itemSkuId', width: 120, show: false },
        { label: 'SKU编号', prop: 'itemSkuNo', width: 80 },
        { label: 'SKU名称', prop: 'itemSkuName', minWidth: 150 },
        {
          label: '订单数量', prop: 'qty', width: 50, align: 'right', type: 'input',
          disabled: (row) => ![0, 1].includes(row.stockStatus),
          on: {
            input: (item, data) => {
              // 只允许输入大于0且不超过10位的整数
              const value = parseInt(item, 10)
              if (isNaN(value) || value <= 0) {
                this.$set(data, 'qty', data.qty || 1) // 如果输入无效，恢复原值或设为1
              } else if (value > 999999999) {
                this.$set(data, 'qty', 999999999) // 如果超过9位，自动设为最大值
              } else {
                this.$set(data, 'qty', value)
                // 更新小计金额
                if (data.itemUnitPrice) {
                  this.$set(data, 'itemAmount', Number(data.itemUnitPrice * data.qty).toFixed(2))
                }
              }
            }
          }
        },
        { label: '占用数量', prop: 'allocateQty', width: 50, align: 'right',
          formatter: (item, row) => {
            // 部分发货 发货 结束
            if ([2, 3, 4].includes(row.status)){
              return row.allocateQty - row.shippedQty
            } else {
              return row.allocateQty
            }
          }
        },
        { label: '期货数量', prop: 'futureQty', width: 50, align: 'right' },
        { label: '缺货数量', prop: 'outOfStockQty', width: 50, align: 'right' },
        // { label: '条码', prop: 'barCode', minWidth: 100 },
        // { label: '型号', prop: 'model', minWidth: 100 },
        // { label: '赠品', prop: 'isGiftText', width: 20 },
        // { label: '规格', prop: 'specification', minWidth: 100 },
        // { label: '型号', prop: 'model', minWidth: 100 },
        // { label: '计量单位', prop: 'unitName', width: 100, align: 'center' },
        // {
        //   label: '预选数量', prop: 'pickedQty', width: 50, align: 'right'
        // },
        {
          label: '已发数量', prop: 'shippedQty', width: 50, align: 'right', show: () => !!this.orderInfo
          // ,
          // type: 'tooltip',
          // content: (row) => {
          //   return row.content || ''
          // }
        },
        // {
        //   label: '未发数量', prop: 'unShipQty', width: 50, align: 'right', show: () => !!this.orderInfo
        //
        // },
        // {
        //   label: '本次发货数量', prop: 'shipQty', width: 50, align: 'right', type: 'text', show: () => !!this.orderInfo
        //   // , disabled: (item) => !item.unShipQty,
        //   // on: {
        //   //   input: (item, data) => {
        //   //     if (item > data.unShipQty) {
        //   //       data.shipQty = data.unShipQty
        //   //     }
        //   //   }
        //   // }
        // },
        {
          label: '单价', prop: 'itemUnitPrice', width: 50, align: 'right', type: 'input',
          disabled: () => !this.$cp('Order.OrderHeader.ManualPriceAdjustment') || !!this.orderInfo,
          // prepend: {
          //   is: 'item-price-history',
          //   props: (data) => {
          //     return {
          //       itemSkuId: data.itemSkuId,
          //       consumerId: (this.orderInfo && this.orderInfo.consumerId) || (this.consumerId ? this.consumerId : '')
          //     }
          //   }
          // },
          on: {
            input: (item, data) => {
              const index = item.indexOf('.')
              data.itemUnitPrice = index !== -1 ? item.slice(0, index+3) : item
              data.itemAmount = Number(data.itemUnitPrice * data.qty).toFixed(2)
              // data.totalAmount = Number(data.itemUnitPrice * data.qty - data.discountAmount).toFixed(2)
            }
          }
        },
        { label: '嘉定仓库', prop: 'qtyAvailableST', width: 100, align: 'right',
          formatter: (item, row) => `${row.qtyAvailableST} (在途: ${row.qtyFromTransferST})`
        },
        // { label: '华南仓库', prop: 'qtyAvailableHN', width: 100, align: 'right',
        //   formatter: (item, row) => `${row.qtyAvailableHN} (在途: ${row.qtyFromTransferHN})`
        //   // ,
        //   // type: 'tooltip',
        //   // content: (row) => `<div>在途: ${row.qtyFromTransferHN}</div>`
        // },
        { label: '昆山仓库', prop: 'qtyAvailableMI', width: 100, align: 'right',
          formatter: (item, row) => `${row.qtyAvailableMI} (在途: ${row.qtyFromTransferMI})`
        },
        { label: '天猫仓库', prop: 'qtyAvailableTM', width: 100, align: 'right',
          formatter: (item, row) => `${row.qtyAvailableTM} (在途: ${row.qtyFromTransferTM})`
        },
        { label: '京东仓库', prop: 'qtyAvailableJD', width: 100, align: 'right',
          formatter: (item, row) => `${row.qtyAvailableJD} (在途: ${row.qtyFromTransferJD})`
        },
        { label: '小计', prop: 'itemAmount', width: 80, align: 'right', formatter: 'money' },
        // {
        //   label: '折扣金额',
        //   prop: 'discountAmount',
        //   width: 100,
        //   align: 'right',
        //   formatter: 'money'
        // },
        // { label: '净金额', prop: 'totalAmount', width: 100, align: 'right', formatter: 'money' },
        { label: '库存分配', prop: 'stockStatusText', width: 50, align: 'center' },
        { label: '状态', prop: 'statusText', width: 50, align: 'center' },
        {
          width: 100,
          label: '操作',
          prop: 'action',
          type: 'button',
          fixed: 'right',
          buttons: [
            {
              id: 'cancel',
              text: '取消',
              eventType: 'danger',
              show: row => !this.isViewMode && (!row.id || row.isCanCancel),
              click: (row, scope) => {
                if (row.id) {
                  this.$refs.cancelLineDialog.open({
                    ...row,
                    orderInfo: this.orderInfo
                  })
                } else {
                  this.orderItemList.splice(scope.$index, 1)
                  this.$nextTick(this.$refs.dataListView.query)
                }
              }
              // ,
              // policy: 'Order.OrderHeader.Update'
            },
            {
              id: 'packingTime',
              text: '履历',
              eventType: 'primary',
              show: row => row.id && row.packingTimeDate && row.packingTimeDate.length > 0,
              click: (row) => {
                this.openPackingTimeDialog(row)
              }
            }
          ]
        }
      ]
    },
    // 判断当前模式是否为查看模式
    isViewMode() {
      return !!this.$route.query.view // 判断是否为查看模式
    },
    // 4 已发货 或 6 已取消 时，返回 false，禁用多选功能
    isSelectionEnabled() {
      return ![4, 6].includes(this.orderInfo?.status)
    },

    // 判断是否显示刷新价格按钮
    // 当单据状态是"待审核"(1)和"未处理"(2)的状态，显示此按钮，其余状态不显示
    shouldShowRefreshPriceButton() {
      return this.orderInfo && [1, 2].includes(this.orderInfo.status)
    },
    // 判断是否显示批量取消按钮
    // 当有选中的数据且选中的数据中有可以取消的订单行时显示
    shouldShowBatchCancelButton() {
      return this.selectChangeData && this.selectChangeData.length > 0 &&
             this.selectChangeData.some(row => !row.id || row.isCanCancel)
    }
  },
  watch: {
    isOutOfStockOnly() {
      this.$emit('filter-change', {
        isOutOfStockOnly: this.isOutOfStockOnly,
        isFutureStockOnly: this.isFutureStockOnly
      })
    },
    isFutureStockOnly() {
      this.$emit('filter-change', {
        isOutOfStockOnly: this.isOutOfStockOnly,
        isFutureStockOnly: this.isFutureStockOnly
      })
    },
    orderInfo: {
      handler(val, oldVal) {
        if (val) {
          const backOrderLine = val.orderItemSkus.filter((x) => {
            return x.stockStatus === 1
          })
          this.isShowBackOrder = backOrderLine.length > 0
          this.setFormValues(val)
        }
      },
      deep: true, // 添加深度监听
      immediate: true // 立即执行一次
    },
    // 监听 isPackageShip 的变化，确保子组件能够实时更新
    isPackageShip: {
      handler(newVal) {
        // 如果 SelectItemSkuDialog 组件已经存在，直接更新其内部状态
        if (this.$refs.selectItemSkuDialog) {
          this.$refs.selectItemSkuDialog.currentIsPackageShip = newVal
        }
      },
      immediate: true
    }
  },
  mounted() {
    this.queryOrderSourceList()
  },
  methods: {
    tableCellClassName({ row, column }) {
      if (row.stockStatus === 3 && column.property === 'itemSkuName') {
        return 'status3'
      }
      if (row.stockStatus === 4 && column.property === 'itemSkuName') {
        return 'status4'
      }
      return ''
    },
    getTableData(){
      return this.orderItemList
    },
    rowSelectable(row, index) {
      // 如果操作栏的取消按钮不显示，那这个表格的勾选项也是置灰不能选择
      if (!row.id || row.isCanCancel) {
        return true
      }
      return false
    },
    getSelectChangeData(data){
      data = data.map(j => ({
        ...j
        // ,
        // shipQty: j.shipQty || j.unShipQty
      }))
      this.selectChangeData = data
      this.getSubmitData()
    },
    tableDataChange(data){
      // 使用索引和 $set 来确保响应式更新
      for (let index = 0; index < this.orderItemList.length; index++) {
        const i = this.orderItemList[index]
        // 优先使用id匹配，如果id不存在则使用lineNumber匹配
        const item = (data || []).find(s => (i.id && s.id === i.id) || (i.lineNumber && s.lineNumber === i.lineNumber))
        if (item) {
          // 使用 $set 更新数组中的对象
          this.$set(this.orderItemList, index, { ...i, ...item })
        }
      }
      this.getSubmitData()
    },
    handleOrderStockAllocate(){
      this.$refs.orderStockAllocateHistory.open(this.orderInfo.id)
    },
    // 打开分配履历对话框
    openPackingTimeDialog(row) {
      this.$refs.packingTimeDialog.open(row.packingTimeDate, row.itemSkuName)
    },
    // 处理保存商品行按钮点击事件
    handleSaveOrderItem() {
      this.saveItemLoading = true
      // 通知父组件保存商品行开始
      this.$emit('save-item-loading-change', true)
      // 通知父组件执行保存商品行操作，传递回调函数
      this.$emit('save-order-item', {
        onSuccess: () => {
          this.saveItemLoading = false
          this.$emit('save-item-loading-change', false)
        },
        onError: () => {
          this.saveItemLoading = false
          this.$emit('save-item-loading-change', false)
        }
      })
    },
    // 处理刷新价格按钮点击事件
    handleRefreshPrice() {
      if (!this.orderInfo || !this.orderInfo.id) {
        this.$message.error('订单信息不存在')
        return
      }

      this.refreshPriceLoading = true
      createOrderHeaderRefreshPriceByOrderId({
        orderId: this.orderInfo.id
      }).then(res => {
        this.$showOperationSuccessfulNotify('价格刷新成功')
        // 刷新页面数据
        this.$emit('refresh-order-data')
      }).catch(error => {
        console.error('刷新价格失败:', error)
      }).finally(() => {
        this.refreshPriceLoading = false
      })
    },
    getSubmitData(){
      this.submitData = this.selectChangeData
      // this.submitData = []
      // this.selectChangeData.forEach(i => {
      //   this.orderItemList.forEach(j => {
      //     if (i.id === j.id) {
      //       if (!j.shipQty) {
      //         this.$set(j, 'shipQty', j.unShipQty)
      //       }
      //       this.submitData.push(j)
      //     }
      //   })
      // })
      this.$emit('items-data-change', this.submitData)
    },
    // clearUserInfo() {
    //   this.$refs.form2.reset()
    //   this.$refs.form3.reset()
    // },
    onBaseSelectChange(key, val) {
      if (key === 'isNeedInvoice') {
        this.isNeedInvoice = Number(val) === 1
      }
    },
    queryOrderSourceList() {
      // getOrderSource({
      //   limit: 999,
      //   page: 1,
      //   forOrderUse: true,
      //   status: 1
      // }).then((res) => {
      //   const list = (res.items || []).map((i) => ({
      //     value: i.id,
      //     label: i.sourceName
      //   }))
      //   this.$refs.form1 &&
      //   this.$refs.form1.setDataSource('orderSourceId', list)
      //   if (!this.orderInfo && list.length) {
      //     this.$nextTick(() => {
      //       this.$refs.form1.setFormValue('orderSourceId', list[0].value)
      //     })
      //   }
      // })
    },
    // async queryAddressList(consumerId, setDefault = true) {
    //   getConsumerAddressList({
    //     consumerId
    //   }).then((res) => {
    //     this.addressList = res.items || []
    //     if (!setDefault) {
    //       return
    //     }
    //     if (this.addressList.length === 1) {
    //       this.setDefaultAddressInfo(this.addressList[0])
    //     } else if (this.addressList.length) {
    //       const address =
    //         this.addressList.find((i) => i.isDefault === 1) ||
    //         this.addressList[0]
    //       this.setDefaultAddressInfo(address)
    //     }
    //   })
    // },
    // setDefaultAddressInfo(row) {
    //   this.$refs.form2.setFormValues({
    //     receiverName: row.receiverName,
    //     mobileNumber: row.phone,
    //     region: {
    //       ids: row.districtId
    //         ? [row.provinceId, row.cityId, row.districtId]
    //         : []
    //     },
    //     addressInfo: row.address
    //   })
    // },
    // async queryInvoiceList(consumerId, setDefault = true) {
    //   getConsumerInvoiceList({
    //     consumerId
    //   }).then((res) => {
    //     this.invoiceList = res.items || []
    //     this.$nextTick(
    //       this.$refs.invoiceListView && this.$refs.invoiceListView.query
    //     )
    //     if (!setDefault) {
    //       return
    //     }
    //     if (this.invoiceList.length === 1) {
    //       this.setDefaultInvoiceInfo(this.invoiceList[0])
    //     } else if (this.invoiceList.length) {
    //       const invoice =
    //         this.invoiceList.find((i) => i.isDefault) ||
    //         this.invoiceList[0]
    //       this.setDefaultInvoiceInfo(invoice)
    //     }
    //   })
    // },
    // setDefaultInvoiceInfo(row) {
    //   this.$refs.form3 &&
    //   this.$refs.form3.setFormValues({
    //     invoiceTitle: row.companyName,
    //     taxNo: row.taxNo,
    //     bankName: row.bankName,
    //     bankAccount: row.bankAccountNo,
    //     phoneNumber: row.phone,
    //     address: row.address
    //   })
    // },
    setFormValues(data) {
      // this.isNeedInvoice = Number(data.isNeedInvoice) === 1
      // data.auditedTime = (data.auditedTime || '').startsWith('202')
      //   ? data.auditedTime
      //   : '未审核'
      // data.payStatus = data.payStatus || '未支付'
      // data.region = {
      //   ids: [data.provinceId, data.cityId, data.districtId]
      // }
      // const datas = []
      // for (let i = 0, l = data.orderItemSkus.length; i < l; i++) {
      //   const orderItemSku = data.orderItemSkus[i]
      //   let unShipQty = orderItemSku.qty
      //   if (orderItemSku.status === 5) {
      //     unShipQty = 0
      //   }
      //   datas.push({ ...orderItemSku, shipQty: orderItemSku.unShipQty })
      // }
      // ===== 【性能优化方案】：分批加载数据 =====
      // 这是一个优化大数据量加载的方案，主要思路是：
      // 1. 先加载少量数据（如前20条），保证首屏快速显示
      // 2. 然后延迟加载剩余数据，避免一次性加载大量数据导致界面卡顿
      // 3. 整个过程对用户透明，体验流畅

      // 第1步：获取完整的订单商品数据
      const fullOrderItemList = (data && data.orderItemSkus || []).map(i => ({
        ...i
        // ,
        // shipQty: i.unShipQty || 0
      }))

      // 第2步：将完整数据存储到缓存中，供后续使用
      this.fullOrderItemList = fullOrderItemList

      // 第3步：设置加载状态标记，避免重复加载
      this.isLoadingMoreItems = true

      // 第4步：先只加载前batchSize条数据（默认50条），确保第一屏能够快速显示
      // 这是性能优化的关键步骤，当数据量大时，只渲染部分数据可以显著提高首屏加载速度
      this.orderItemList = fullOrderItemList.slice(0, this.batchSize)

      this.$nextTick(() => {
        // 第5步：先让表格渲染第一批数据
        // 这样用户可以立即看到内容，提升用户体验
        this.$refs.dataListView.query()

        // 第6步：使用setTimeout延迟加载剩余数据，避免阻塞UI线程
        // 延迟执行可以让浏览器先完成首屏渲染，再处理剩余数据
        setTimeout(() => {
          // 第7步：加载完整数据到表格中
          // 此时用户已经可以看到并操作前batchSize条数据，不会感觉到页面卡顿
          this.orderItemList = fullOrderItemList

          // 第8步：重置加载状态标记
          this.isLoadingMoreItems = false

          // 第9步：通知表格组件更新视图，显示完整数据
          this.$nextTick(() => {
            this.$refs.dataListView.query()
          })
        }, 300) // 延迟300毫秒加载剩余数据，这个时间可以根据实际情况调整
      })
    },
    async checkIsSelectedConsumer() {
      if (!this.consumerId && !(this.orderInfo?.consumerId)) {
        this.$notify({
          title: '提示',
          message: '请先选择客户',
          type: 'info',
          duration: 3000
        })
        return false
      }
      return this.consumerId || this.orderInfo?.consumerId || ''
    },
    async handleAddItem() {
      const consumerId = await this.checkIsSelectedConsumer()
      if (consumerId) {
        this.$refs.selectItemSkuDialog.open({
          consumerId,
          exhibitionId: null,
          isPackageShip: this.isPackageShip
        })
      }
    },
    // 处理导入商品数据的方法，同样使用分批加载策略
    handleExportItem(response) {
      // 处理导入的数据，设置必要的属性
      const list = (response || []).map(i => ({
        ...i,
        itemUnitPrice: i.salePrice,
        // unShipQty: i.qty,
        // shipQty: i.qty,
        shippedQty: 0,
        pickedQty: 0
      }))

      // 筛选出新导入的商品（避免重复添加）
      const newItems = []
      list.forEach(i => {
        if (!(this.fullOrderItemList.some(j => j.itemSkuId === i.itemSkuId))) {
          newItems.push(i)
        }
      })

      // 将新导入的商品添加到完整数据列表的开头
      this.fullOrderItemList = [...newItems, ...this.fullOrderItemList]

      // ===== 以下是分批加载策略，与setFormValues方法相同 =====

      // 设置加载状态标记
      this.isLoadingMoreItems = true

      // 先只加载前batchSize条数据，确保第一屏快速显示
      this.orderItemList = this.fullOrderItemList.slice(0, this.batchSize)

      this.$nextTick(() => {
        // 先让表格渲染第一批数据
        this.$refs.dataListView.query()

        // 使用setTimeout延迟加载剩余数据，避免阻塞UI
        setTimeout(() => {
          // 加载完整数据到表格中
          this.orderItemList = this.fullOrderItemList

          // 重置加载状态标记
          this.isLoadingMoreItems = false

          // 通知表格组件更新视图
          this.$nextTick(() => {
            this.$refs.dataListView.query()
          })
        }, 300) // 延迟300毫秒加载剩余数据
      })
      // createOrderHeaderOrderItemSku({
      //   consumerId: this.consumerId,
      //   orderItemSkus: list.map(i => ({
      //     itemSkuId: i.id,
      //     qty: i.orderQty
      //   }))
      // }).then(res => {
      //   this.orderItemList = this.orderItemList.concat(res)
      //   this.$nextTick(() => {
      //     this.$refs.dataListView.query()
      //   })
      // }).finally(() => {
      //   this.saveLoading = false
      //   this.dialogVisible = false
      // })
      // Promise.all(list.map(i => {
      //   return createOrderHeaderOrderItemSku({
      //     consumerId: this.consumerId || this.orderInfo?.consumerId,
      //     itemSkuId: i.id,
      //     qty: i.orderQty
      //   })
      // })).then(res => {
      //   const saveList = res.map(i => {
      //     const sku = list.find(s => s.id === i.itemSkuId)
      //     return {
      //       ...sku,
      //       ...i,
      //       stockStatusText: i.stockStatusTest
      //     }
      //   })
      //   this.orderItemList = this.orderItemList.concat(saveList)
      //   this.$nextTick(this.$refs.dataListView.query)
      // })
    },
    async beforeUpload() {
      this.uploading = true
      return await this.checkIsSelectedConsumer()
    },
    importSuccess(response, file, fileList) {
      this.$message.success('导入成功')
      this.uploading = false
      this.handleExportItem(response)
    },
    importError(response, file, fileList) {
      this.uploading = false
      this.fileList = []
      this.$message.error((JSON.parse(response.message)).error.message)
    },
    handleBackOrderAllocate() {
      if (!this.selectChangeData.length) {
        this.$message.error('请选择要分配库存的商品')
        return
      }
      if (this.selectChangeData.some(i => !i.id)) {
        this.$message.error('请先保存商品信息')
        return
      }
      this.allocateLoading = true
      createOrderHeaderAllocate({
        orderId: this.orderInfo.id,
        orderItemSkuIds: this.selectChangeData.map(i => i.id)
      }).then(res => {
        this.$showOperationSuccessfulNotify()
        this.$emit('allocate-success')
      }).finally(() => {
        this.allocateLoading = false
      })
    },
    handleBackOrderDeallocate() {
      if (!this.selectChangeData.length) {
        this.$message.error('请选择要释放的商品')
        return
      }
      this.deallocateLoading = true
      createOrderHeaderDeallocate({
        orderId: this.orderInfo.id,
        orderItemSkuIds: this.selectChangeData.map(i => i.id)
      }).then(res => {
        this.$showOperationSuccessfulNotify()
        this.$emit('deallocate-success')
      }).finally(() => {
        this.deallocateLoading = false
      })
    },
    // 处理选择商品后的数据加载，同样使用分批加载策略
    handleSelectItemSku(list) {
      // 将新选择的商品添加到完整数据列表的开头
      this.fullOrderItemList = list.concat(this.fullOrderItemList)

      // ===== 以下是分批加载策略，与setFormValues方法相同 =====

      // 设置加载状态标记
      this.isLoadingMoreItems = true

      // 先只加载前batchSize条数据，确保第一屏快速显示
      // 这样用户可以立即看到新添加的商品
      this.orderItemList = this.fullOrderItemList.slice(0, this.batchSize)

      this.$nextTick(() => {
        // 先让表格渲染第一批数据
        this.$refs.dataListView.query()

        // 使用setTimeout延迟加载剩余数据，避免阻塞UI
        setTimeout(() => {
          // 加载完整数据到表格中
          this.orderItemList = this.fullOrderItemList

          // 重置加载状态标记
          this.isLoadingMoreItems = false

          // 通知表格组件更新视图
          this.$nextTick(() => {
            this.$refs.dataListView.query()
          })
        }, 300) // 延迟300毫秒加载剩余数据
      })

      // 触发订单金额更新事件
      this.$emit('get-order-amount', this.orderInfo.totalAmount || 0)
    },
    handleCancelLineSuccess() {
      this.$emit('cancel-line-success')
    },
    // 处理批量取消订单行
    handleBatchCancelLine() {
      if (!this.selectChangeData || this.selectChangeData.length === 0) {
        this.$message.error('请选择要取消的订单行')
        return
      }

      // 过滤出可以取消的订单行
      const cancelableItems = this.selectChangeData.filter(row => !row.id || row.isCanCancel)

      if (cancelableItems.length === 0) {
        this.$message.error('所选订单行均不可取消')
        return
      }

      // 为每个订单行添加 orderInfo 信息
      const batchData = cancelableItems.map(item => ({
        ...item,
        orderInfo: this.orderInfo
      }))

      // 打开批量取消弹窗
      this.$refs.cancelLineDialog.open(batchData)
    },
    handleCancelLine(row, button, closeConfirm) {
      const index = this.orderItemList.findIndex(
        (i) => i.itemSkuId === row.itemSkuId
      )
      this.orderItemList.splice(index, 1)
      this.$nextTick(() => {
        this.$refs.dataListView.query()
      })
      closeConfirm()
    }
  }
}
</script>
