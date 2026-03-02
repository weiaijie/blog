<template>
  <div class="consumer-detail-consumer-address">
    <table-list-card ref="dataListView"
                     :api="getConsumerAddressList"
                     sortable="custom"
                     paging
                     highlight-current-row
                     :show-setting="false"
                     :selection="true"
                     :selection-fixed="true"
                     :query-params="{ consumerId }"
                     :columns="columns"
                     :use-filter-bar="true"
                     :table-name="`consumer-shipping-address-${consumerId}`"
                     @selectChange="handleSelectionChange">
      <template slot="button">
        <el-button size="mini"
                   :loading="batchDeleting"
                   :disabled="!selectedAddresses.length"
                   @click="handleBatchDelete">
          批量删除
        </el-button>
        <el-button v-if="$cp('CRM.Consumer.ConsumerAddressInfoSave')"
                   size="mini"
                   @click="handleCreateAddress">新增</el-button>
      </template>
    </table-list-card>
    <consumer-address-dialog ref="consumerAddressDialog" @save-success="getList"></consumer-address-dialog>
  </div>
</template>

<script>
import {
  getConsumerAddressList,
  deleteConsumerAddressById,
  createConsumerDeleteMuiltyAddress,
  createConsumerSaveAddress,
  createConsumerImportConsumerAddress
} from '@/api/gens-api/crm'
import ConsumerAddressDialog from './ConsumerAddressDialog'
export default {
  name: 'ConsumerShippingAddress',
  components: { ConsumerAddressDialog },
  data() {
    return {
      consumerId: this.$route.params.id || '',
      listLoading: true,
      tempValue: '',
      selectedAddresses: [],
      batchDeleting: false,
      addressImporting: false
    }
  },
  computed: {
    columns() {
      return [
        {
          label: '收货方',
          prop: 'recipient',
          minWidth: 150,
          filter: {
            key: 'recipient',
            type: 'text',
            quick: true,
            placeholder: '请输入收货方'
          }
        },
        {
          label: '收货人',
          prop: 'receiverName',
          minWidth: 120,
          filter: {
            key: 'receiverName',
            type: 'text',
            quick: true,
            placeholder: '请输入收货人'
          }
        },
        {
          label: '电话',
          prop: 'phone',
          minWidth: 120,
          filter: {
            key: 'phone',
            type: 'text',
            quick: true,
            placeholder: '请输入电话'
          }
        },
        {
          label: '省市区',
          prop: 'region',
          minWidth: 120,
          formatter(item, data) {
            return (data.provinceName + data.cityName + data.districtName) || '--'
          }
        },
        {
          label: '详细地址',
          prop: 'address',
          minWidth: 120,
          filter: {
            key: 'address',
            type: 'text',
            quick: true,
            placeholder: '请输入详细地址'
          }
        },
        {
          label: '楼栋',
          prop: 'buildingName',
          minWidth: 120
        },
        {
          label: '邮编',
          prop: 'postalcode',
          minWidth: 120
        },
        {
          label: '地址类型',
          prop: 'addressTypeText',
          minWidth: 120,
          align: 'center'
        },
        {
          label: '是否默认',
          prop: 'isDefaultText',
          minWidth: 120,
          align: 'center'
        },
        {
          width: 150,
          label: '操作',
          prop: 'action',
          type: 'button',
          fixed: 'right',
          buttons: [{
            id: 'default',
            text: '设为默认',
            eventType: 'primary',
            actionType: 'confirm',
            confirmText: row => `确认将收货信息’<span style="color: red;">${row.receiverName}</span>‘设为默认？`,
            loading: false,
            show: row => row.isDefault !== 1,
            click: (row, button, closeConfirm) => {
              this.handleRowDefault(row, button, closeConfirm)
            },
            policy: 'CRM.Consumer.ConsumerAddressInfoSave'
          },
            {
              id: 'edit',
              text: '编辑',
              eventType: 'primary',
              click: row => this.$refs.consumerAddressDialog.open({
                consumerId: this.consumerId,
                ...row
              }),
              policy: 'CRM.Consumer.ConsumerAddressInfoSave'
            }, {
              id: 'delete',
              text: '删除',
              eventType: 'danger',
              actionType: 'confirm',
              confirmText: row => `确认删除收货信息’<span style="color: red;">${row.receiverName}</span>‘？`,
              loading: false,
              click: (row, button, closeConfirm) => {
                this.handleRowDelete(row, button, closeConfirm)
              },
              policy: 'CRM.Consumer.ConsumerAddressInfoSave'
            }]
        }]
    }
  },
  methods: {
    getConsumerAddressList,

    getList() {
      this.selectedAddresses = []
      this.$refs['dataListView'].load()
    },
    handleSelectionChange(selection) {
      this.selectedAddresses = selection || []
    },
    handleBatchDelete() {
      if (!this.selectedAddresses.length) {
        return
      }
      this.$confirm(`确认删除选中的 ${this.selectedAddresses.length} 条收货地址？`, '提示', {
        type: 'warning'
      }).then(() => {
        this.batchDeleting = true
        createConsumerDeleteMuiltyAddress({
          consumerId: this.consumerId,
          addressIds: this.selectedAddresses.map(address => address.id)
        }).then(() => {
          this.$showOperationSuccessfulNotify()
          this.getList()
        }).catch((error) => {
          this.$message.error(error?.message || '批量删除失败')
        }).finally(() => {
          this.batchDeleting = false
        })
      }).catch(() => {})
    },
    handleConsumerAddressImportRequest({ file, onSuccess, onError }) {
      if (!file) {
        onError && onError(new Error('请选择文件'))
        return
      }
      this.addressImporting = true
      const formData = new FormData()
      formData.append('file', file)
      createConsumerImportConsumerAddress(formData)
        .then((res) => {
          this.$showOperationSuccessfulNotify()
          this.getList()
          onSuccess && onSuccess(res)
        })
        .catch((error) => {
          const message = error?.message || '导入失败'
          this.$message.error(message)
          onError && onError(error)
        })
        .finally(() => {
          this.addressImporting = false
        })
    },
    handleRowDefault(row, button, closeConfirm) {
      button.loading = true
      createConsumerSaveAddress({
        ...row,
        isDefault: 1
      }).then(() => {
        this.$showOperationSuccessfulNotify()
        this.getList()
      }).finally(() => {
        button.loading = false
        closeConfirm()
      })
    },
    handleRowDelete(row, button, closeConfirm) {
      button.loading = true
      deleteConsumerAddressById(row.id).then(() => {
        this.$showOperationSuccessfulNotify()
        this.getList()
      }).finally(() => {
        button.loading = false
        closeConfirm()
      })
    },
    handleCreateAddress(code) {
      this.$refs.consumerAddressDialog.open({
        consumerId: this.consumerId
      })
    }
  }
}
</script>

<style lang="scss">
.consumer-detail-consumer-address {
  ::v-deep .table-list-card {
    margin-top: 20px;
    margin-bottom: 20px;
  }
  
  ::v-deep .quick-filter {
    margin-right: 15px;
    margin-bottom: 15px;
  }
  
  ::v-deep .el-input__inner {
    height: 32px;
  }
}
</style>
