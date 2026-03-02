<template>
  <view :style="colorStyle" class="cashier-page">
    <view class="w-full relative">
      <NavBar
        titleText="订单支付"
        textSize="34rpx"
        :isScrolling="false"
        :iconColor="'#ffffff'"
        :textColor="'#ffffff'"
        showBack
      ></NavBar>
      <view class="px-20 relative z-80">
        <!-- 支付金额信息 -->
        <view class="pay-content">
          <view class="pay-info">
            <view class="pay-status-label">待付款</view>
            <view class="pay-amount-row">
              <view class="pay-amount-label">需付款:</view>
              <view class="pay-amount">¥ {{ formatPrice(payPriceShow) }}</view>
              <view class="pay-time-label">支付剩余:</view>
              <view class="pay-time-text">{{ timeRemaining }}</view>
            </view>
          </view>
        </view>
      </view>
      <view
        class="w-full bg-gradient abs-lt header-bg-container"
        :style="{ height: 213 + sysHeight + 'px' }"
      >
        <image
          class="order-bg-icon"
          src="https://xiangyijinlian.oss-cn-hangzhou.aliyuncs.com/attach/2025/12/d55a4202512121128583852.png"
          mode="aspectFit"
        ></image>
        <view class="w-full abs-lb white_jianbian z-20"></view>
      </view>
    </view>
    <view class="pay-content-wrapper mt-20">
      <!-- 统一使用组合支付UI (所有用户) -->
      <view v-show="isShow">
        <!-- <view class="pay_title">选择支付方式</view> -->

        <!-- 金币支付 (仅企业用户且福利金支付可用时显示,充值场景不显示) -->
        <view
          class="pay_item_new rd-24rpx"
          v-if="isEnterprise && welfarePayStatus == 1 && !onlyWechat"
          :class="{ disabled: !welfareEnabled }"
        >
          <view class="flex-between-center mb-24">
            <view class="flex-y-center">
              <view class="pay_icon_wrapper">
                <image
                  class="pay_icon_img"
                  src="/static/images/money-icon.png"
                  mode="widthFix"
                ></image>
              </view>
              <view class="ml-20">
                <view class="pay_name">金币支付</view>
                <view class="pay_tips">可用额度: ¥{{ enterpriseWelfare }}</view>
              </view>
            </view>
            <view class="switch-wrapper">
              <switch
                :checked="welfareEnabled"
                @change="onWelfareSwitch"
                :color="'var(--view-theme, #e93323)'"
                style="transform: scale(0.8)"
              />
            </view>
          </view>
          <view class="flex-between-center">
            <view
              class="pay_input_wrapper"
              :class="{ disabled: !welfareEnabled }"
              @tap="onWelfareWrapperClick"
            >
              <text
                class="pay_input_prefix"
                v-if="
                  welfareEnabled ||
                  (welfareAmount && parseFloat(welfareAmount) > 0)
                "
                >¥</text
              >
              <input
                ref="welfareInput"
                class="pay_input_new"
                type="text"
                v-model="welfareAmount"
                placeholder="请输入金额"
                @input="onWelfareInput"
                @blur="onWelfareBlur"
                :disabled="!welfareEnabled"
              />
              <view
                class="pay_all_btn_new"
                :class="{ disabled: !welfareEnabled }"
                @tap.stop="useAllWelfare"
                >全额</view
              >
            </view>
          </view>
        </view>

        <!-- 余额支付 (所有用户都显示,充值场景不显示) -->
        <view
          class="pay_item_new rd-24rpx"
          v-if="!onlyWechat"
          :class="{ disabled: !balanceEnabled }"
        >
          <view class="flex-between-center mb-24">
            <view class="flex-y-center">
              <view class="pay_icon_wrapper">
                <image
                  class="pay_icon_img"
                  src="/static/images/balance-icon.png"
                  mode="aspectFit"
                ></image>
              </view>
              <view class="ml-20">
                <view class="pay_name">余额支付</view>
                <view class="pay_tips">可用余额: ¥{{ now_money }}</view>
              </view>
            </view>
            <view class="switch-wrapper">
              <switch
                :checked="balanceEnabled"
                @change="onBalanceSwitch"
                :color="'var(--view-theme, #e93323)'"
                style="transform: scale(0.8)"
              />
            </view>
          </view>
          <view class="flex-between-center">
            <view
              class="pay_input_wrapper"
              :class="{ disabled: !balanceEnabled }"
              @tap="onBalanceWrapperClick"
            >
              <text
                class="pay_input_prefix"
                v-if="
                  balanceEnabled ||
                  (balanceAmount && parseFloat(balanceAmount) > 0)
                "
                >¥</text
              >
              <input
                ref="balanceInput"
                class="pay_input_new"
                type="text"
                v-model="balanceAmount"
                placeholder="请输入金额"
                @input="onBalanceInput"
                :disabled="!balanceEnabled"
              />
              <view
                class="pay_all_btn_new"
                :class="{ disabled: !balanceEnabled }"
                @tap.stop="useAllBalance"
                >全额</view
              >
            </view>
          </view>
        </view>

        <!-- 微信支付 (所有用户都显示) -->
        <view class="pay_item_new rd-24rpx" style="border-bottom: none">
          <view class="flex-between-center mb-24">
            <view class="flex-y-center">
              <view class="pay_icon_wrapper">
                <image
                  class="pay_icon_img"
                  src="/static/images/wechat-icon.png"
                  mode="aspectFit"
                ></image>
              </view>
              <view class="ml-20">
                <view class="pay_name">微信支付</view>
                <view class="pay_tips">自动支付剩余金额</view>
              </view>
            </view>
          </view>
          <view class="pay_input_wrapper disabled">
            <text class="pay_input_prefix" v-if="onlinePayAmount">¥</text>
            <view class="pay_input_new" style="color: #000">{{
              onlinePayAmount || "加载中..."
            }}</view>
          </view>
        </view>
      </view>
    </view>
    <view class="w-full h-128 pb-safe flex-center fixed-lb">
      <!-- :class="welfarePayStatus ? 'bottom-enterprise' : 'bottom-normal'" -->
      <view
        class="w-710 h-88 flex-center rd-40rpx text--w111-fff fs-32 order-btn"
        @click="goPay()"
        >确认支付 ¥ {{ payPriceShow ? formatPrice(payPriceShow) : "" }}</view
      >
    </view>
    <view v-show="false" v-html="formContent"></view>
  </view>
</template>

<script>
import countDown from '@/components/countDown';
import colors from "@/mixins/color";
import { getCashierOrder, orderPay } from "@/api/order";
import { rechargePayAPi, memberCardPayApi } from "@/api/user.js"
import { HTTP_REQUEST_URL } from '@/config/app';
import NavBar from "@/components/NavBar.vue";

let sysHeight = uni.getWindowInfo().statusBarHeight;

export default {
	components: {
		countDown,
		NavBar,
	},
	mixins: [colors],
	computed: {
		// 计算在线支付金额 (所有用户都适用)
		onlinePayAmount() {
			// 确保响应式依赖
			const total = parseFloat(this.payPriceShow) || 0;
			const welfareEnabled = this.welfareEnabled;
			const balanceEnabled = this.balanceEnabled;
			const welfareAmount = this.welfareAmount;
			const balanceAmount = this.balanceAmount;

			// 企业用户可能有福利金,普通用户福利金为0
			let welfare = (this.isEnterprise && welfareEnabled) ? (parseFloat(welfareAmount) || 0) : 0;
			let balance = balanceEnabled ? (parseFloat(balanceAmount) || 0) : 0;

			let online = total - welfare - balance;
			console.log('[' + new Date().toLocaleTimeString() + '] 计算在线支付金额:', {
				payPriceShow: this.payPriceShow,
				total,
				welfare,
				balance,
				online,
				welfareAmount,
				balanceAmount,
				welfareEnabled,
				balanceEnabled,
				isEnterprise: this.isEnterprise
			});

			// 如果订单金额为0,说明数据还没加载,返回空字符串
			if (total === 0) {
				return '';
			}

			return online > 0 ? online.toFixed(2) : '0.00';
		},
		payTypeList() {
			let list = [];
			this.cartArr.forEach(item => {
				if (item.payStatus == 1) {
					list.push(item);
				}
			})
			list.length && this.payType(list[0].value, 0)
			return list
		}
	},
	data() {
		return {
			sysHeight: sysHeight,
			invalidTime: 0,
				checked:false,
				orderId: 0,
				timeRemaining: '00时00分00秒',
				timeTimer: null,
			fromType: '',
			onlyWechat: false, // 是否只允许微信支付(充值场景)
			active: -1,
			payPrice: 0,
			payPriceShow: 0,
			now_money:'',
			payPostage: 0,
			offlinePostage: false,
			invalidTime: 0,
			initIn: false,
			jumpData: {
				orderId: '',
				msg: ''
			},
			formContent: '',
			// 企业用户相关
			isEnterprise: false, // 是否企业用户
			enterpriseWelfare: '0.00', // 企业福利金余额
			welfarePayStatus: 0, // 福利金支付是否可用(0-不可用,1-可用,控制金币支付区域显示)
			welfareAmount: '', // 福利金支付金额
			balanceAmount: '', // 余额支付金额
			welfareEnabled: false, // 福利金开关(默认关闭)
			balanceEnabled: false, // 余额开关(默认关闭)
			onlinePayType: 'weixin', // 在线支付方式
			cashierOpenId: '',
			payInitiated: false, // 标记是否已发起支付（H5模式下用于防止重复支付）
			cartArr: [
				{
					"name": "微信支付",
					"icon": HTTP_REQUEST_URL + "/statics/images/order/wx_pay.png",
					value: 'weixin',
					title: '使用微信快捷支付',
					payStatus: 1,
				},
				{
					"name": "支付宝支付",
					"icon": HTTP_REQUEST_URL + "/statics/images/order/alipay.png",
					value: 'alipay',
					title: '使用线上支付宝支付',
					payStatus: 1,
				},
				{
					"name": "余额支付",
					"icon": HTTP_REQUEST_URL + "/statics/images/order/yue_pay.png",
					value: 'yue',
					title: '可用余额:',
					payStatus: 1,
				},
				{
					"name": "线下支付",
					"icon": HTTP_REQUEST_URL + "/statics/images/order/xianxia_pay.png",
					value: 'offline',
					title: '选择线下付款方式',
					payStatus: 2,
				}
			],
			paytype:'',
			isShow: false
		}
	},
	onLoad(options) {
		if (options.order_id) this.orderId = options.order_id;
		if (options.from_type) this.fromType = options.from_type;
		if (options.only_wechat) this.onlyWechat = options.only_wechat == '1';
		this.getCashierOrder();
	},
	onShow() {
		if (!this.orderId) return;

		// #ifdef H5
		// H5模式下：如果已经发起过支付，直接跳转到支付结果页面，防止重复支付
		if (this.payInitiated) {
			console.log('H5支付已发起，直接跳转到支付结果页');
			uni.redirectTo({
				url: `/pages/goods/order_pay_status/index?order_id=${this.orderId}&type=3`
			});
			return;
		}
		// #endif

		const key = this.getPayRedirectKey();
		const shouldRedirect = uni.getStorageSync(key);
		if (shouldRedirect) {
			uni.removeStorageSync(key);
			uni.redirectTo({
				url: `/pages/goods/order_pay_status/index?order_id=${this.orderId}`
			});
		}
	},
	onUnload() {
		if (this.timeTimer) {
			clearInterval(this.timeTimer);
			this.timeTimer = null;
		}
	},
	methods: {
		formatPrice(price) {
			const num = Number(price);
			if (isNaN(num)) {
				return "0.00";
			}
			return num.toFixed(2);
		},
		getPayRedirectKey() {
			return `cashier_pay_redirect_${this.orderId || ''}`;
		},
		markPayRedirect() {
			if (!this.orderId) return;
			uni.setStorageSync(this.getPayRedirectKey(), Date.now());
		},
		getWechatOpenId() {
			const userInfo =
				(this.$store && this.$store.getters && this.$store.getters.userInfo) || {};
			return (
				this.cashierOpenId ||
				userInfo.openid ||
				userInfo.open_id ||
				userInfo.wechat_openid ||
				userInfo.wechatOpenid ||
				userInfo.openId ||
				''
			);
		},
		getH5PayFrom() {
			const isWeixin =
				this.$wechat && this.$wechat.isWeixin && this.$wechat.isWeixin();
			return isWeixin && this.getWechatOpenId() ? 'weixin' : 'weixinh5';
		},
		formatTimeRemaining() {
			if (!this.invalidTime || this.invalidTime <= 0) {
				this.timeRemaining = '00时00分00秒';
				return '00时00分00秒';
			}
			const now = Math.floor(Date.now() / 1000);
			const diff = this.invalidTime - now;
			if (diff <= 0) {
				this.timeRemaining = '00时00分00秒';
				return '00时00分00秒';
			}
			const hours = Math.floor(diff / 3600);
			const minutes = Math.floor((diff % 3600) / 60);
			const seconds = diff % 60;
			const timeStr = `${String(hours).padStart(2, '0')}时${String(minutes).padStart(2, '0')}分${String(seconds).padStart(2, '0')}秒`;
			this.timeRemaining = timeStr;
			return timeStr;
		},
		startTimeCountdown() {
			if (this.timeTimer) {
				clearInterval(this.timeTimer);
			}
			this.formatTimeRemaining();
			this.timeTimer = setInterval(() => {
				this.formatTimeRemaining();
			}, 1000);
		},
		payType(paytype, index) {
			this.active = index;
			this.paytype = paytype;
			if (this.offlinePostage) {
				if (paytype == 'offline') {
					this.payPriceShow = this.$util.$h.Sub(this.payPrice, this.payPostage);
				} else {
					this.payPriceShow = this.payPrice;
				}
			}
		},
		getCashierOrder() {
			getCashierOrder(this.orderId, this.fromType).then(res => {
				this.isShow = true;
				this.cashierOpenId =
					res.data.openid ||
					res.data.open_id ||
					res.data.wechat_openid ||
					res.data.wechatOpenid ||
					this.cashierOpenId;
				//微信支付是否开启
				this.cartArr[0].payStatus = res.data.pay_weixin_open || 0
				//支付宝是否开启
				// #ifdef MP-WEIXIN
				/*微信小程序环境中不允许支付宝支付*/
				this.cartArr[1].payStatus = 0;
				// #endif
				// #ifdef H5
				/*微信公众号环境中不允许支付宝支付*/
				this.cartArr[1].payStatus = this.$wechat.isWeixin() ? 0 : res.data.ali_pay_status;
				// #endif
				// #ifdef APP-PLUS
				this.cartArr[1].payStatus = res.data.ali_pay_status || 0;
				// #endif
				//余额支付是否开启
				this.cartArr[2].payStatus = res.data.yue_pay_status;
				this.now_money = res.data.now_money;
				//线下支付是否开启
				if (res.data.offline_pay_status == 1) {
					this.cartArr[3].payStatus = 1
				} else {
					this.cartArr[3].payStatus = 0
				}

				// 企业福利金信息
				this.isEnterprise = res.data.is_enterprise == 1;
				this.enterpriseWelfare = res.data.enterprise_welfare || '0.00';
				this.welfarePayStatus = res.data.welfare_pay_status || 0; // 福利金是否可用(控制金币支付区域显示)

				// 如果是企业用户,添加金币支付选项(旧的单一支付方式列表)
				if (this.isEnterprise && res.data.welfare_pay_status == 1) {
					// 在数组开头插入金币支付(暂时使用积分图标)
					this.cartArr.unshift({
						"name": "金币支付",
						"icon": HTTP_REQUEST_URL + "/statics/images/order/prize_integral_icon.png",
						value: 'welfare',
						title: '可用额度:',
						payStatus: 1,
					});
				}
				// 订单价格
				this.payPrice = this.payPriceShow = res.data.pay_price
				console.log('订单数据加载完成, payPriceShow=', this.payPriceShow);
				//剩余时间
				this.invalidTime = res.data.invalid_time;
				// 邮费
				this.payPostage = res.data.pay_postage;
				this.getShowPay();
				// 启动倒计时
				if (this.invalidTime) {
					this.startTimeCountdown();
				}

				// 强制触发计算属性更新
				this.$nextTick(() => {
					console.log('nextTick后, onlinePayAmount=', this.onlinePayAmount);
				});
			}).catch(err => {
				this.isShow = true;
				uni.hideLoading();
				return this.$util.Tips({
					title: err
				})
			})
		},
		getShowPay(){
			//付费会员购买和余额充值不允许使用线下支付和余额支付，未开启线上支付支付的话给出提示并且返回上一页
			//检查支付类型列表数组的payStatus是不是都是0或者2
			const isAllPayStatusZero = this.cartArr.every(item => item.payStatus == 0 || item.payStatus == 2);
			if(isAllPayStatusZero && ['vip','recharge'].includes(this.fromType)){
				return this.$util.Tips({
					title: '未开启线上支付，请联系管理员'
				}, {
					tab: 3,
				});
			}
		},
		goPay(){
			let that = this;

			// #ifdef H5
			// H5模式下：如果已经发起过支付，直接跳转到支付结果页面
			if (this.payInitiated) {
				console.log('H5支付已发起，直接跳转到支付结果页');
				let backUrl = '/pages/goods/order_pay_status/index?order_id=' + this.orderId + '&type=3';
				uni.redirectTo({ url: backUrl });
				return;
			}
			// #endif

			// #ifdef H5
			// 微信内拦截提示已移到支付返回处理里
			// #endif

			// 如果是只允许微信支付的场景(充值场景 only_wechat=1)
			// 强制使用微信支付，不受其他任何字段影响
			if (that.onlyWechat) {
				// 充值场景强制使用微信支付
				that.active = 0;
				that.paytype = 'weixin';
				// 继续执行原有的单一支付逻辑（跳过组合支付）
			} else if (that.fromType == 'order') {
				// 订单支付场景使用组合支付逻辑
				return that.goCombinationPay();
			}

			if(that.active == -1) return that.$util.Tips({
				title: '请选择付款方式'
			});
			if (!that.orderId) return that.$util.Tips({
				title: '请选择要支付的订单'
			});
			if (that.paytype == 'yue' && parseFloat(this.now_money) < parseFloat(that.payPriceShow)) return that.$util.Tips({
				title: '余额不足'
			});

			uni.showLoading({
				title: '支付中'
			});

			let funApi = '';
			if(this.fromType == 'order'){
				funApi = orderPay({
					uni: that.orderId,
					paytype: that.paytype,
					// #ifdef MP
					'from': 'routine',
					// #endif
					// #ifdef H5
					'from': that.getH5PayFrom(),
					quitUrl: location.port ? location.protocol + '//' + location.hostname + ':' + location.port + '/pages/goods/order_pay_status/index?order_id=' + this.orderId : location.protocol + '//' + location.hostname +'/pages/goods/order_pay_status/index?order_id=' + this.orderId
					// #endif
					// #ifdef APP-PLUS
					,'from': 'app',
					quitUrl: '/pages/goods/order_pay_status/index?order_id=' + this.orderId
					// #endif
				})
			}else if(this.fromType == 'recharge'){
				funApi = rechargePayAPi({
					uni: this.orderId,
					paytype: that.paytype,
					// #ifdef MP
					'from': 'routine',
					// #endif
					// #ifdef H5
					'from': that.getH5PayFrom(),
					quitUrl: location.port ? location.protocol + '//' + location.hostname + ':' + location.port + '/pages/users/user_payment/index' : location.protocol + '//' + location.hostname +'/pages/users/user_payment/index'
					// #endif
					// #ifdef APP-PLUS
					,'from': 'app',
					quitUrl: '/pages/users/user_payment/index'
					// #endif
				})
			}else if(this.fromType == 'vip'){
				funApi = memberCardPayApi({
					uni: this.orderId,
					paytype: this.paytype,
					// #ifdef MP
					'from': 'routine',
					// #endif
					// #ifdef H5
					'from': that.getH5PayFrom(),
					quitUrl: '/pages/annex/vip_paid/index'
					// #endif
					// #ifdef APP-PLUS
					,'from': 'app',
					quitUrl: '/pages/annex/vip_paid/index'
					// #endif
				})
			}

			funApi.then(res=>{
				let status = res.data.status,
				orderId = res.data.result.order_id || '',
				jsConfig = res.data.result.jsConfig;
				//页面回调地址
				let PageObj = {
					'order': '/pages/goods/order_pay_status/index?order_id=' + this.orderId + '&msg=' +res.msg +'&type=3' + '&totalPrice=' + this.payPriceShow,
					'recharge': '/pages/users/user_payment/index',
					'vip': '/pages/annex/vip_paid/index',
				};
				let backUrl = PageObj[this.fromType];
			switch (status) {
				case 'ORDER_EXIST':
				case 'EXTEND_ORDER':
				case 'PAY_ERROR':
					this.pageReject(res.msg,backUrl);
					break;
				case 'SUCCESS':
					this.pageReject(res.msg,backUrl);
					break;
				case 'WECHAT_PAY':
					// 检查是否是银联支付(嵌套在jsConfig中)
					if (jsConfig && jsConfig.status === 'UMS_MINI_PAY') {
						this.umsWechatPayFun(jsConfig.result, backUrl);
					} else if (jsConfig && jsConfig.status === 'UMS_H5_PAY') {
						// H5支付: 新窗口打开支付页面,当前页面跳转到支付状态页
						this.handleH5Pay(jsConfig.result.pay_url, backUrl);
					} else {
						// 原有的微信支付逻辑
						this.wechatPayFun(res.data.result, backUrl);
					}
					break;
				case 'UMS_MINI_PAY':
					// 银联商务 - 小程序支付
					this.umsWechatPayFun(res.data.result, backUrl);
					break;
				case 'UMS_H5_PAY':
					// 银联商务 - H5支付: 新窗口打开支付页面,当前页面跳转到支付状态页
					this.handleH5Pay(res.data.result.pay_url, backUrl);
					break;
				case 'PAY_DEFICIENCY':
					uni.hideLoading();
					this.pageReject(res.msg,backUrl);
					break;
				case "WECHAT_H5_PAY":
					uni.hideLoading();
					let h5JsConfig = res.data.result.jsConfig;

					// 检查是否是银联H5支付(嵌套在jsConfig中)
					if (h5JsConfig && h5JsConfig.status === 'UMS_H5_PAY') {
						console.log('检测到银联H5支付(WECHAT_H5_PAY状态), pay_url:', h5JsConfig.result.pay_url);
						// H5支付: 新窗口打开支付页面,当前页面跳转到支付状态页
						this.handleH5Pay(h5JsConfig.result.pay_url, backUrl);
					} else {
						// 原生微信H5支付
						console.log('使用原生微信H5支付, mweb_url:', h5JsConfig.mweb_url);
						// #ifdef H5
						// 标记支付已发起，然后跳转到微信支付页面
						this.payInitiated = true;
						// #endif
						setTimeout(() => {
							location.href = h5JsConfig.mweb_url + '&redirect_url=' + window.location.protocol + '//' + window.location.host + backUrl;
						}, 500);
					}
					break;

				case 'ALIPAY_PAY':
					//#ifdef H5
					uni.hideLoading();
					that.formContent = res.data.result.jsConfig;
					that.$nextTick(() => {
						document.getElementById('alipaysubmit').submit();
					})
					//#endif
					// #ifdef APP-PLUS
					uni.requestPayment({
						provider: 'alipay',
						orderInfo: jsConfig,
						success: (e) => {
							that.pageReject('支付成功',backUrl);
						},
						fail: (e) => {
							that.pageReject('支付失败',backUrl);
						},
						complete: () => {
							uni.hideLoading();
						},
					});
					// #endif
					break;
				}
			}).catch(err=>{
				uni.hideLoading();
				return that.$util.Tips({
					title: err
				});
			})
		},
		wechatPayFun(data, backUrl){
			let that = this;
			// #ifdef MP
			uni.requestPayment({
				timeStamp: data.jsConfig.timestamp || data.jsConfig.timeStamp,  // 兼容两种命名方式
				nonceStr: data.jsConfig.nonceStr,
				package: data.jsConfig.package,
				signType: data.jsConfig.signType,
				paySign: data.jsConfig.paySign,
				success: function(res) {
					console.log("success", res);
					that.pageReject('支付成功',backUrl);
				},
				fail: function(e) {
					console.log("fail",e);
					that.pageReject('支付失败',backUrl);
				},
			})
			// #endif
			// #ifdef H5
			this.$wechat.pay(jsConfig).then(res => {
				this.pageReject('支付成功',backUrl);
			}).catch(res => {
				if (!this.$wechat.isWeixin()) {
					this.pageReject('支付失败',backUrl);
				}
				if (res.errMsg == 'chooseWXPay:cancel') {
					this.pageReject('取消支付',backUrl);
				}
			})
			// #endif
			// #ifdef APP-PLUS
			uni.requestPayment({
				provider: 'wxpay',
				orderInfo: jsConfig,
				success: (e) => {
					that.pageReject('支付成功',backUrl);
				},
				fail: (e) => {
					that.pageReject('支付失败',backUrl);
				},
			});
			// #endif
		},
		// 银联商务微信支付
		umsWechatPayFun(payData, backUrl) {
			let that = this;
			console.log('===== 银联支付方法调用 =====');
			console.log('订单号:', this.orderId);
			console.log('支付参数:', payData);
			console.log('回调URL:', backUrl);

			// #ifdef MP
			// 小程序支付
			console.log('使用小程序支付');
			uni.requestPayment({
				provider: 'wxpay',
				timeStamp: String(payData.timeStamp),
				nonceStr: String(payData.nonceStr),
				package: String(payData.package),
				signType: String(payData.signType),
				paySign: String(payData.paySign),
				success: function(res) {
					console.log('===== 小程序支付成功回调 =====');
					console.log('支付结果:', res);
					// 支付成功,跳转到支付状态页面,带上pay_success=1参数
					let successUrl = backUrl + (backUrl.indexOf('?') > -1 ? '&' : '?') + 'pay_success=1';
					console.log('跳转URL:', successUrl);
					uni.redirectTo({
						url: successUrl
					});
				},
				fail: function(err) {
					console.log('===== 小程序支付失败回调 =====');
					console.log('错误信息:', err);
					// 用户取消支付,跳转到支付状态页面
					if (err.errMsg && err.errMsg.indexOf('cancel') > -1) {
						uni.redirectTo({
							url: backUrl
						});
					} else {
						that.pageReject('支付失败', backUrl);
					}
				}
			});
			// #endif
			// #ifdef H5
			// H5微信支付
			console.log('使用H5支付');
			this.$wechat.pay(payData).then(res => {
				console.log('===== H5支付成功回调 =====');
				console.log('支付结果:', res);
				// 支付成功,跳转到支付状态页面,带上pay_success=1参数
				let successUrl = backUrl + (backUrl.indexOf('?') > -1 ? '&' : '?') + 'pay_success=1';
				console.log('跳转URL:', successUrl);
				uni.redirectTo({
					url: successUrl
				});
			}).catch(err => {
				console.log('===== H5支付失败回调 =====');
				console.log('错误信息:', err);
				if (!this.$wechat.isWeixin()) {
					this.pageReject('支付失败', backUrl);
				}
				if (err.errMsg == 'chooseWXPay:cancel') {
					// 用户取消支付,跳转到支付状态页面
					uni.redirectTo({
						url: backUrl
					});
				}
			});
			// #endif
		},
		/**
		 * H5支付处理方法
		 * 新窗口打开支付页面,当前页面跳转到支付状态页并轮询订单状态
		 */
		handleH5Pay(payUrl, backUrl) {
			console.log('===== H5支付处理 =====');
			console.log('支付URL:', payUrl);
			console.log('回调URL:', backUrl);

			uni.hideLoading();

			// 构建支付状态页URL
			let statusUrl = backUrl + (backUrl.indexOf('?') > -1 ? '&' : '?') + 'pay_success=1';

			// #ifdef H5
			// H5环境:标记支付已发起，然后直接跳转到支付结果页面等待
			console.log('H5环境:标记支付已发起，跳转到支付结果页');
			this.payInitiated = true;
			// 跳转到支付状态页，让用户在结果页面等待支付完成
			console.log('跳转到支付状态页:', statusUrl);
			uni.redirectTo({ url: statusUrl });
			// #endif

			// #ifdef APP-PLUS
			// APP环境:打开外部浏览器进行支付,然后跳转到支付结果页面轮询
			try {
				plus.runtime.openURL(payUrl);
			} catch (err) {
				console.log('openURL fail:', err);
			}

			// 标记需要跳转到支付结果页
			this.markPayRedirect();

			// 跳转到支付状态页,带上pay_success=1参数启动轮询
			console.log('跳转到支付状态页:', statusUrl);

			setTimeout(() => {
				uni.redirectTo({
					url: statusUrl
				});
			}, 300);
			// #endif
		},
		// 福利金输入框变化
		onWelfareInput(e) {
			let value = e.detail.value || '';
			let decimalPosition = value.indexOf('.');

			// 如果只有一个小数点,重置为空
			if (value === '.' || (value.length === 1 && value === '.')) {
				value = '';
			} else if (decimalPosition !== -1) {
				// 有小数点,分离整数和小数部分
				let integerPart = value.slice(0, decimalPosition);
				let decimalPart = value.slice(decimalPosition + 1);

				// 移除小数部分的非数字字符
				decimalPart = decimalPart.replace(/\D/g, '');

				// 限制小数部分最多2位
				if (decimalPart.length > 2) {
					decimalPart = decimalPart.slice(0, 2);
				}

				// 重新组装
				value = integerPart + '.' + decimalPart;

				// 首位不能是小数点
				if (integerPart === '' && decimalPart !== '') {
					value = '';
				}
			} else {
				// 没有小数点,只允许数字
				value = value.replace(/\D/g, '');
			}

			// 限制最大值
			let maxWelfare = parseFloat(this.enterpriseWelfare) || 0;
			let maxPay = parseFloat(this.payPriceShow) || 0;
			let numValue = parseFloat(value) || 0;

			if (numValue > maxWelfare) {
				value = maxWelfare.toFixed(2);
			} else if (numValue > maxPay) {
				value = maxPay.toFixed(2);
			}

			// 使用$nextTick更新数据
			this.$nextTick(() => {
				this.welfareAmount = value;
			});
		},

		// 余额输入框变化
		onBalanceInput(e) {
			let value = e.detail.value || '';
			let decimalPosition = value.indexOf('.');

			// 如果只有一个小数点,重置为空
			if (value === '.' || (value.length === 1 && value === '.')) {
				value = '';
			} else if (decimalPosition !== -1) {
				// 有小数点,分离整数和小数部分
				let integerPart = value.slice(0, decimalPosition);
				let decimalPart = value.slice(decimalPosition + 1);

				// 移除小数部分的非数字字符
				decimalPart = decimalPart.replace(/\D/g, '');

				// 限制小数部分最多2位
				if (decimalPart.length > 2) {
					decimalPart = decimalPart.slice(0, 2);
				}

				// 重新组装
				value = integerPart + '.' + decimalPart;

				// 首位不能是小数点
				if (integerPart === '' && decimalPart !== '') {
					value = '';
				}
			} else {
				// 没有小数点,只允许数字
				value = value.replace(/\D/g, '');
			}

			// 限制最大值
			let maxBalance = parseFloat(this.now_money) || 0;
			let maxPay = parseFloat(this.payPriceShow) || 0;
			let welfareUsed = (this.isEnterprise && this.welfareEnabled) ? (parseFloat(this.welfareAmount) || 0) : 0;
			let remainPay = maxPay - welfareUsed;
			let numValue = parseFloat(value) || 0;

			if (numValue > maxBalance) {
				value = maxBalance.toFixed(2);
			} else if (numValue > remainPay) {
				value = remainPay.toFixed(2);
			}

			// 使用$nextTick更新数据
			this.$nextTick(() => {
				this.balanceAmount = value;
			});
		},

		// 使用全额福利金
		useAllWelfare() {
			if (!this.welfareEnabled) return;
			let maxWelfare = parseFloat(this.enterpriseWelfare) || 0;
			let maxPay = parseFloat(this.payPriceShow) || 0;
			// 金币支持两位小数
			this.welfareAmount = Math.min(maxWelfare, maxPay).toFixed(2);
			this.welfareEnabled = true;
		},

		// 使用全额余额
		useAllBalance() {
			if (!this.balanceEnabled) return;
			let maxBalance = parseFloat(this.now_money) || 0;
			let maxPay = parseFloat(this.payPriceShow) || 0;
			let welfareUsed = (this.isEnterprise && this.welfareEnabled) ? (parseFloat(this.welfareAmount) || 0) : 0;
			let remainPay = maxPay - welfareUsed;
			this.balanceAmount = Math.min(maxBalance, remainPay).toFixed(2);
			this.balanceEnabled = true;
		},

		// 福利金开关
		onWelfareSwitch(e) {
			this.welfareEnabled = e.detail.value;
			if (!this.welfareEnabled) {
				this.welfareAmount = '';
			}
		},

		// 余额开关
		onBalanceSwitch(e) {
			this.balanceEnabled = e.detail.value;
			if (!this.balanceEnabled) {
				this.balanceAmount = '';
			}
		},

		// 金币输入框包裹层点击
		onWelfareWrapperClick(e) {
			if (!this.welfareEnabled) {
				this.$util.Tips({
					title: '请先开启金币支付开关'
				});
			}
		},

		// 余额输入框包裹层点击
		onBalanceWrapperClick(e) {
			if (!this.balanceEnabled) {
				this.$util.Tips({
					title: '请先开启余额支付开关'
				});
			}
		},

		// 企业用户组合支付
		goCombinationPay(){
			let that = this;

			// #ifdef H5
			// H5模式下：如果已经发起过支付，直接跳转到支付结果页面
			if (this.payInitiated) {
				console.log('H5组合支付已发起，直接跳转到支付结果页');
				let backUrl = '/pages/goods/order_pay_status/index?order_id=' + this.orderId + '&type=3';
				uni.redirectTo({ url: backUrl });
				return;
			}
			// #endif

			// 直接执行组合支付,不再弹窗
			that.executeCombinationPayNew();
		},

		// 执行组合支付(新版)
		executeCombinationPayNew(){
			console.log('执行组合支付(新版)');
			let that = this;

			// #ifdef H5
			// 微信内拦截提示已移到支付返回处理里
			// #endif

			// 如果是只允许微信支付的场景(only_wechat=1)，强制只使用微信支付
			// 不受 welfare_pay_status 等其他字段影响
			let welfareAmount = 0;
			let balanceAmount = 0;

			if (!this.onlyWechat) {
				// 只有在非 onlyWechat 场景下才允许使用福利金和余额
				welfareAmount = this.welfareEnabled ? (parseFloat(this.welfareAmount) || 0) : 0;
				balanceAmount = this.balanceEnabled ? (parseFloat(this.balanceAmount) || 0) : 0;
			}

			let totalPay = parseFloat(this.payPriceShow) || 0;
			let inputTotal = welfareAmount + balanceAmount;

			// 验证输入金额不超过订单金额
			if (inputTotal > totalPay) {
				return this.$util.Tips({
					title: '支付金额超过订单金额'
				});
			}

			// 验证福利金余额
			if (welfareAmount > 0 && welfareAmount > parseFloat(this.enterpriseWelfare)) {
				return this.$util.Tips({
					title: '福利金余额不足'
				});
			}

			// 验证余额
			if (balanceAmount > 0 && balanceAmount > parseFloat(this.now_money)) {
				return this.$util.Tips({
					title: '账户余额不足'
				});
			}

			uni.showLoading({
				title: '支付中'
			});

			// 判断支付方式数量
			let paymentMethodCount = 0;
			if (welfareAmount > 0) paymentMethodCount++;
			if (balanceAmount > 0) paymentMethodCount++;
			let onlineAmount = parseFloat(this.onlinePayAmount) || 0;
			if (onlineAmount > 0) paymentMethodCount++;

			// 判断支付类型
			// 组合支付：至少使用2种支付方式
			// 单一支付：只使用1种支付方式
			let isCombinationPay = paymentMethodCount >= 2;

			// 确定 paytype
			let paytype;
			if (isCombinationPay) {
				// 组合支付
				paytype = 'combination';
			} else {
				// 单一支付：判断具体是哪种
				if (welfareAmount > 0) {
					// 纯金币支付（只要使用了金币且没有其他支付方式）
					paytype = 'welfare';
				} else if (balanceAmount > 0) {
					// 纯余额支付（只要使用了余额且没有其他支付方式）
					paytype = 'yue';
				} else if (onlineAmount > 0) {
					// 纯微信支付（只使用在线支付）
					paytype = 'weixin';
				} else {
					// 默认微信支付
					paytype = 'weixin';
				}
			}

			console.log('支付方式判断:', {
				welfareAmount,
				balanceAmount,
				onlineAmount,
				paymentMethodCount,
				isCombinationPay,
				paytype
			});

			// 构建支付明细（组合支付才需要）
			let payDetail = isCombinationPay ? {
				welfare: welfareAmount,
				balance: balanceAmount,
				online_pay_type: this.onlinePayType
			} : undefined;

			// 调用支付接口
			orderPay({
				uni: that.orderId,
				paytype: paytype,  // 根据实际情况传递支付类型
				pay_detail: isCombinationPay ? payDetail : undefined,  // 只有组合支付才传 pay_detail
				// #ifdef MP
				'from': 'routine',
				// #endif
				// #ifdef H5
				'from': this.getH5PayFrom(),
				quitUrl: location.port ? location.protocol + '//' + location.hostname + ':' + location.port + '/pages/goods/order_pay_status/index?order_id=' + this.orderId : location.protocol + '//' + location.hostname +'/pages/goods/order_pay_status/index?order_id=' + this.orderId,
				// #endif
				// #ifdef APP-PLUS
				quitUrl: '/pages/goods/order_pay_status/index?order_id=' + this.orderId
				// #endif
			}).then(res=>{
				let status = res.data.status;
				let backUrl = '/pages/goods/order_pay_status/index?order_id=' + this.orderId + '&msg=' +res.msg +'&type=3' + '&totalPrice=' + this.payPriceShow;

				console.log('===== 组合支付响应 =====');
				console.log('status:', status);
				console.log('result:', res.data.result);

				switch (status) {
					case 'SUCCESS':
					case 'success':
						this.pageReject(res.msg, backUrl);
						break;
					case 'WECHAT_PAY':
					case 'wechat_pay':
						// 需要微信支付
						let jsConfig = res.data.result.jsConfig;

						// 检查是否是银联支付(嵌套在jsConfig中)
						if (jsConfig && jsConfig.status === 'UMS_MINI_PAY') {
							console.log('检测到银联小程序支付');
							this.umsWechatPayFun(jsConfig.result, backUrl);
						} else if (jsConfig && jsConfig.status === 'UMS_H5_PAY') {
							console.log('检测到银联H5支付, pay_url:', jsConfig.result.pay_url);
							// H5支付: 新窗口打开支付页面,当前页面跳转到支付状态页
							this.handleH5Pay(jsConfig.result.pay_url, backUrl);
						} else {
							// 原有的微信支付逻辑
							console.log('使用原生微信支付');
							this.wechatPayFun(res.data.result, backUrl);
						}
						break;
					case 'WECHAT_H5_PAY':
					case 'wechat_h5_pay':
						let h5JsConfig = res.data.result.jsConfig;

						// 检查是否是银联H5支付(嵌套在jsConfig中)
						if (h5JsConfig && h5JsConfig.status === 'UMS_H5_PAY') {
							console.log('检测到银联H5支付(WECHAT_H5_PAY状态), pay_url:', h5JsConfig.result.pay_url);
							// H5支付: 新窗口打开支付页面,当前页面跳转到支付状态页
							this.handleH5Pay(h5JsConfig.result.pay_url, backUrl);
						} else {
							// 原生微信H5支付
							console.log('使用原生微信H5支付');
							// #ifdef H5
							// 标记支付已发起
							this.payInitiated = true;
							// #endif
							uni.hideLoading();
							setTimeout(() => {
								location.href = res.data.result.jsConfig.mweb_url + '&redirect_url=' + window.location.protocol + '//' + window.location.host + backUrl;
							}, 500);
						}
						break;
					case 'UMS_MINI_PAY':
						// 银联小程序支付（直接状态）
						console.log('检测到银联小程序支付(直接状态)');
						console.log('支付数据结构:', res.data.result);
						// 银联支付参数在 result.result 中
						let umsPayData = res.data.result.result || res.data.result;
						this.umsWechatPayFun(umsPayData, backUrl);
						break;
					case 'UMS_H5_PAY':
						// 直接的银联H5支付
						console.log('检测到银联H5支付(直接状态), pay_url:', res.data.result.result.pay_url);
						// H5支付: 新窗口打开支付页面,当前页面跳转到支付状态页
						this.handleH5Pay(res.data.result.result.pay_url, backUrl);
						break;
					default:
						uni.hideLoading();
						this.$util.Tips({
							title: res.msg || '支付失败'
						});
						break;
				}
			}).catch(err=>{
				uni.hideLoading();
				return that.$util.Tips({
					title: err
				});
			});
		},

		pageReject(msg,backUrl){
			uni.hideLoading();
			return this.$util.Tips({
				title: msg
			}, {
				tab: 5,
				url: backUrl
			});
		}
	}
}
</script>

<style lang="scss">
.cashier-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
  .w-full {
    width: 100%;
  }

  .relative {
    position: relative;
  }

  .header-bg-container {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 0;

    .order-bg-icon {
      position: absolute;
      right: 36rpx;
      bottom: 200rpx;
      width: 120rpx;
      height: 120rpx;
      z-index: 1;
      opacity: 0.3;
    }
  }

  .white_jianbian {
    height: 120rpx;
    background: linear-gradient(0deg, #f5f5f5 0%, rgba(245, 245, 245, 0) 100%);
  }

  .pay-content {
    padding: 19rpx 0;
    position: relative;
    z-index: 1;
    margin-top: 12rpx;

    .pay-info {
      .pay-status-label {
        font-size: 36rpx;
        color: #ffffff;
        margin-bottom: 16rpx;
        opacity: 0.9;
      }

      .pay-amount-row {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 0;
        font-size: 28rpx;
        color: #fafafa;

        .pay-amount-label {
          margin-right: 8rpx;
        }

        .pay-amount {
          line-height: 1;
          margin-right: 24rpx;
        }

        .pay-time-label {
          margin-right: 8rpx;
        }

        .pay-time-text {
          font-size: 28rpx;
          opacity: 0.9;
        }
      }
    }
  }

  .pay-content-wrapper {
    padding: 0 20rpx;
    position: relative;
    z-index: 100;
  }
}

/deep/ .styleAll {
  padding: 0 6rpx;
  border: 1rpx solid #dddddd;
  border-radius: 8rpx;
}
.pay_card {
  padding: 40rpx 32rpx;
}
.pay_item ~ .pay_item {
  margin-top: 56rpx;
}
.icon-ic_unselect {
  color: #ccc;
}
.icon-a-ic_CompleteSelect {
  color: var(--view-theme);
}

/* 组合支付样式 - 新版 */
.pay_title {
  padding: 32rpx 32rpx 24rpx;
  font-size: 28rpx;
  color: #333333;
  font-weight: 500;
}
.pay_item_new {
  padding: 48rpx;
  background-color: #fff;
  margin-bottom: 32rpx;
}
.pay_icon_wrapper {
  //width: 88rpx;
  //height: 88rpx;
  //border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  scale: 1.2;
}
.pay_icon_orange {
  background: linear-gradient(135deg, #ffb84d 0%, #ff8a00 100%);
}
.pay_icon_blue {
  background: linear-gradient(135deg, #6bb4ff 0%, #3a7eff 100%);
}
.pay_icon_green {
  background: #09bb07;
}
.pay_icon_text {
  font-size: 48rpx;
  color: #ffffff;
  font-weight: bold;
}
.pay_icon_img {
  width: 56rpx;
  height: 56rpx;
}
.pay_name {
  font-size: 28rpx;
  color: #000000;
  //font-weight: 500;
  //line-height: 44rpx;
}
.pay_tips {
  font-size: 24rpx;
  color: #999999;
  //line-height: 34rpx;
  //margin-top: 4rpx;
}
.pay_input_wrapper {
  flex: 1;
  height: 80rpx;
  background: #f3f3f3;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  padding: 0;
  position: relative;
  overflow: hidden;
}
.pay_input_wrapper.disabled {
  background: #f3f3f3;
}
.pay_input_prefix {
  font-size: 28rpx;
  color: #000;
  margin-right: 8rpx;
  margin-left: 24rpx;
}
.pay_input_wrapper.disabled .pay_input_prefix {
  color: #000;
}
.pay_input_new {
  flex: 1;
  font-size: 28rpx;
  color: #000;
  background: transparent;
  border: none;
  padding: 0 24rpx;
  padding-right: 0;
}
.pay_input_wrapper.disabled .pay_input_new {
  color: #999;
}
.pay_input_new::placeholder {
  color: #999;
}
.pay_all_btn_new {
  width: 96rpx;
  height: 80rpx;
  background: var(--view-theme, #e93323);
  border-radius: 0 12rpx 12rpx 0;
  color: #ffffff;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  flex-shrink: 0;
  margin-left: auto;
}
.pay_all_btn_new.disabled {
  background: #999999;
  color: #ffffff;
  font-size: 28rpx;
}
.wx-switch-input::before {
  background: #d9d9d9 !important; /* 关闭时的背景色 */
}

/* 开关右对齐 */
.pay_item_new .flex-between-center {
  display: flex !important;
  align-items: center;
  justify-content: space-between !important;
  width: 100%;
}

.switch-wrapper {
  margin-left: auto;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  width: 100rpx;
}

.mb-24 {
  margin-bottom: 24rpx;
}
.ml-20 {
  margin-left: 20rpx;
}
.order-btn {
  background: linear-gradient(
    90deg,
    var(--view-theme, #e93323) 0,
    var(--view-gradient, #ff7931) 100%
  );
}

.bottom-enterprise {
  bottom: 80rpx;
}

.bottom-normal {
  bottom: 161rpx;
}
</style>
