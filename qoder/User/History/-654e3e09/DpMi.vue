<template>
  <div class="app-container app-container-scroll">
    <menubar :left-buttons="leftButtons" :right-buttons="rightButtons" fixed @menu-button-click="handleButtonClick">
    </menubar>
    <!-- <menubar :left-buttons="[
        (!orderInfo || orderInfo.status === 1 || orderInfo.status === 2) && {...$menuButton.save
        ,policy:id ?'Order.OrderHeader.Update':'Order.OrderHeader.Create',loading: saveLoading
        },
        orderInfo && (orderInfo.status === 1 ) && {...$menuButton.audit
        ,policy:'Order.OrderHeader.Audit'
        },
        // orderInfo && (orderInfo.status === 2 ) && {...$menuButton.unaudit
        // // ,policy:'Order.OrderHeader.UnAudit'
        // },
        // orderInfo && $menuButton.custom({code:'print1',text:'打印销售单'
        // // ,policy:'Order.OrderHeader.Print'
        // }),
        // orderInfo && $menuButton.custom({code:'print2',text:'打印出库单'
        // // ,policy:'Order.OrderHeader.Print'
        // }),
        // orderInfo && (orderInfo.status === 2 ) && {...$menuButton.createPackingSlip
        // ,policy:'Order.OrderHeader.PackingSlip'
        // },
       orderInfo && {code:'export',text:'订单明细导出'
       ,policy:'Order.OrderHeader.OrderItemSkuExport'
       }
      ]" :right-buttons="[
        orderInfo && (orderInfo.status === 6 ) && {...$menuButton.delete
        ,policy:'Order.OrderHeader.Delete'
        },
        orderInfo && orderInfo.isCanCancel && {...$menuButton.cancel
        ,policy:'Order.OrderHeader.Cancel'
        },
        orderInfo && $menuButton.custom({code:'history',text:'取消记录', policy:'Order.OrderHeader.CancelOrderPay'}),
        orderInfo && {
          code: 'orderHandleInfo', text: '订单处理信息'
        }
      ]" fixed @menu-button-click="handleButtonClick">
    </menubar> -->
    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane v-loading="loading" label="基本信息" name="baseInfo">
        <order-base-info ref="baseInfo" :order-info="orderInfo" @get-consumer-id="getConsumerId"
          @get-is-package-ship="getIsPackageShip" @over-credit-type="getOverCreditType"></order-base-info>
      </el-tab-pane>
      <el-tab-pane v-loading="tabLoading.orderItemInfo" label="商品信息" name="orderItemInfo" lazy>
        <keep-alive>
          <order-item-info v-if="isOrderItemInfoRendered" ref="orderItemInfo"
            :order-info="orderInfo" :consumer-id="consumerId" :is-package-ship="isPackageShip"
            @cancel-line-success="getOrderInfo" @items-data-change="getPackSlitData" @allocate-success="getOrderInfo"
            @deallocate-success="getOrderInfo" @get-order-amount="getOrderTotalAmount"
            @filter-change="onFilterChange" @refresh-order-data="getOrderInfo" @save-order-item="saveOrderItem"
            @save-item-loading-change="handleSaveItemLoadingChange"></order-item-info>
        </keep-alive>
      </el-tab-pane>
      <el-tab-pane v-if="id" v-loading="loading" label="支付信息" name="paymentInfo">
        <payment-info :order-info="orderInfo" :settle-type="settleType" @pay-success="getOrderInfo"
          @cancel-pay-success="getOrderInfo"></payment-info>
      </el-tab-pane>
      <!--      <el-tab-pane v-if="promotions.length" v-loading="loading" label="促销活动">-->
      <!--        <order-promotion :promotions="promotions"></order-promotion>-->
      <!--      </el-tab-pane>-->
      <el-tab-pane v-if="id && packSlitTableData.length" v-loading="loading" label="发货单" name="packSlit">
        <order-packing-slip :pack-slit-table-data="packSlitTableData"
          @update-ship-list="getPackingSlipTableData"></order-packing-slip>
      </el-tab-pane>
    </el-tabs>
    <cancel-order-dialog ref="cancelOrderDialog" @save-success="getOrderInfo"></cancel-order-dialog>
    <print-dialog ref="printDialog"></print-dialog>
    <cancel-history-dialog ref="cancelHistoryDialog"></cancel-history-dialog>
    <order-processing-info-dialog ref="orderProcessingInfoDialog"></order-processing-info-dialog>
    <!-- <popup-view :visible.sync="exportVisible" title="导出下载">
      <collapse-card-view title="导出下载">
        <div style="margin: 20px">
          <a :href="exportUrl" target="_blank">导出成功，点击下载</a>
        </div>
      </collapse-card-view>
    </popup-view> -->
  </div>
</template>

<script>
import {
  getOrderHeaderOrderHeaderSingle,
  createOrderHeader,
  // updateOrderHeaderById,
  deleteOrderHeaderById,
  createOrderHeaderAuditOrder,
  createOrderHeaderUnAuditOrder,
  createPackingSlip,
  // getPackingSlip,
  getOrderHeaderOrderItemSkuRedundantExport,
  updateOrderHeader,
  getPackingSlipByOrderId,
  createOrderHeaderModifyOrderHoldById
} from '@/api/gens-api/order'
import OrderBaseInfo from './components/OrderBaseInfo'
import OrderItemInfo from './components/OrderItemInfo'
import PaymentInfo from './components/PaymentInfo'
import CancelOrderDialog from './components/CancelOrderDialog'
import PrintDialog from './components/PrintDialog'
import CancelHistoryDialog from './components/CancelHistoryDialog'
import OrderPackingSlip from './components/OrderPackingSlip'
import OrderProcessingInfoDialog from './components/OrderProcessingInfoDialog'
import { getConsumerById, getConsumerSettleSettleInfoById } from '@/api/gens-api/crm'
export default {
  name: 'order-detail',
  components: { OrderItemInfo, OrderBaseInfo, PaymentInfo, CancelOrderDialog, PrintDialog, CancelHistoryDialog, OrderPackingSlip, OrderProcessingInfoDialog },
  data() {
    return {
      activeTab: 'baseInfo',
      loading: false,
      saveLoading: false,
      isSavingOrderItem: false, // 是否正在保存商品行
      id: '',
      consumerId: '',
      orderInfo: null,
      promotions: [],
      packSlitData: [],
      packSlitTableData: [],
      exportVisible: false,
      isPackageShip: false,
      isEnableCredit: false,
      overCreditType: 0,
      remainAmount: 0,
      orderTotalAmount: 0,
      settleType: 0, // 结算方式
      filterParams: {
        isOutOfStockOnly: false,
        isFutureStockOnly: false
      },
      // 标签页渲染状态
      isOrderItemInfoRendered: false,
      // 标签页加载状态
      tabLoading: {
        orderItemInfo: false,
        paymentInfo: false,
        packSlit: false
      }
    }
  },
  computed: {
    visitedViews() {
      return this.$store.state.tagsView.visitedViews
    },
    // ,
    // showCancel() {
    //   const isExit = this.orderInfo.orderItemSkus.some(i => )
    //   return this.orderInfo && (this.orderInfo.status === 1 || this.orderInfo.status === 2)
    // }
    // 判断当前模式是否为查看模式
    isViewMode() {
      return !!this.$route.query.view // 判断是否为查看模式
    },
    // 动态生成左侧按钮组
    leftButtons() {
      // 根据订单状态和权限动态生成按钮
      const buttons = [
        (!this.orderInfo ||
        [1, 2, 3,].includes(this.orderInfo?.status)) && {
          ...this.$menuButton.save,
          policy: this.id
            ? 'Order.OrderHeader.Update'
            : 'Order.OrderHeader.Create',
          loading: this.saveLoading,
          disabled: this.isSavingOrderItem // 保存商品行时禁用保存按钮
        },
        this.orderInfo &&
          this.orderInfo.status === 1 && {
            ...this.$menuButton.audit,
            policy: 'Order.OrderHeader.Audit'
          },
        this.orderInfo && {
          code: 'export',
          text: '订单明细导出',
          policy: 'Order.OrderHeader.OrderItemSkuExport'
        }
      ].filter(Boolean)
      // 如果是查看模式，仅保留【导出】按钮，隐藏其他操作按钮
      if (this.isViewMode) {
        return buttons.filter((btn) => btn.code === 'export')
      }
      return buttons
    },
    // 动态生成右侧按钮组
    rightButtons() {
      // 根据订单状态和权限动态生成按钮
      const buttons = [
        // this.orderInfo &&
        //   this.orderInfo.status === 6 && {
        //     ...this.$menuButton.delete,
        //     policy: 'Order.OrderHeader.Delete'
        //   },
        this.orderInfo &&
          this.orderInfo.isCanCancel && {
            ...this.$menuButton.cancel,
            policy: 'Order.OrderHeader.Cancel'
          },
        this.orderInfo &&
          this.$menuButton.custom({
            code: 'history',
            text: '取消记录',
            policy: 'Order.OrderHeader.CancelOrderPay'
          }),
        this.orderInfo && { code: 'orderHandleInfo', text: '订单处理信息' }
      ].filter(Boolean)
      // 如果是查看模式，仅保留【取消记录】和【订单处理信息】按钮
      if (this.isViewMode) {
        return buttons.filter((btn) =>
          ['history', 'orderHandleInfo'].includes(btn.code)
        )
      }
      return buttons
    }
  },
  watch: {
    consumerId: {
      handler(val){
        if (val) {
          this.getCreditLimitInfo(val)
          this.getConsumerInfo()
        }
      },
      immediate: true
    },
    // 监听标签页切换
    activeTab: {
      handler(newTab, oldTab) {
        console.log('Tab changed:', newTab, oldTab)

        // 处理商品信息标签页
        if (newTab === 'orderItemInfo' && !this.isOrderItemInfoRendered) {
          this.isOrderItemInfoRendered = true

          // 延迟一点时间再渲染组件，让标签页切换动画完成
          setTimeout(() => {
            this.tabLoading.orderItemInfo = true

            // 再延迟一点时间关闭加载状态，给组件渲染留出时间
            setTimeout(() => {
              this.tabLoading.orderItemInfo = false
            }, 300)
          }, 100)
        }
      }
    }
  },
  mounted() {
    console.log('order-detail mounted')
  },
  created() {
    this.id = this.$route.params.id
    if (this.id) {
      this.getIsHoldOrderInfo()
      this.getPackingSlipTableData()
    }
  },
  methods: {
    getConsumerInfo() {
      this.loading = true
      getConsumerById(this.consumerId).then(res => {
        this.overCreditType = res.overCreditHandleType
        this.settleType = res.settleType
      }).finally(() => {
        this.loading = false
      })
    },
    getCreditLimitInfo(consumerId){
      getConsumerSettleSettleInfoById(consumerId).then(res => {
        this.remainAmount = res.remainAmount
        this.isEnableCredit = res.isEnableCredit
      })
    },
    getConsumerId(val){
      this.consumerId = val
    },
    getIsPackageShip(val){
      this.isPackageShip = val
    },
    getOverCreditType(val){
      this.overCreditType = val
    },
    getOrderTotalAmount(val){
      this.orderTotalAmount = val
    },
    getPackSlitData(data){
      this.packSlitData = data || []
    },
    onFilterChange(params) {
      this.filterParams = { ...params }
      this.getOrderInfo()
    },
    getOrderInfo() {
      this.loading = true
      getOrderHeaderOrderHeaderSingle({
        id: this.id,
        ...this.filterParams
      }).then(res => {
        this.orderInfo = res
        this.consumerId = res.consumerId
        if (this.orderInfo.tips) {
          this.$message.warning(this.orderInfo.tips)
        }
      }).finally(() => {
        this.loading = false
      })
    },
    getIsHoldOrderInfo(){
      this.loading = true
      getOrderHeaderOrderHeaderSingle({
        id: this.id
      }).then(res => {
        this.orderInfo = res
        this.consumerId = res.consumerId
        if (this.orderInfo.tips) {
          this.$message.warning(this.orderInfo.tips)
        }
        if (!this.isViewMode) {
          this.holdOrderInfo()
        }
      }).finally(() => {
        this.loading = false
      })
    },
    holdOrderInfo(){
      if (this.orderInfo.status === 2 || this.orderInfo.status === 3) {
        createOrderHeaderModifyOrderHoldById({ id: this.orderInfo.id }).then(res => {
          this.getOrderInfo()
          alert('订单已被挂起，已避免修改过程中被发货')
        })
      }
    },
    getPackingSlipTableData(){
      this.loading = true
      getPackingSlipByOrderId(this.id).then(res => {
        this.packSlitTableData = res || []
      }).finally(() => {
        // this.loading = false
      })
    },
    saveOrder() {
      this.$refs.baseInfo.getFormValues().then(formValues => {
        if (!formValues) {
          return
        }
        // 尝试获取商品数据
        let orderItemSkus = []

        // 如果组件已存在，直接获取数据
        if (this.$refs.orderItemInfo) {
          orderItemSkus = this.$refs.orderItemInfo.getTableData() || []
        } else {
          // 如果组件不存在，直接从orderInfo中获取数据
          orderItemSkus = this.orderInfo && this.orderInfo.orderItemSkus ? [...this.orderInfo.orderItemSkus] : []
        }

        if (!orderItemSkus || !orderItemSkus.length) {
          this.$message.error('至少需要一行订单商品信息')
          return
        }

        const { ids = [] } = formValues.region || {}
        formValues.settleConsumerId = formValues.consumerId
        formValues.provinceId = ids[0]
        formValues.cityId = ids[1]
        formValues.districtId = ids[2]
        formValues.orderItemSkus = orderItemSkus.map((i) => ({
          id: i.id || undefined,
          itemSkuId: i.itemSkuId,
          qty: i.qty,
          isAppointPrice: true,
          salePrice: i.itemUnitPrice
        }))
        delete formValues.orderPays // 保存不带已有支付记录
        if (this.isEnableCredit && this.overCreditType === 2 && this.orderTotalAmount > this.remainAmount ) {
          this.$confirm(`您的信用额度不足，订单无发提交，请联系对应的营业`, '提示', {
            distinguishCancelAndClose: true,
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            beforeClose: (action, instance, done) => {
              if (action === 'confirm') {
                instance.confirmButtonLoading = true
                instance.confirmButtonLoading = false
                done()
              } else {
                done()
              }
            }
          })
        } else if (this.isEnableCredit && this.overCreditType === 1 && this.orderTotalAmount > this.remainAmount ) {
          this.$confirm(`您的订单已超过信用额度，订单会进入待审批，是否确认提交订单?`, '提示', {
            distinguishCancelAndClose: true,
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            beforeClose: async (action, instance, done) => {
              if (action === 'confirm') {
                instance.confirmButtonLoading = true
                await this.submitOrder(formValues)
                instance.confirmButtonLoading = false
                done()
              } else {
                done()
              }
            }
          })
        } else {
          this.submitOrder(formValues)
        }
      })
    },
    submitOrder(formValues){
      const api = this.id ? updateOrderHeader : createOrderHeader
      if (!this.id) {
        formValues.deliveryCharges = 0
      }
      this.saveLoading = true
      this.loading = true
      api(formValues).then(res => {
        this.$showOperationSuccessfulNotify()
        // if (this.id) {
        //   this.getOrderInfo()
        // } else {
          const fullPath = this.$route.fullPath
          const view = this.visitedViews.find(i => fullPath === i.fullPath)
          this.$store.dispatch('tagsView/delView', view)
          this.$router.push(`/order/order-list`)
        // }
      }).finally(() => {
        this.saveLoading = false
        this.loading = false
      })
    },
    // 保存商品行（复用原先的保存逻辑但不跳转页面）
    saveOrderItem(callbacks) {
      this.$refs.baseInfo.getFormValues().then(formValues => {
        if (!formValues) {
          callbacks && callbacks.onError && callbacks.onError()
          return
        }
        // 尝试获取商品数据
        let orderItemSkus = []

        // 如果组件已存在，直接获取数据
        if (this.$refs.orderItemInfo) {
          orderItemSkus = this.$refs.orderItemInfo.getTableData() || []
        } else {
          // 如果组件不存在，直接从orderInfo中获取数据
          orderItemSkus = this.orderInfo && this.orderInfo.orderItemSkus ? [...this.orderInfo.orderItemSkus] : []
        }

        if (!orderItemSkus || !orderItemSkus.length) {
          this.$message.error('至少需要一行订单商品信息')
          callbacks && callbacks.onError && callbacks.onError()
          return
        }

        const { ids = [] } = formValues.region || {}
        formValues.settleConsumerId = formValues.consumerId
        formValues.provinceId = ids[0]
        formValues.cityId = ids[1]
        formValues.districtId = ids[2]
        formValues.orderItemSkus = orderItemSkus.map((i) => ({
          id: i.id || undefined,
          itemSkuId: i.itemSkuId,
          qty: i.qty,
          isAppointPrice: true,
          salePrice: i.itemUnitPrice
        }))
        delete formValues.orderPays // 保存不带已有支付记录

        // 执行保存但不跳转页面
        this.submitOrderItemOnly(formValues, callbacks)
      }).catch(error => {
        callbacks && callbacks.onError && callbacks.onError()
      })
    },
    // 只保存订单商品，不跳转页面
    submitOrderItemOnly(formValues, callbacks){
      const api = this.id ? updateOrderHeader : createOrderHeader
      if (!this.id) {
        formValues.deliveryCharges = 0
      }
      // 不设置saveLoading和loading，避免影响顶部保存按钮的显示
      api(formValues).then(res => {
        this.$showOperationSuccessfulNotify('商品行保存成功')
        // 刷新订单数据但不跳转页面
        this.getOrderInfo()
        callbacks && callbacks.onSuccess && callbacks.onSuccess()
      }).catch(error => {
        callbacks && callbacks.onError && callbacks.onError()
      })
    },
    // 处理保存商品行loading状态变化
    handleSaveItemLoadingChange(isLoading) {
      this.isSavingOrderItem = isLoading
    },
    confirmAction(title, api, args) {
      this.$confirm(`确认${title}当前订单?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        beforeClose: (action, instance, done) => {
          if (action === 'confirm') {
            instance.confirmButtonLoading = true
            api(args).then(() => {
              this.$showOperationSuccessfulNotify()
              if (title === '删除') {
                const fullPath = this.$route.fullPath
                const view = this.visitedViews.find(i => fullPath === i.fullPath)
                this.$store.dispatch('tagsView/delView', view)
                this.$router.push(`/order/order-list`)
                return
              }
              this.getOrderInfo()
            }).finally(() => {
              instance.confirmButtonLoading = false
              done()
            })
          } else {
            done()
          }
        }
      })
    },
    deleteOrder() {
      this.confirmAction('删除', deleteOrderHeaderById, this.id)
    },
    auditOrder() {
      this.confirmAction('审核通过', createOrderHeaderAuditOrder, { id: this.id })
    },
    unauditOrder() {
      this.confirmAction('反审核', createOrderHeaderUnAuditOrder, { id: this.id })
    },
    cancelOrder() {
      this.$refs.cancelOrderDialog.open({
        id: this.id,
        orderNo: this.orderInfo.orderNo
      })
    },
    handleCreatePackingSlip() {
      // if (this.orderInfo && this.orderInfo.isAllowMultiShip === 1) {
      //   if (!this.packSlitData.length) {
      //     this.$notify({
      //       title: '提示',
      //       message: '请先选择订单商品',
      //       type: 'info',
      //       duration: 3000
      //     })
      //     return false
      //   }
      // } else {
      //   this.packSlitData = this.orderInfo.orderItemSkus.map(i => ({ ...i, shipQty: i.qty }))
      // }
      if (!this.packSlitData.length) {
        this.$notify({
          title: '提示',
          message: '请先选择订单商品',
          type: 'info',
          duration: 3000
        })
        return false
      }
      const list = this.packSlitData.filter(i => i.status !== 6 ).map(i => ({
        orderItemSkuId: i.id
        // ,
        // qty: i.shipQty
      }))
      let totallyQty = 0
      list.forEach(i => {
        totallyQty += Number(i.qty)
      })
      this.$confirm(`发货总数量为${totallyQty}，确认要创建发货单?`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        return createPackingSlip({
          orderId: this.id,
          packingSlipItemSkus: list
        })
      }).then(() => {
        this.getOrderInfo()
      })
    },
    exportOrderItemSku() {
      getOrderHeaderOrderItemSkuRedundantExport({
        orderId: this.id
      }).then(res => {
        this.$utils.createDownload(res)
      })
    },
    handlePrint(type){
      const isExit = (this.orderInfo.orderItemSkus || []).some(i => i.stockStatus === 2)
      if (isExit) {
        this.$confirm(`该订单中含有缺货商品,确定继续打印当前订单?`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          beforeClose: (action, instance, done) => {
            if (action === 'confirm') {
              instance.confirmButtonLoading = true
              this.$refs.printDialog.open(this.id, type)
              instance.confirmButtonLoading = false
              done()
            } else {
              done()
            }
          }
        })
      } else {
        this.$refs.printDialog.open(this.id, type)
      }
    },
    handleButtonClick(code) {
      if (code === 'save') {
        this.saveOrder()
      } else if (code === 'delete') {
        this.deleteOrder()
      } else if (code === 'audit') {
        this.auditOrder()
      } else if (code === 'unaudit') {
        this.unauditOrder()
      } else if (code === 'cancel') {
        this.cancelOrder()
      } else if (code === 'print1') {
        this.handlePrint(1)
      } else if (code === 'print2') {
        this.handlePrint(2)
      } else if (code === 'history') {
        this.$refs.cancelHistoryDialog.open(this.id)
      } else if (code === 'createPackingSlip') {
        // this.handleCreatePackingSlip()
      } else if (code === 'export') {
        this.exportOrderItemSku()
      } else if (code === 'orderHandleInfo') {
        this.$refs.orderProcessingInfoDialog.open(this.id)
      }
    }
  }
}
</script>

<style scoped>
::v-deep.app-container .el-tabs__content {
  padding: 0px;
  padding-bottom: 10px;
}
::v-deep.app-container .el-tabs {
  margin: 5px;
  margin-top: 5px;
}

::v-deep.app-container .el-tabs__item {
  height: 35px;
  line-height: 35px;
}
</style>
