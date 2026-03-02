<?php
// +----------------------------------------------------------------------
// | CRMEB [ CRMEB赋能开发者，助力企业发展 ]
// +----------------------------------------------------------------------
// | Copyright (c) 2016~2020 https://www.crmeb.com All rights reserved.
// +----------------------------------------------------------------------
// | Licensed CRMEB并不是自由软件，未经许可不能去掉CRMEB相关版权
// +----------------------------------------------------------------------
// | Author: CRMEB Team <admin@crmeb.com>
// +----------------------------------------------------------------------
namespace app\services\order;

use app\dao\order\StoreOrderRefundDao;
use app\jobs\notice\SmsAdminJob;
use app\jobs\notice\template\RoutineTemplateJob;
use app\jobs\notice\template\WechatTemplateJob;
use app\jobs\order\OrderStatusJob;
use app\services\activity\discounts\StoreDiscountsServices;
use app\services\activity\bargain\StoreBargainServices;
use app\services\activity\combination\StoreCombinationServices;
use app\services\activity\combination\StorePinkServices;
use app\services\activity\integral\StoreIntegralServices;
use app\services\activity\newcomer\StoreNewcomerServices;
use app\services\activity\seckill\StoreSeckillServices;
use app\services\BaseServices;
use app\services\activity\coupon\StoreCouponUserServices;
use app\services\message\service\StoreServiceServices;
use app\services\other\ExpressServices;
use app\services\pay\PayServices;
use app\services\product\product\StoreProductServices;
use app\services\store\SystemStoreServices;
use app\services\supplier\SystemSupplierServices;
use app\services\user\UserBillServices;
use app\services\user\UserBrokerageServices;
use app\services\user\UserMoneyServices;
use app\services\user\UserServices;
use app\services\wechat\WechatUserServices;
use crmeb\services\AliPayService;
use crmeb\services\CacheService;
use crmeb\services\FormBuilder as Form;
use crmeb\services\wechat\Payment;
use think\annotation\Inject;
use think\facade\Log;
use think\exception\ValidateException;

/**
 * 订单退款
 * Class StoreOrderRefundServices
 * @package app\services\order
 * @mixin StoreOrderRefundDao
 */
class StoreOrderRefundServices extends BaseServices
{

    /**
     * 退款方式
     * @var array|string[]
     */
    protected array $refundPriceType = [
        PayServices::WEIXIN_PAY => '原微信返还',
        PayServices::YUE_PAY => '余额账户返还',
        PayServices::OFFLINE_PAY => '线下返还',
        PayServices::ALIPAY_PAY => '原支付宝返还',
        PayServices::CASH_PAY => '现金返还',
    ];

    /**
     * 订单services
     * @var StoreOrderServices
     */
    #[Inject]
    protected StoreOrderServices $storeOrderServices;

    /**
     * @var StoreOrderRefundDao
     */
    #[Inject]
    protected StoreOrderRefundDao $dao;

    /**
     * 退款订单列表
     * @param array $where
     * @param array $with
     * @return array
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function refundList(array $where, array $with = ['user'])
    {
        $where['is_cancel'] = 0;
        $where['store_id'] = isset($where['store_id']) ? $where['store_id'] : '';
        if (isset($where['time']) && $where['time'] != '') {
            $where['time'] = is_string($where['time']) ? explode('-', $where['time']) : $where['time'];
        }
        [$page, $limit] = $this->getPageValue();
        $with = array_merge($with, ['orderShippingType']);
        $list = $this->dao->getRefundList($where, '*', $with, $page, $limit);
        $count = $this->dao->count($where);
        if ($list) {
            $siteUrl = sys_config('site_url');
            foreach ($list as &$item) {
                $item['refund'] = [];
                $item['is_all_refund'] = 1;
                $item['paid'] = 1;
                $item['add_time'] = isset($item['add_time']) ? date('Y-m-d H:i', (int)$item['add_time']) : '';
                $item['cartInfo'] = $item['cart_info'];
                if (in_array($item['refund_type'], [0, 1, 2, 4, 5])) {
                    $item['refund_status'] = 1;
                } elseif ($item['refund_type'] == 6) {
                    $item['refund_status'] = 2;
                } elseif ($item['refund_type'] == 3) {
                    $item['refund_status'] = 3;
                }
                foreach ($item['cart_info'] as $items) {
                    $item['_info'][]['cart_info'] = $items;
                }
                $item['total_num'] = $item['refund_num'];
                $item['pay_price'] = $item['refund_price'];
                $item['pay_postage'] = 0;
                if (isset($item['shipping_type']) && !in_array($item['shipping_type'], [2, 4])) {
                    $item['pay_postage'] = floatval($this->getOrderSumPrice($item['cart_info'], 'postage_price', false));
                }
                [$type, $title, $status_name, $pic, $desc] = $this->tidyOrderStatus($item);
                $item['status_name'] = [
                    'pic' => $siteUrl . $pic,
                    'status_name' => $status_name
                ];
                unset($item['cart_info']);
                $item['_status'] = [
                    '_type' => $type,
                    '_title' => $title,
                    'pic' => $siteUrl . $pic,
                    'status_name' => $status_name,
                    'desc' => $desc
                ];
            }
        }
        $data['list'] = $list;
        $data['count'] = $count;

        $supplierId = $where['supplier_id'] ?? 0;
        if ($supplierId) {
            $del_where = ['supplier_id' => $supplierId, 'is_cancel' => 0];
        } else {
            $del_where = ['store_id' => $where['store_id'], 'is_cancel' => 0];
        }
        $data['num'] = [
//            0 => ['name' => '全部', 'num' => $this->dao->count($del_where)],
            1 => ['name' => '仅退款', 'num' => $this->dao->count($del_where + ['refund_type' => 1])],
            2 => ['name' => '退货退款', 'num' => $this->dao->count($del_where + ['refund_type' => 2])],
            3 => ['name' => '拒绝退款', 'num' => $this->dao->count($del_where + ['refund_type' => 3])],
            4 => ['name' => '商品待退货', 'num' => $this->dao->count($del_where + ['refund_type' => 4])],
            5 => ['name' => '退货待收货', 'num' => $this->dao->count($del_where + ['refund_type' => 5])],
            6 => ['name' => '已退款', 'num' => $this->dao->count($del_where + ['refund_type' => 6])]
        ];
        return $data;
    }

    /**
     * 前端订单列表
     * @param array $where
     * @param array|string[] $field
     * @param array $with
     * @return mixed
     */
    public function getRefundOrderList(array $where, string $field = '*', array $with = [])
    {
        [$page, $limit] = $this->getPageValue();
        $where['is_cancel'] = 0;
        $where['is_del'] = 0;
        $data = $this->dao->getRefundList($where, $field, $with, $page, $limit);
        $siteUrl = sys_config('site_url');
        foreach ($data as &$item) {
            $item['add_time'] = isset($item['add_time']) ? date('Y-m-d H:i', (int)$item['add_time']) : '';
            $item['cartInfo'] = $item['cart_info'];
            unset($item['cart_info']);
            [$type, $title, $status_name, $pic, $desc] = $this->tidyOrderStatus($item);
            $item['_status'] = [
                '_type' => $type,
                '_title' => $title,
                'pic' => $siteUrl . $pic,
                'status_name' => $status_name,
                'desc' => $desc
            ];
        }
        return $data;
    }

    /**
     * 处理退款订单状态
     * @param array $refund
     * @return array
     */
    public function tidyOrderStatus($refund)
    {
        $path = '/statics/images/order/';
        if ($refund['is_cancel'] || $refund['is_del']) {
            $type = -1;
            $title = '已撤销';
            $status_name = '用户已撤销';
            $pic = 'refund_cancel_icon.png';
            $desc = '您已撤销售后申请，感谢您对我们的支持！';
        } else {
            if (in_array($refund['refund_type'], [0, 1, 2])) {
                $type = 0;
                $title = '申请中';
                $status_name = '商家审核中';
                $pic = 'refund_verify_icon.png';
                $desc = '退款前请与商家协商一致，有助于更好的处理售后问题，感谢您对我们的支持！';
            } else {
                switch ($refund['refund_type']) {
                    case 3://已拒绝
                        $type = 3;
                        $title = '拒绝退款';
                        $status_name = '商家已拒绝';
                        $pic = 'refund_refuse_icon.png';
                        $desc = '商家已拒绝您的申请，拒绝原因：' . $refund['refuse_reason'];
                        break;
                    case 4://待退货
                        $type = 4;
                        $title = '待退货';
                        $status_name = '商家已同意';
                        $pic = 'refund_success_icon.png';
                        $desc = '商家已确认退货退款，您尽快寄回商品！';
                        break;
                    case 5://退款中
                        $type = 5;
                        $title = '退款中';
                        $status_name = '商家收货中';
                        $pic = 'refund_success_icon.png';
                        $desc = '商家确认收货寄回商品后进行打款，请您耐心等待！';
                        break;
                    case 6://已退款
                        $type = 6;
                        $title = '已退款';
                        $status_name = '已退款完成';
                        $pic = 'refund_success_icon.png';
                        $desc = '商家已为您退款（退款单号：' . ($refund['order_id'] ?? '') . '），感谢您对我们的支持！';
                        break;
                    default:
                        $type = 0;
                        $title = '申请中';
                        $status_name = '商家审核中';
                        $pic = 'refund_verify_icon.png';
                        $desc = '退款前请与商家协商一致，有助于更好的处理售后问题，感谢您对我们的支持！';
                        break;
                }
            }
        }
        return [$type, $title, $status_name, $path . $pic, $desc];
    }

    /**
     * 订单申请退款
     * @param int $id
     * @param int $uid
     * @param array $order
     * @param array $cart_ids
     * @param int $apply_type
     * @param float $apply_price
     * @param array $refundData
     * @return mixed
     * @throws \Psr\SimpleCache\InvalidArgumentException
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function applyRefund(int $id, int $uid, $order = [], array $cart_ids = [], int $apply_type = 1, float $apply_price = 0.00, array $refundData = [], $admin = 0)
    {
        if (!$order) {
            $order = $this->storeOrderServices->get($id);
        }
        if (!$order) {
            throw new ValidateException('支付订单不存在!');
        }
        $is_now = $this->dao->getCount([
            ['store_order_id', '=', $id],
            ['refund_type', 'in', [0, 1, 2, 4, 5]],
            ['is_cancel', '=', 0],
            ['is_del', '=', 0]
        ]);
        if ($is_now) throw new ValidateException('退款处理中，请联系商家');
        if (!$this->storeOrderServices->isRefundAvailable($id)) {
            throw new ValidateException('已超过设置售后期限，请联系商家');
        }

        $refund_num = $order['total_num'];
        // 如果传入了apply_price,使用apply_price作为退款金额(支持部分退款)
        // 否则使用订单总金额(整单退款)
        $refund_price = $apply_price > 0 ? $apply_price : $order['pay_price'];
        /** @var StoreOrderCartInfoServices $storeOrderCartInfoServices */
        $storeOrderCartInfoServices = app()->make(StoreOrderCartInfoServices::class);
        //退部分
        $cartInfo = [];
        $cartInfos = $storeOrderCartInfoServices->getCartColunm(['oid' => $id], 'id,cart_id,product_type,is_support_refund,cart_num,refund_num,cart_info');
        if ($cart_ids) {
            $cartInfo = array_combine(array_column($cartInfos, 'cart_id'), $cartInfos);
            $refund_num = 0;
            foreach ($cart_ids as $cart) {
                if (!isset($cartInfo[$cart['cart_id']])) throw new ValidateException('该订单中商品不存在，请重新选择!');
                if (!$cartInfo[$cart['cart_id']]['is_support_refund'] && !$admin) {
                    throw new ValidateException('该订单中有商品不支持退款，请联系管理员');
                }
                if ($cart['cart_num'] + $cartInfo[$cart['cart_id']]['refund_num'] > $cartInfo[$cart['cart_id']]['cart_num']) {
                    throw new ValidateException('超出订单中商品数量，请重新选择!');
                }
                $refund_num = bcadd((string)$refund_num, (string)$cart['cart_num'], 0);
            }
            //总共申请多少件
            $total_num = array_sum(array_column($cart_ids, 'cart_num'));
            if ($total_num < $order['total_num']) {
                $total_price = 0;
                foreach ($cartInfos as $cart) {
                    $_info = is_string($cart['cart_info']) ? json_decode($cart['cart_info'], true) : $cart['cart_info'];
                    $total_price = bcadd((string)$total_price, bcmul((string)($_info['truePrice'] ?? 0), (string)$cart['cart_num'], 4), 2);
                }
                //订单实际支付金额
                $order_pay_price = bcadd((string)$total_price, (string)$order['pay_postage'], 2);

                /** @var StoreOrderSplitServices $storeOrderSpliteServices */
                $storeOrderSpliteServices = app()->make(StoreOrderSplitServices::class);
                $cartInfos = $storeOrderSpliteServices->getSplitOrderCartInfo($id, $cart_ids, $order);
                $total_price = $pay_postage = 0;
                foreach ($cartInfos as $cart) {
                    $_info = is_string($cart['cart_info']) ? json_decode($cart['cart_info'], true) : $cart['cart_info'];
                    $total_price = bcadd((string)$total_price, bcmul((string)($_info['truePrice'] ?? 0), (string)$cart['cart_num'], 4), 2);
                    if (!in_array($order['shipping_type'], [2, 4])) {
                        $pay_postage = bcadd((string)$pay_postage, (string)($_info['postage_price'] ?? 0), 2);
                    }
                }
                //实际退款金额
                $refund_pay_price = bcadd((string)$total_price, (string)$pay_postage, 2);
                $refund_price = $refund_pay_price;
                if (isset($order['change_price']) && (float)$order['change_price']) {//有改价 且是拆分
                    //订单原实际支付金额
                    $order_pay_price = bcadd((string)$order['change_price'], (string)$order['pay_price'], 2);
                    if ($order_pay_price) {
                        $refund_price = bcmul((string)bcdiv((string)$order['pay_price'], (string)$order_pay_price, 4), (string)$refund_pay_price, 2);
                    }
                }
            }
        } else {//整单退款
            foreach ($cartInfos as $cart) {
                if (!$cart['is_support_refund'] && !$admin) {
                    throw new ValidateException('该订单中有商品不支持退款，请联系管理员');
                }
                if ($cart['refund_num'] > 0) {
                    throw new ValidateException('超出订单中商品数量，请重新选择!');
                }
            }
        }
        if ($apply_price > $refund_price) {
            throw new ValidateException("退款金额（{$apply_price}元）超过可退金额（{$refund_price}元），请调整退款金额");
        }
        foreach ($cartInfos as &$cart) {
            $cart['cart_info'] = is_string($cart['cart_info']) ? json_decode($cart['cart_info'], true) : $cart['cart_info'];
        }
        $refundData['uid'] = $uid;
        $refundData['store_id'] = $order['store_id'];
        $refundData['supplier_id'] = $order['supplier_id'];
        $refundData['store_order_id'] = $id;
$refundData['refund_num'] = $refund_num;
        $refundData['apply_type'] = $apply_type;
        $refundData['refund_goods_type'] = in_array($apply_type, [2, 3]) ? $apply_type : 1;
        $refundData['apply_price'] = $apply_price;
        $refundData['refund_price'] = $refund_price;
        $refundData['refunded_price'] = '0.00';
        $refundData['order_id'] = app()->make(StoreOrderCreateServices::class)->getNewOrderId('');
        $refundData['add_time'] = time();
        $refundData['cart_info'] = json_encode(array_column($cartInfos, 'cart_info'));
        $refundData['channel'] = $order['channel'];
        $refundId = $this->transaction(function () use ($id, $order, $cart_ids, $refundData, $storeOrderCartInfoServices, $cartInfo, $cartInfos, $admin, $apply_price) {
            $change_message = $admin ? '管理员操作退款，原因：' . $refundData['refund_explain'] ?? '无;退款金额:' . $apply_price . ';操作人:' . $admin : '用户申请退款，原因：' . $refundData['refund_reason'] ?? '无';
            $change_manager_type = $admin ? 'admin' : 'user';
            OrderStatusJob::dispatch([$order['id'], 'apply_refund', ['change_message' => $change_message, 'change_manager_type' => $change_manager_type]]);
            $res1 = true;
            $res2 = true;
            //添加退款数据
            /** @var StoreOrderRefundServices $storeOrderRefundServices */
            $storeOrderRefundServices = app()->make(StoreOrderRefundServices::class);
            $res3 = $storeOrderRefundServices->save($refundData);
            if (!$res3) {
                throw new ValidateException('添加退款申请失败');
            }
            $res4 = true;
            if ($cart_ids) {
                //修改订单商品退款信息
                foreach ($cart_ids as $cart) {
                    $res4 = $res4 && $storeOrderCartInfoServices->update(['oid' => $id, 'cart_id' => $cart['cart_id']], ['refund_num' => (($cartInfo[$cart['cart_id']]['refund_num'] ?? 0) + $cart['cart_num'])]);
                }
            } else {//整单退款
                //修改原订单状态
//                $res2 = false !== $this->storeOrderServices->update(['id' => $order['id']], ['refund_status' => 1]);
                foreach ($cartInfos as $cart) {
                    $res4 = $res4 && $storeOrderCartInfoServices->update(['oid' => $id, 'cart_id' => $cart['cart_id']], ['refund_num' => $cart['cart_num']]);
                }
            }
            if ($res1 && $res2 && $res3 && $res4) {
                return (int)$res3->id;
            } else {
                return false;
            }
        });
        $storeOrderCartInfoServices->clearOrderCartInfo($order['id']);
        //申请退款事件
        event('order.applyRefund', [$order, $refundId]);
        return $refundId;
    }

    /**
     * 再次申请退款
     * @param int $uid
     * @param string $order_id
     * @return bool|\think\Response
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function againRefundOrder(int $uid, int $id)
    {
        $orderRefund = $this->dao->get(['id' => $id, 'is_cancel' => 0, 'is_del' => 0]);
        if (!$orderRefund || $orderRefund['uid'] != $uid) {
            throw new ValidateException('订单不存在');
        }
        $refundData = [
            'refund_reason' => $orderRefund['refund_reason'],
            'refund_explain' => $orderRefund['refund_explain'],
            'refund_img' => $orderRefund['refund_img'] ? (is_array($orderRefund['refund_img']) ? json_encode($orderRefund['refund_img']) : $orderRefund) : '',
        ];
        $cart_ids = [];
        if ($orderRefund['cart_info']) {
            $cart_info = is_string($orderRefund['cart_info']) ? json_decode($orderRefund['cart_info']) : $orderRefund['cart_info'];
            foreach ($cart_info as $item) {
                $cart_ids[] = ['cart_id' => $item['id'], 'cart_num' => $item['cart_num']];
            }
        }
        $applyPrice = (float)$orderRefund['apply_price'];
        //再次申请
        $this->applyRefund((int)$orderRefund['store_order_id'], $uid, [], $cart_ids, (int)$orderRefund['apply_type'], $applyPrice, $refundData);
        return true;
    }


    /**
     * 拒绝退款
     * @param int $id
     * @param array $data
     * @param array $orderRefundInfo
     * @return bool
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function refuseRefund(int $id, array $data, $orderRefundInfo = [])
    {
        if (!$orderRefundInfo) {
            $orderRefundInfo = $this->dao->get(['id' => $id, 'is_cancel' => 0]);
        }
        if (!$orderRefundInfo) {
            throw new ValidateException('售后订单不存在');
        }
        $this->transaction(function () use ($id, $orderRefundInfo, $data) {
            //处理售后订单
            if (isset($data['refund_price'])) unset($data['refund_price']);
            $this->dao->update($id, $data);
            //处理订单
            $oid = (int)$orderRefundInfo['store_order_id'];
            $this->storeOrderServices->update($oid, ['refund_status' => 0, 'refund_type' => 3]);
            //处理订单商品cart_info
            $this->cancelOrderRefundCartInfo($id, $oid, $orderRefundInfo);
            //记录
            OrderStatusJob::dispatch([$id, 'refund_n', ['change_message' => '不退款原因:' . ($data['refund_reason'] ?? $data['refuse_reason'] ?? ''), 'change_manager_id' => request()->adminId(), 'change_manager_type' => 'admin']]);
        });
        $orderInfo = $this->storeOrderServices->get((int)$orderRefundInfo['store_order_id']);
        //订单拒绝退款事件
        event('order.refuseRefund', [$orderInfo]);
        return true;
    }

    /**
     * 取消申请退款
     * @param int $uid
     * @param string $order_id
     * @return bool|\think\Response
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function cancelApplyRefund(int $uid, string $order_id)
    {
        $orderRefund = $this->dao->get(['order_id' => $order_id, 'is_cancel' => 0]);
        if (!$orderRefund || $orderRefund['uid'] != $uid) {
            throw new ValidateException('订单不存在');
        }
        if (!in_array($orderRefund['refund_type'], [0, 1, 2, 4, 5])) {
            throw new ValidateException('当前状态不能取消申请');
        }
        $this->transaction(function () use ($uid, $orderRefund) {
            $this->dao->update($orderRefund['id'], ['is_cancel' => 1]);
            $this->cancelOrderRefundCartInfo((int)$orderRefund['id'], (int)$orderRefund['store_order_id'], $orderRefund);

            OrderStatusJob::dispatch([$orderRefund['store_order_id'], 'cancel_apply_refund', ['change_message' => '用户取消申请退款', 'change_manager_type' => 'user', 'change_manager_id' => $orderRefund['uid']]]);

        });
        return true;
    }

    /**
     * 取消申请、后台拒绝处理cart_info refund_num数据
     * @param int $id
     * @param int $oid
     * @param array $orderRefundInfo
     * @return bool
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function cancelOrderRefundCartInfo(int $id, int $oid, $orderRefundInfo = [])
    {
        if (!$orderRefundInfo) {
            $orderRefundInfo = $this->dao->get(['id' => $id, 'is_cancel' => 0]);
        }
        if (!$orderRefundInfo) {
            throw new ValidateException('售后订单不存在');
        }
        $cart_ids = array_column($orderRefundInfo['cart_info'], 'id');
        /** @var StoreOrderCartInfoServices $storeOrderCartInfoServices */
        $storeOrderCartInfoServices = app()->make(StoreOrderCartInfoServices::class);
        $cartInfos = $storeOrderCartInfoServices->getColumn([['oid', '=', $oid], ['cart_id', 'in', $cart_ids]], 'cart_id,refund_num', 'cart_id');
        foreach ($orderRefundInfo['cart_info'] as $cart) {
            $cart_refund_num = $cartInfos[$cart['id']]['refund_num'] ?? 0;
            if ($cart['cart_num'] >= $cart_refund_num) {
                $refund_num = 0;
            } else {
                $refund_num = bcsub((string)$cart_refund_num, (string)$cart['cart_num'], 0);
            }
            $storeOrderCartInfoServices->update(['oid' => $oid, 'cart_id' => $cart['id']], ['refund_num' => $refund_num]);
        }
        $storeOrderCartInfoServices->clearOrderCartInfo($oid);
        // 推送订单
        event('out.outPush', ['refund_cancel_push', ['order_id' => (int)$orderRefundInfo['id']]]);
        return true;
    }

    /**
     * 商家同意退货退款，等待客户退货
     * @param int $id
     * @return bool
     */
    public function agreeRefundProdcut(int $id)
    {
        $refundOrder = $this->dao->get($id);
        if (!$refundOrder) {
            throw new ValidateException('订单不存在');
        }
        $res = $this->dao->update(['id' => $id], ['refund_type' => 4]);
        OrderStatusJob::dispatch([$refundOrder['store_order_id'], 'refund_express', ['change_message' => '等待用户退货', 'change_manager_id' => request()->adminId(), 'change_manager_type' => 'admin']]);
        if ($res) return true;
        throw new ValidateException('操作失败');
    }

    /**
     * 同意退款：拆分退款单、退积分、佣金等
     * @param int $id
     * @param array $refundData
     * @return bool
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function agreeRefund(int $id, array $refundData, string $admin = '')
    {
        // 用于存储福利金退款金额,需要在事务外部使用
        $refundWelfareAmount = 0;

        // 在退款前检查订单是否已有划付记录
        $refundOrderInfo = $this->dao->get($id);

        // 验证退款金额必须大于0（除了0元订单的情况）
        // 注意：0元订单在控制器层已处理，这里只做兜底验证
        if (!isset($refundData['refund_price']) || bccomp((string)($refundData['refund_price'] ?? 0), '0', 2) <= 0) {
            // 检查订单是否为0元订单
            if ($refundOrderInfo && $refundOrderInfo['store_order_id']) {
                $orderInfo = $this->storeOrderServices->get((int)$refundOrderInfo['store_order_id']);
                if ($orderInfo && bccomp((string)($orderInfo['pay_price'] ?? 0), '0', 2) > 0) {
                    // 非0元订单，退款金额必须大于0
                    Log::error("退款金额验证失败: refund_price={$refundData['refund_price']}, 订单pay_price={$orderInfo['pay_price']}");
                    throw new ValidateException('退款金额必须大于0');
                }
            }
        }
        if ($refundOrderInfo && $refundOrderInfo['store_order_id']) {
            $preCheckOrder = $this->storeOrderServices->get((int)$refundOrderInfo['store_order_id']);
            if ($preCheckOrder) {
                $preCheckOrder = is_array($preCheckOrder) ? $preCheckOrder : $preCheckOrder->toArray();

                // 确定要检查的订单号(子订单检查自己，主订单检查主订单及其子订单)
                $checkOrderNo = $preCheckOrder['order_id'];
                $checkOrderId = $preCheckOrder['id'];
                if ($preCheckOrder['pid'] > 0) {
                    // 如果是子订单，检查子订单本身的划付记录
                    $checkOrderNo = $preCheckOrder['order_id'];
                    $checkOrderId = $preCheckOrder['id'];
                }

                // 使用内联代码检查划付记录
                /** @var \app\dao\pay\WechatTransferOrderDao $transferOrderDao */
                $transferOrderDao = app()->make(\app\dao\pay\WechatTransferOrderDao::class);

                // 只检查状态为success的划付记录
                $hasSupplierTransfer = $transferOrderDao->existsByOrderNoTypeAndStatuses(
                    $checkOrderNo, 'supplier', ['pending', 'processing', 'success']

                );
                $hasPlatformTransfer = $transferOrderDao->existsByOrderNoTypeAndStatuses(
                    $checkOrderNo, 'platform', ['pending', 'processing', 'success']
                );

                // 如果是主订单，还需要检查子订单的划付记录
                $hasSubOrderTransfer = false;
                if ($checkOrderId > 0) {
                    $subOrders = $this->storeOrderServices->getColumn(['pid' => $checkOrderId], 'order_id');
                    foreach ($subOrders as $subOrderNo) {
                        $subSupplierTransfer = $transferOrderDao->existsByOrderNoTypeAndStatuses(
                            $subOrderNo, 'supplier', ['success']
                        );
                        $subPlatformTransfer = $transferOrderDao->existsByOrderNoTypeAndStatuses(
                            $subOrderNo, 'platform', ['success']
                        );
                        if ($subSupplierTransfer || $subPlatformTransfer) {
                            $hasSubOrderTransfer = true;
                            Log::info("子订单已有成功划付记录: sub_order_no={$subOrderNo}");
                            break;
                        }
                    }
                }

                $hasTransfer = $hasSupplierTransfer || $hasPlatformTransfer || $hasSubOrderTransfer;
                if ($hasTransfer) {
                    Log::warning("退款订单已有划付记录，阻止退款: order_no={$checkOrderNo}, refund_id={$id}, supplier={$hasSupplierTransfer}, platform={$hasPlatformTransfer}, sub_order={$hasSubOrderTransfer}");
                    throw new ValidateException('该订单已有划付记录，无法退款');
                }
            }
        }

        $order = $this->transaction(function () use ($id, &$refundData, $admin, &$refundWelfareAmount) {
            //退款拆分
            $orderModel = $this->agreeSplitRefundOrder($id);

            // 将模型对象转换为数组(用于大部分逻辑)
            $order = is_array($orderModel) ? $orderModel : $orderModel->toArray();

            // 计算应返还的福利金金额(在事务内计算,确保数据一致性)
            $refundWelfareAmount = $this->calculateRefundWelfareAmount($order, $refundData['refund_price'] ?? 0);
            $refundData['refund_welfare_price'] = $refundWelfareAmount;

            // 更新退款单的福利金返还金额
            $this->dao->update($id, ['refund_welfare_price' => $refundWelfareAmount]);

            //回退积分和优惠卷(需要模型对象)
            if (!$this->integralAndCouponBack($orderModel)) {
                throw new ValidateException('回退积分和优惠卷失败');
            }
            //退拼团
            if ($order['pid'] == 0 && $order['type'] == 3) {
                /** @var StorePinkServices $pinkServices */
                $pinkServices = app()->make(StorePinkServices::class);
                if (!$pinkServices->setRefundPink($order)) {
                    throw new ValidateException('拼团修改失败!');
                }
            }
            //退佣金
            /** @var UserBrokerageServices $userBrokerageServices */
            $userBrokerageServices = app()->make(UserBrokerageServices::class);
            if (!$userBrokerageServices->orderRefundBrokerageBack($order)) {
                throw new ValidateException('回退佣金失败');
            }
            //回退库存
            if ($order['status'] == 0) {
                /** @var StoreOrderStatusServices $services */
                $services = app()->make(StoreOrderStatusServices::class);
                if (!$services->count(['oid' => $order['id'], 'change_type' => 'refund_price'])) {
                    $this->regressionStock($order);
                }
            }
            //退金额
            if ($refundData['refund_price'] > 0) {
                if (!isset($refundData['refund_id']) || !$refundData['refund_id']) {
                    mt_srand();
                    $refundData['refund_id'] = $order['order_id'] . rand(100, 999);
                }
                if ($order['pid'] > 0) {//子订单
                    $refundOrder = $this->storeOrderServices->get((int)$order['pid']);
                    // 将模型对象转换为数组
                    $refundOrder = is_array($refundOrder) ? $refundOrder : $refundOrder->toArray();
                    $refundData['pay_price'] = $refundOrder['pay_price'];
                } else {
                    // $order 已经在第579行转换为数组了
                    $refundOrder = $order;
                }

                Log::info('开始处理退款: ' . json_encode([
                    'order_id' => $refundOrder['id'] ?? 'unknown',
                    'order_no' => $refundOrder['order_id'] ?? 'unknown',
                    'pay_type' => $refundOrder['pay_type'] ?? 'unknown',
                    'pay_price' => $refundOrder['pay_price'] ?? 'unknown',
                    'online_pay_price' => $refundOrder['online_pay_price'] ?? 'unknown',
                    'balance_pay_price' => $refundOrder['balance_pay_price'] ?? 'unknown',
                    'welfare_pay_price' => $refundOrder['welfare_pay_price'] ?? 'unknown',
                    'pay_type_detail' => $refundOrder['pay_type_detail'] ?? 'empty',
                    'refund_price' => $refundData['refund_price'] ?? 'unknown',
                ], JSON_UNESCAPED_UNICODE));

                // 处理组合支付退款
                // 判断是否是组合支付:
                // 1. pay_type = 'combination' (最准确的判断)
                // 2. 或者至少有两种支付方式的金额 > 0
                $paymentMethodCount = 0;
                if (isset($refundOrder['online_pay_price']) && $refundOrder['online_pay_price'] > 0) {
                    $paymentMethodCount++;
                }
                if (isset($refundOrder['balance_pay_price']) && $refundOrder['balance_pay_price'] > 0) {
                    $paymentMethodCount++;
                }
                if (isset($refundOrder['welfare_pay_price']) && $refundOrder['welfare_pay_price'] > 0) {
                    $paymentMethodCount++;
                }

                $isCombinationPay = ($refundOrder['pay_type'] === 'combination') || ($paymentMethodCount >= 2);

                if ($isCombinationPay) {
                    Log::info('检测到组合支付订单,进入组合支付退款流程, pay_type: ' . ($refundOrder['pay_type'] ?? 'unknown'));

                    // 组合支付退款顺序:
                    // 1. 先退余额(事务内,可回滚)
                    // 2. 再退在线支付(第三方接口,不可回滚)
                    // 3. 最后退福利金(监听器处理)

                    // ========== 第一步: 按比例计算各支付方式的退款金额 ==========
                    $refundRatio = bcdiv((string)$refundData['refund_price'], (string)$refundOrder['pay_price'], 4);
                    Log::info('退款比例: ' . $refundRatio);

                    // 获取各支付方式的实际支付金额
                    $welfarePayPrice = $refundOrder['welfare_pay_price'] ?? 0;
                    $balancePayPrice = $refundOrder['balance_pay_price'] ?? 0;
                    $onlinePayPrice = $refundOrder['online_pay_price'] ?? 0;

                    // 计算福利金退款金额
                    $welfareRefundAmount = '0.00';
                    if ($welfarePayPrice > 0) {
                        $welfareRefundAmount = bcmul((string)$welfarePayPrice, $refundRatio, 2);
                        Log::info('福利金按比例计算: ' . $welfareRefundAmount . ' 元');
                    }

                    // 计算余额退款金额
                    $balanceRefundAmount = '0.00';
                    if ($balancePayPrice > 0) {
                        $balanceRefundAmount = bcmul((string)$balancePayPrice, $refundRatio, 2);
                        Log::info('余额按比例计算: ' . $balanceRefundAmount . ' 元');
                    }

                    // 计算在线支付退款金额
                    $onlineRefundAmount = '0.00';
                    if ($onlinePayPrice > 0) {
                        $onlineRefundAmount = bcmul((string)$onlinePayPrice, $refundRatio, 2);
                        Log::info('在线支付按比例计算: ' . $onlineRefundAmount . ' 元');
                    }

                    // ========== 第二步: 处理精度问题 - 确保有支付的方式能分到退款 ==========
                    // 当某个支付方式有实际支付金额，但按比例计算结果为0时，给它分配最小金额0.01元
                    $minAmount = '0.01';
                    $remainingRefund = (string)$refundData['refund_price'];

                    // 先处理小额支付方式（余额和福利金），确保它们能分到退款
                    // 优先级：余额 > 福利金（因为余额是用户自己的钱）
                    if ($balancePayPrice > 0 && bccomp($balanceRefundAmount, '0', 2) <= 0) {
                        // 余额有支付但计算结果为0，检查是否还有足够的退款金额
                        if (bccomp($remainingRefund, $minAmount, 2) >= 0) {
                            $balanceRefundAmount = $minAmount;
                            $remainingRefund = bcsub($remainingRefund, $minAmount, 2);
                            Log::info('余额精度补偿: 分配最小金额 ' . $minAmount . ' 元');
                        }
                    }

                    if ($welfarePayPrice > 0 && bccomp($welfareRefundAmount, '0', 2) <= 0) {
                        // 福利金有支付但计算结果为0，检查是否还有足够的退款金额
                        if (bccomp($remainingRefund, $minAmount, 2) >= 0) {
                            $welfareRefundAmount = $minAmount;
                            $remainingRefund = bcsub($remainingRefund, $minAmount, 2);
                            Log::info('福利金精度补偿: 分配最小金额 ' . $minAmount . ' 元');
                        }
                    }

                    // ========== 第三步: 计算差额并补偿到在线支付 ==========
                    // 计算三种支付方式的总和
                    $calculatedTotal = bcadd(bcadd($welfareRefundAmount, $balanceRefundAmount, 2), $onlineRefundAmount, 2);
                    Log::info('计算总和: ' . $calculatedTotal . ' 元');

                    // 计算差额
                    $diff = bcsub((string)$refundData['refund_price'], $calculatedTotal, 2);
                    Log::info('差额: ' . $diff . ' 元');

                    // 如果有正差额，补偿到在线支付（因为在线支付金额通常最大）
                    if (bccomp($diff, '0', 2) > 0) {
                        Log::info('检测到正差额 ' . $diff . ' 元,补偿到在线支付...');
                        $onlineRefundAmount = bcadd($onlineRefundAmount, $diff, 2);
                        Log::info('差额补偿到在线支付,调整后: ' . $onlineRefundAmount . ' 元');
                    } elseif (bccomp($diff, '0', 2) < 0) {
                        // 如果有负差额（计算总额超过应退金额），从在线支付中扣除
                        Log::info('检测到负差额 ' . $diff . ' 元,从在线支付中扣除...');
                        $onlineRefundAmount = bcadd($onlineRefundAmount, $diff, 2);
                        if (bccomp($onlineRefundAmount, '0', 2) < 0) {
                            $onlineRefundAmount = '0.00';
                        }
                        Log::info('调整后在线支付退款: ' . $onlineRefundAmount . ' 元');
                    }

                    // 确保各退款金额不超过对应的支付金额
                    if (bccomp($welfareRefundAmount, (string)$welfarePayPrice, 2) > 0) {
                        $welfareRefundAmount = (string)$welfarePayPrice;
                        Log::info('福利金退款金额超限,调整为: ' . $welfareRefundAmount . ' 元');
                    }
                    if (bccomp($balanceRefundAmount, (string)$balancePayPrice, 2) > 0) {
                        $balanceRefundAmount = (string)$balancePayPrice;
                        Log::info('余额退款金额超限,调整为: ' . $balanceRefundAmount . ' 元');
                    }
                    if (bccomp($onlineRefundAmount, (string)$onlinePayPrice, 2) > 0) {
                        $onlineRefundAmount = (string)$onlinePayPrice;
                        Log::info('在线支付退款金额超限,调整为: ' . $onlineRefundAmount . ' 元');
                    }

                    // 验证补偿后的总额
                    $finalTotal = bcadd(bcadd($welfareRefundAmount, $balanceRefundAmount, 2), $onlineRefundAmount, 2);
                    Log::info('补偿后总额: ' . $finalTotal . ' 元, 应退款: ' . $refundData['refund_price'] . ' 元');
                    
                    if (bccomp($finalTotal, $refundData['refund_price'], 2) > 0) {
                        Log::error('❌ 退款金额计算异常: 计算总额(' . $finalTotal . ')大于应退款金额(' . $refundData['refund_price'] . ')');
                        throw new ValidateException('退款金额计算异常，请联系客服');
                    }

                    // ========== 第三步: 执行退款 ==========
                    // 组合支付:处理余额退款部分(如果有)
                    if (bccomp($balanceRefundAmount, '0', 2) > 0) {
                        Log::info('开始处理余额退款,金额: ' . $balanceRefundAmount . ' 元');

                        // 临时修改退款金额为余额部分
                        $originalRefundPrice = $refundData['refund_price'];
                        $refundData['refund_price'] = $balanceRefundAmount;

                        // 执行余额退款
                        if (!$this->yueRefund($refundOrder, $refundData)) {
                            Log::info('余额退款失败!');
                            throw new ValidateException('余额退款失败');
                        }
                        Log::info('余额退款成功!');

                        // 恢复原始退款金额
                        $refundData['refund_price'] = $originalRefundPrice;
                    }

                    // 组合支付:处理在线支付部分(如果有)
                    if (bccomp($onlineRefundAmount, '0', 2) > 0) {
                        Log::info('开始处理在线支付退款,金额: ' . $onlineRefundAmount . ' 元');

                        // 临时保存计算好的在线支付退款金额
                        $refundData['_calculated_online_refund_amount'] = $onlineRefundAmount;

                        $this->handleOnlinePayRefund($refundOrder, $refundData);
                        Log::info('在线支付退款完成!');
                    }

                    // 保存福利金退款金额(福利金退款由监听器统一处理)
                    if (bccomp($welfareRefundAmount, '0', 2) > 0) {
                        Log::info('保存福利金退款金额: ' . $welfareRefundAmount . ' 元');
                        $refundData['refund_welfare_price'] = $welfareRefundAmount;
                    }

                    // 保存各支付方式的实际退款金额，供供应商分账使用
                    // 这样供应商分账时可以准确知道每种支付方式退了多少钱
                    $refundData['refund_amounts'] = [
                        'welfare' => $welfareRefundAmount,
                        'balance' => $balanceRefundAmount,
                        'online' => $onlineRefundAmount,
                    ];
                    Log::info('保存各支付方式实际退款金额: ' . json_encode($refundData['refund_amounts']));

                    Log::info('组合支付退款流程完成,福利金将由监听器处理');
                } else {
                    // 单一支付方式
                    Log::info('进入单一支付方式退款流程,pay_type: ' . ($refundOrder['pay_type'] ?? 'unknown'));
                    switch ($refundOrder['pay_type']) {
                        case PayServices::WEIXIN_PAY:
                            Log::info('匹配到微信支付退款 case');
                            $no = $refundOrder['order_id'];
                            if ($refundOrder['trade_no'] && $refundOrder['trade_no'] != $refundOrder['order_id']) {
                                $no = $refundOrder['trade_no'];
                                $refundData['type'] = 'trade_no';
                            }
                            if ($refundOrder['is_channel'] == 1) {
                                //小程序退款
                                //判断是不是小程序支付 TODO 之后可根据订单判断
                                $pay_routine_open = (bool)sys_config('pay_routine_open', 0);
                                if ($pay_routine_open) {
                                    $refundData['refund_no'] = $refundOrder['order_id'];  // 退款订单号
                                    /** @var WechatUserServices $wechatUserServices */
                                    $wechatUserServices = app()->make(WechatUserServices::class);
                                    $refundData['open_id'] = $wechatUserServices->value(['uid' => (int)$order['uid']], 'openid');
                                    //判断订单是不是重新支付订单
                                    if (in_array(substr($refundOrder['unique'], 0, 2), ['wx', 'cp', 'hy', 'cz'])) {
                                        $refundData['routine_order_id'] = $refundOrder['unique'];
                                    } else {
                                        $refundData['routine_order_id'] = $refundOrder['order_id'];
                                    }
                                    $refundData['pay_routine_open'] = true;
                                }
                                Payment::instance()->setAccessEnd(Payment::MINI)->payOrderRefund($no, $refundData);//小程序
                            } else {
                                if (!sys_config('wechat_appid')) {
                                    //APP退款
                                    Payment::instance()->setAccessEnd(Payment::APP)->payOrderRefund($no, $refundData);//APP
                                } else {
                                    //微信公众号退款
                                    Payment::instance()->setAccessEnd(Payment::WEB)->payOrderRefund($no, $refundData);//公众号
                                }
                            }
                            break;
                        case 'routine':
                        case 'weixinh5':
                        case 'ums':
                            // 银联商务支付退款
                            Log::info('匹配到银联支付退款 case, pay_type: ' . ($refundOrder['pay_type'] ?? 'unknown'));
                            // 银联退款订单号使用累计方式: 订单号_R退款次数
                            if (isset($refundData['refund_id']) && $refundData['refund_id']) {
                                $refund_id = $refundData['refund_id'];
                            } else {
                                $umsRefundCount = $this->dao->getCount([['order_id', 'like', $refundOrder['order_id'] . '%']]);
                                $refund_id = $refundOrder['order_id'] . '_R' . ($umsRefundCount + 1);
                                Log::info("生成银联退款订单号: order_id={$refundOrder['order_id']}, refund_count={$umsRefundCount}, refund_id={$refund_id}");
                            }

                            // 使用实际支付单号（如果有的话）
                            // 注意: actual_pay_order_id 可能是空字符串,需要用 empty() 检查
                            // 如果 actual_pay_order_id 为空,使用 order_id + pay_attempt_count 构建
                            if (!empty($refundOrder['actual_pay_order_id'])) {
                                $actualPayOrderId = $refundOrder['actual_pay_order_id'];
                            } else {
                                $payAttemptCount = $refundOrder['pay_attempt_count'] ?? 1;
                                $actualPayOrderId = $refundOrder['order_id'] . '_' . $payAttemptCount;
                            }
                            
                            // 确保支付单号格式正确：如果支付单号已经有3HD3前缀，直接使用；否则让UmsPayService内部处理
                            if (str_starts_with($actualPayOrderId, '3HD3')) {
                                // 已经有前缀，直接使用
                                $formattedActualPayOrderId = $actualPayOrderId;
                            } else {
                                // 没有前缀，让UmsPayService内部处理（仅在生产环境中添加）
                                $formattedActualPayOrderId = $actualPayOrderId;
                            }

                            // 判断是否是H5支付
                            $isH5 = $this->isH5Payment($refundOrder);
                            $instMid = $isH5 ? 'H5DEFAULT' : '';

                            // 根据支付类型实例化对应配置的UmsPayService
                            $paymentType = $isH5 ? 'h5' : 'mini';
                            Log::info('退款使用配置类型: ' . $paymentType);

                            // 构建分账退款参数
                            $divisionRefundData = $this->buildRefundDivisionData($refundOrder, $refundData['refund_price']);

                            Log::info("银联退款参数 - 业务订单号: " . $refundOrder['order_id'] . ", 实际支付单号: " . $actualPayOrderId . ", 退款单号: " . $refund_id . ", 订单总金额: " . $refundData['pay_price'] . ", 退款金额: " . $refundData['refund_price'] . ", instMid: " . $instMid);
                            if (!empty($divisionRefundData)) {
                                Log::info('分账退款数据: ' . json_encode($divisionRefundData, JSON_UNESCAPED_UNICODE));
                            }

                            try {
                                // 使用支付类型参数实例化,确保退款时的mid/tid与支付时一致
                                $umsPay = new \crmeb\services\UmsPayService($paymentType);
                                
                                // 确保退款订单号格式正确：如果退款订单号已经有3HD3前缀，直接使用；否则让UmsPayService内部处理
                                if (str_starts_with($refund_id, '3HD3')) {
                                    $formattedRefundId = $refund_id;
                                } else {
                                    $formattedRefundId = $refund_id;
                                }
                                
                                $refundResult = $umsPay->refund(
                                    $formattedActualPayOrderId,          // 使用格式化后的实际支付单号
                                    $formattedRefundId,                  // 使用格式化后的退款订单号
                                    (string)$refundData['pay_price'],   // 订单总金额
                                    (string)$refundData['refund_price'],// 退款金额
                                    '订单退款',                          // 退款原因
                                    $divisionRefundData,                // 分账退款数据
                                    $instMid                            // H5支付需要传instMid
                                );
                                Log::info('银联退款返回结果: ' . json_encode($refundResult, JSON_UNESCAPED_UNICODE));
                                Log::info('银联退款调用成功');
                            } catch (\Exception $e) {
                                Log::info('银联退款调用失败: ' . $e->getMessage());
                                Log::info('异常堆栈: ' . $e->getTraceAsString());

                                // 提取银联返回的错误信息
                                $errorMsg = $e->getMessage();
                                $userFriendlyMsg = '退款失败，请联系客服处理';

                                if (str_contains($errorMsg, '已退') && str_contains($errorMsg, '还可退')) {
                                    $userFriendlyMsg = $errorMsg;
                                } elseif (str_contains($errorMsg, '退货金额校验不通过')) {
                                    $userFriendlyMsg = $errorMsg;
                                } elseif (str_contains($errorMsg, '子商户')) {
                                    $userFriendlyMsg = $errorMsg;
                                }

                                Log::error('银联退款失败,用户可见错误信息: ' . $userFriendlyMsg);
                                throw new ValidateException($userFriendlyMsg);
                            }
                            break;
                        case PayServices::YUE_PAY:
                            //余额退款
                            Log::info('匹配到余额支付退款 case');
                            if (!$this->yueRefund($refundOrder, $refundData)) {
                                throw new ValidateException('余额退款失败');
                            }
                            break;
                        case PayServices::ALIPAY_PAY:
                            Log::info('匹配到支付宝支付退款 case');
                            mt_srand();
                            $refund_id = $refundData['refund_id'] ?? $refundOrder['order_id'] . rand(100, 999);
                            //支付宝退款
                            AliPayService::instance()->refund(strpos($refundOrder['trade_no'], '_') !== false ? $refundOrder['trade_no'] : $refundOrder['order_id'], floatval($refundData['refund_price']), $refund_id);
                            break;
                        case PayServices::WELFARE_PAY:
                            // 福利金支付:不需要在这里处理退款,由监听器统一处理
                            // 福利金退款逻辑在 app/listener/order/Refund.php 中的 refundWelfare() 方法
                            break;
                    }
                }
            }
            //订单记录
            $admin = $admin ? "操作人:" . $admin : '';
            OrderStatusJob::dispatch([$order['id'], 'refund_price', ['change_message' => '退款给用户：' . $refundData['refund_price'] . '元; ' . $admin, 'change_manager_id' => request()->adminId(), 'change_manager_type' => 'admin']]);

            return $order;
        });
// 在事件触发前更新 refunded_price
        if (!empty($refundData['refunded_price']) && bccomp($refundData['refunded_price'], '0', 2) > 0) {
            \think\facade\Log::info("在事件触发前更新退款单 refunded_price: id={$this->dao->getValue(['id' => $refundId ?? 0], 'id')}, amount={$refundData['refunded_price']}");
            $this->dao->update(['id' => $refundId ?? 0], ['refunded_price' => $refundData['refunded_price']]);
        }

        //订单同意退款事件
        Log::info('=== 触发 order.refund 事件 ===');
        Log::info('refundData: ' . json_encode($refundData, JSON_UNESCAPED_UNICODE));
        Log::info('order: ' . json_encode($order, JSON_UNESCAPED_UNICODE));
        event('order.refund', [$refundData, $order, 'order_refund']);
        Log::info('=== order.refund 事件触发完成 ===');
        return true;
    }

    /**
     * 处理退款 拆分订单
     * @param int $id
     * @param array $orderRefundInfo
     * @return bool
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function agreeSplitRefundOrder(int $id, $orderRefundInfo = [])
    {
        if (!$orderRefundInfo) {
            $orderRefundInfo = $this->dao->get($id);
        }
        if (!$orderRefundInfo) {
            throw new ValidateException('数据不存在');
        }
        $cart_ids = [];
        if ($orderRefundInfo['cart_info']) {
            foreach ($orderRefundInfo['cart_info'] as $cart) {
                $cart_ids[] = [
                    'cart_id' => $cart['id'],
                    'cart_num' => $cart['cart_num'],
                ];
            }
        }
        return $this->transaction(function () use ($orderRefundInfo, $cart_ids) {
            /** @var StoreOrderSplitServices $storeOrderSplitServices */
            $storeOrderSplitServices = app()->make(StoreOrderSplitServices::class);
            $oid = (int)$orderRefundInfo['store_order_id'];
            $splitResult = $storeOrderSplitServices->equalSplit($oid, $cart_ids, [], 0, true);
            $orderInfo = [];
            if ($splitResult) {//拆分发货
                [$orderInfo, $otherOrder] = $splitResult;
            }
            if ($orderInfo) {
                /** @var StoreOrderServices $storeOrderServices */
                $storeOrderServices = app()->make(StoreOrderServices::class);
                //原订单退款状态清空
                $storeOrderServices->update($oid, ['refund_status' => 0, 'refund_type' => 0]);

                // 根据退款金额判断是全额退款还是部分退款
                // 拆分订单的 pay_price 就是本次退款的金额，所以拆分后就是全额退款
                $splitRefundStatus = 1; // 拆分订单全额退款
                $storeOrderServices->update($orderInfo['id'], ['refund_status' => $splitRefundStatus, 'refund_type' => 6]);
                \think\facade\Log::info("拆分订单退款状态设置: order_id={$orderInfo['id']}, refund_status={$splitRefundStatus}");

                //修改售后订单 关联退款订单
                $this->dao->update($orderRefundInfo['id'], ['store_order_id' => $orderInfo['id']]);
                if ($oid != $otherOrder['id']) {//拆分生成新订单了
                    //修改原订单还在申请的退款单
                    $this->dao->update(['store_order_id' => $oid], ['store_order_id' => $otherOrder['id']]);
                }
                $orderInfo = $storeOrderServices->get($orderInfo['id']);
            } else {//整单退款
                /** @var StoreOrderServices $storeOrderServices */
                $storeOrderServices = app()->make(StoreOrderServices::class);

                // 获取订单信息判断是全额退款还是部分退款
                $currentOrder = $storeOrderServices->get($oid);
                $totalRefundPrice = bcadd((string)($currentOrder['refund_price'] ?? 0), (string)($orderRefundInfo['refund_price'] ?? 0), 2);
                $payPrice = (string)($currentOrder['pay_price'] ?? 0);

                // 如果累计退款金额 >= 支付金额，则为全额退款(1)，否则为部分退款(2)
                $refundStatus = bccomp($totalRefundPrice, $payPrice, 2) >= 0 ? 1 : 2;
                \think\facade\Log::info("整单退款状态判断: order_id={$oid}, pay_price={$payPrice}, total_refund={$totalRefundPrice}, refund_status={$refundStatus}");

                $storeOrderServices->update($oid, ['refund_status' => $refundStatus, 'refund_type' => 6]);
                //修改订单商品申请退款数量
                /** @var StoreOrderCartInfoServices $storeOrderCartInfoServices */
                $storeOrderCartInfoServices = app()->make(StoreOrderCartInfoServices::class);
                $storeOrderCartInfoServices->update(['oid' => $oid], ['refund_num' => 0]);
                $orderInfo = $storeOrderServices->get($oid);
            }
            return $orderInfo;
        });
    }

    /**
     * 订单退款表单
     * @param int $id
     * @param string $type
     * @return mixed
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function refundOrderForm(int $id, string $type = 'refund')
    {
        if ($type == 'refund') {//售后订单
            $orderRefund = $this->dao->get($id);
            if (!$orderRefund) {
                throw new ValidateException('未查到订单');
            }
            $order = $this->storeOrderServices->get((int)$orderRefund['store_order_id']);
            if (!$order) {
                throw new ValidateException('未查到订单');
            }
            if (!$order['paid']) {
                throw new ValidateException('未支付无法退款');
            }
            if ($orderRefund['refund_price'] > 0 && in_array($orderRefund['refund_type'], [1, 5])) {
                if ($orderRefund['refund_price'] <= $orderRefund['refunded_price']) {
                    throw new ValidateException('订单已退款');
                }
            }
            $f[] = Form::input('order_id', '退款单号', $orderRefund->getData('order_id'))->disabled(true);
            $f[] = Form::number('refund_price', '退款金额', (float)bcsub((string)$orderRefund->getData('refund_price'), (string)$orderRefund->getData('refunded_price'), 2))->min(0)->required('请输入退款金额');
            $f[] = Form::input('pay_postage', '运费', $order->getData('pay_postage'))->disabled(true);
            return create_form('退款处理', $f, $this->url('/refund/refund/' . $id), 'PUT');
        } else {//订单主动退款
            $order = $this->storeOrderServices->get((int)$id);
            if (!$order) {
                throw new ValidateException('未查到订单');
            }
            if (!$order['paid']) {
                throw new ValidateException('未支付无法退款');
            }
            if ($order['pay_price'] > 0 && in_array($order['refund_status'], [0, 1])) {
                if ($order['pay_price'] <= $order['refund_price']) {
                    throw new ValidateException('订单已退款');
                }
            }
            if ($order['pid'] >= 0) {//未拆分主订单、已拆分子订单
                /** @var StoreOrderRefundServices $storeOrderRefundServices */
                $storeOrderRefundServices = app()->make(StoreOrderRefundServices::class);
                if ($storeOrderRefundServices->count(['store_order_id' => $id, 'refund_type' => [1, 2, 4, 5, 6], 'is_cancel' => 0, 'is_del' => 0])) {
                    throw new ValidateException('请到售后订单列表处理');
                }
            } else {//已拆分发货
                throw new ValidateException('主订单已拆分发货，暂不支持整单主动退款');
            }

            $f[] = Form::input('order_id', '退款单号', $order->getData('order_id'))->disabled(true);
            $f[] = Form::number('refund_price', '退款金额', (float)bcsub((string)$order->getData('pay_price'), (string)$order->getData('refund_price'), 2))->required('请输入退款金额');
            return create_form('退款处理', $f, $this->url('/order/refund/' . $id), 'PUT');
        }
    }


    /**
     * 余额退款
     * @param $order
     * @param array $refundData
     * @return bool
     */
    public function yueRefund($order, array $refundData)
    {
        \think\facade\Log::info('=== 开始处理余额退款 ===');
        \think\facade\Log::info('订单号: ' . ($order['order_id'] ?? 'unknown'));
        \think\facade\Log::info('订单ID: ' . ($order['id'] ?? 'unknown'));
        \think\facade\Log::info('用户ID: ' . ($order['uid'] ?? 0));
        \think\facade\Log::info('退款金额: ' . ($refundData['refund_price'] ?? 0));

        if (!$order['uid']) {
            \think\facade\Log::warning('用户ID为空，跳过余额退款');
            return true;
        }

        $refundPrice = $refundData['refund_price'];
        if (bccomp((string)$refundPrice, '0', 2) <= 0) {
            \think\facade\Log::warning('退款金额为0或负数，跳过余额退款');
            return true;
        }

        /** @var UserServices $userServices */
        $userServices = app()->make(UserServices::class);
        $usermoney = $userServices->value(['uid' => $order['uid']], 'now_money');
        
        \think\facade\Log::info('用户当前余额: ' . $usermoney);

        $res = $userServices->bcInc($order['uid'], 'now_money', $refundPrice, 'uid');
        if (!$res) {
            \think\facade\Log::error('❌ 余额退款失败：增加用户余额失败');
            throw new ValidateException('余额退款失败，请联系客服');
        }
        \think\facade\Log::info('✅ 用户余额增加成功，增加金额: ' . $refundPrice);

        /** @var StoreOrderCartInfoServices $cartInfoServices */
        $cartInfoServices = app()->make(StoreOrderCartInfoServices::class);
        try {
            $storeName = $cartInfoServices->getCarIdByProductTitle($order['id']);
            $arr = explode('|', $storeName);
            $num = count($arr);
            if ($num > 1) {
                $title = '购买' . substrUTf8($arr[0], 9, 'UTF-8', '') . '等';
            } else {
                $title = '购买' . substrUTf8($storeName, 10, 'UTF-8', '');
            }
            \think\facade\Log::info('商品标题: ' . $title);
        } catch (\Exception $e) {
            $title = '';
            \think\facade\Log::warning('获取商品标题失败: ' . $e->getMessage());
        }

        /** @var UserMoneyServices $userMoneyServices */
        $userMoneyServices = app()->make(UserMoneyServices::class);
        
        $afterMoney = bcadd((string)$usermoney, (string)$refundPrice, 2);
        \think\facade\Log::info('退款后余额: ' . $afterMoney);

        $billResult = $userMoneyServices->income('pay_product_refund', $order['uid'], $refundPrice, $afterMoney, $order['id'], $title);
        
        if (!$billResult) {
            \think\facade\Log::error('❌ 余额退款失败：记录资金流水失败');
            throw new ValidateException('记录资金流水失败，请联系客服');
        }
        
        \think\facade\Log::info('✅ 资金流水记录成功');
        \think\facade\Log::info('=== 余额退款处理完成 ===');
        
        return true;
    }
    /**
     * 回退积分和优惠卷
     * @param $order
     * @return bool
     */
    public function integralAndCouponBack($order)
    {
        $res = true;
        //回退优惠卷 拆分子订单不退优惠券
        if (!$order['pid'] && $order['coupon_id'] && $order['coupon_price']) {
            /** @var StoreCouponUserServices $coumonUserServices */
            $coumonUserServices = app()->make(StoreCouponUserServices::class);
            $res = $res && $coumonUserServices->recoverCoupon((int)$order['coupon_id']);
        }
        //回退积分
        [$order, $changeIntegral] = $this->regressionIntegral($order);
        if ($changeIntegral > 0) {
            OrderStatusJob::dispatch([$order['id'], 'integral_back', ['change_message' => '商品退积分:' . $changeIntegral, 'change_manager_id' => request()->adminId(), 'change_manager_type' => 'admin']]);
        }
        return $res && $order->save();
    }

    /**
     * 回退使用积分和赠送积分
     * @param $order
     * @return array
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function regressionIntegral($order)
    {
        /** @var UserServices $userServices */
        $userServices = app()->make(UserServices::class);
        $userInfo = $userServices->get($order['uid'], ['integral']);
        if (!$userInfo) {
            $order->back_integral = $order->use_integral;
            return [$order, 0];
        }
        $integral = $userInfo['integral'];
        if ($order['status'] == -2 || $order['is_del']) {
            return [$order, 0];
        }
        $res1 = $res2 = $res3 = $res4 = true;
        //订单赠送积分
        /** @var UserBillServices $userBillServices */
        $userBillServices = app()->make(UserBillServices::class);
        $where = [
            'uid' => $order['uid'],
            'category' => 'integral',
            'type' => 'gain',
            'link_id' => $order['id']
        ];
        $give_integral = $userBillServices->sum($where, 'number');
        if ((int)$order['refund_status'] != 2 && $order['back_integral'] >= $order['use_integral']) {
            return [$order, 0];
        }
        //子订单退款 再次查询主订单
        if (!$give_integral && $order['pid']) {
            $where['link_id'] = $order['pid'];
            $give_integral = $userBillServices->sum($where, 'number');
            if ($give_integral) {
                $p_order = $this->storeOrderServices->get($order['pid']);
                $give_integral = bcmul((string)$give_integral, (string)bcdiv((string)$order['pay_price'], (string)$p_order['pay_price'], 4), 0);
            }
        }
        if ($give_integral) {
            //判断订单是否已经回退积分
            $count = $userBillServices->count(['category' => 'integral', 'type' => 'deduction', 'link_id' => $order['id']]);
            if (!$count) {
                if ($integral > $give_integral) {
                    $integral = bcsub((string)$integral, (string)$give_integral);
                } else {
                    $integral = 0;
                }
                //记录赠送积分收回
                $res1 = $userBillServices->income('integral_refund', $order['uid'], (int)$give_integral, (int)$integral, $order['id']);
            }
        }
        //返还下单支付积分 积分兑换
        $pay_integral = $order['pay_integral'];
        if ($pay_integral > 0) {
            $integral = bcadd((string)$integral, (string)$pay_integral);
            //记录下单支付积分还回
            $res2 = $userBillServices->income('order_integral_refund', $order['uid'], (int)$pay_integral, (int)$integral, $order['id']);
        }
        //返还下单抵扣积分
        $use_integral = $order['use_integral'];
        if ($use_integral > 0) {
            $integral = bcadd((string)$integral, (string)$use_integral);
            //记录下单抵扣积分还回
            $res2 = $userBillServices->income('pay_product_integral_back', $order['uid'], (int)$use_integral, (int)$integral, $order['id']);
        }
        $res3 = $userServices->update($order['uid'], ['integral' => $integral]);
        if (!($res1 && $res2 && $res3)) {
            throw new ValidateException('回退积分增加失败');
        }
        if ($use_integral > $give_integral) {
            $order->back_integral = bcsub($use_integral, $give_integral, 2);
        }
        return [$order, bcsub((string)$integral, (string)$userInfo['integral'], 0)];
    }

    /**
     * 回退库存
     * @param $order
     * @return bool
     */
    public function regressionStock($order)
    {
        if ($order['status'] == -2 || $order['is_del']) return true;
        $res5 = true;
        /** @var StoreOrderCartInfoServices $cartServices */
        $cartServices = app()->make(StoreOrderCartInfoServices::class);
        /** @var StoreProductServices $services */
        $services = app()->make(StoreProductServices::class);
        /** @var StoreSeckillServices $seckillServices */
        $seckillServices = app()->make(StoreSeckillServices::class);
        /** @var StoreCombinationServices $pinkServices */
        $pinkServices = app()->make(StoreCombinationServices::class);
        /** @var StoreBargainServices $bargainServices */
        $bargainServices = app()->make(StoreBargainServices::class);
        /** @var StoreDiscountsServices $discountServices */
        $discountServices = app()->make(StoreDiscountsServices::class);
        /** @var StoreNewcomerServices $storeNewcomerServices */
        $storeNewcomerServices = app()->make(StoreNewcomerServices::class);
        /** @var StoreIntegralServices $storeIntegralServices */
        $storeIntegralServices = app()->make(StoreIntegralServices::class);
        $activity_id = (int)$order['activity_id'];
        $store_id = (int)$order['store_id'] ?? 0;
        $cartInfo = $cartServices->getCartInfoList(['cart_id' => $order['cart_id']], ['cart_info']);
        foreach ($cartInfo as $cart) {
            $cart['cart_info'] = is_array($cart['cart_info']) ? $cart['cart_info'] : json_decode($cart['cart_info'], true);
            //增库存减销量
            $unique = isset($cart['cart_info']['productInfo']['attrInfo']) ? $cart['cart_info']['productInfo']['attrInfo']['unique'] : '';
            $cart_num = (int)$cart['cart_info']['cart_num'];
            $product_id = (int)$cart['cart_info']['productInfo']['id'];
            switch ($order['type']) {
                case 0://普通
                case 6://预售
                case 8://抽奖
                    $res5 = $res5 && $services->incProductStock($cart_num, $product_id, $unique);
                    break;
                case 1://秒杀
                    $res5 = $res5 && $seckillServices->incSeckillStock($cart_num, $activity_id, $unique, $store_id);
                    break;
                case 2://砍价
                    $res5 = $res5 && $bargainServices->incBargainStock($cart_num, $activity_id, $unique, $store_id);
                    break;
                case 3://拼团
                    $res5 = $res5 && $pinkServices->incCombinationStock($cart_num, $activity_id, $unique, $store_id);
                    break;
                case 4://积分
                    $res5 = $res5 && $storeIntegralServices->incIntegralStock($cart_num, $activity_id, $unique, $store_id);
                    break;
                case 5://套餐
                    CacheService::setStock(md5($activity_id), 1, 5, false);
                    $res5 = $res5 && $discountServices->incDiscountStock($cart_num, $activity_id, (int)($cart['cart_info']['discount_product_id'] ?? 0), (int)($cart['cart_info']['product_id'] ?? 0), $unique, $store_id);
                    break;
                case 7://新人专享
                    $res5 = $res5 && $storeNewcomerServices->incNewcomerStock($cart_num, $activity_id, $unique, $store_id);
                    break;
                default:
                    $res5 = $res5 && $services->incProductStock($cart_num, $product_id, $unique);
                    break;
            }
            if (in_array($order['type'], [1, 2, 3])) CacheService::setStock($unique, $cart_num, (int)$order['type'], false);
        }
        if ($order['type'] == 5) {
            //改变套餐限量
            $res5 = $res5 && $discountServices->changeDiscountLimit($activity_id, false);
        }
        $this->regressionRedisStock($order);
        return $res5;
    }

    /**
     * 回退redis占用库存
     * @param $order
     * @return bool
     */
    public function regressionRedisStock($order)
    {
        if ($order['status'] == -2 || $order['is_del']) return true;
        $type = $order['type'] ?? 0;
        /** @var StoreOrderCartInfoServices $storeOrderCartInfoServices */
        $storeOrderCartInfoServices = app()->make(StoreOrderCartInfoServices::class);
        $cartInfo = $storeOrderCartInfoServices->getOrderCartInfo((int)$order['id']);
        //回退套餐限量库
        if ($type == 5 && $order['activity_id']) CacheService::setStock(md5($order['activity_id']), 1, 5, false);
        foreach ($cartInfo as $item) {//回退redis占用
            if (!isset($item['product_attr_unique']) || !$item['product_attr_unique']) continue;
            $type = $item['type'];
            if (in_array($type, [1, 2, 3, 4])) CacheService::setStock($item['product_attr_unique'], (int)$item['cart_num'], $type, false);
        }
        return true;
    }

    /**
     * 同意退款退款失败写入订单记录
     * @param int $id
     * @param $refund_price
     */
    public function storeProductOrderRefundYFasle(int $id, $refund_price)
    {
        OrderStatusJob::dispatch([$id, 'refund_price', ['change_message' => '退款给用户：' . $refund_price . '元失败', 'change_manager_id' => request()->adminId(), 'change_manager_type' => 'admin']]);
    }

    /**
     * 不退款表单
     * @param int $id
     * @return array
     * @throws \FormBuilder\Exception\FormBuilderException
     */
    public function noRefundForm(int $id)
    {
        $orderRefund = $this->dao->get($id);
        if (!$orderRefund) {
            throw new ValidateException('未查到订单');
        }
        $order = $this->storeOrderServices->get((int)$orderRefund['store_order_id']);
        if (!$order) {
            throw new ValidateException('未查到订单');
        }
        $f[] = Form::input('order_id', '不退款单号', $order->getData('order_id'))->disabled(true);
        $f[] = Form::input('refund_reason', '不退款原因')->type('textarea')->required('请填写不退款原因');
        return create_form('不退款原因', $f, $this->url('order/no_refund/' . $id), 'PUT');
    }

    /**
     * 退积分表单创建
     * @param int $id
     * @return array
     * @throws \FormBuilder\Exception\FormBuilderException
     */
    public function refundIntegralForm(int $id)
    {
        if (!$orderInfo = $this->storeOrderServices->get($id))
            throw new ValidateException('订单不存在');
        if ($orderInfo->use_integral < 0 || $orderInfo->use_integral == $orderInfo->back_integral)
            throw new ValidateException('积分已退或者积分为零无法再退');
        if (!$orderInfo->paid)
            throw new ValidateException('未支付无法退积分');
        $f[] = Form::input('order_id', '退款单号', $orderInfo->getData('order_id'))->disabled(1);
        $f[] = Form::number('use_integral', '使用的积分', (float)$orderInfo->getData('use_integral'))->min(0)->disabled(1);
        $f[] = Form::number('use_integrals', '已退积分', (float)$orderInfo->getData('back_integral'))->min(0)->disabled(1);
        $f[] = Form::number('back_integral', '可退积分', (float)bcsub($orderInfo->getData('use_integral'), $orderInfo->getData('back_integral')))->min(0)->precision(0)->required('请输入可退积分');
        return create_form('退积分', $f, $this->url('/order/refund_integral/' . $id), 'PUT');
    }

    /**
     * 单独退积分处理
     * @param $orderInfo
     * @param $back_integral
     */
    public function refundIntegral($orderInfo, $back_integral)
    {
        /** @var UserServices $userServices */
        $userServices = app()->make(UserServices::class);
        $integral = $userServices->value(['uid' => $orderInfo['uid']], 'integral');
        if ($back_integral > 0) {
            return $this->transaction(function () use ($userServices, $orderInfo, $back_integral, $integral) {
                $res1 = $userServices->bcInc($orderInfo['uid'], 'integral', $back_integral, 'uid');
                /** @var UserBillServices $userBillServices */
                $userBillServices = app()->make(UserBillServices::class);
                $balance = bcadd((string)$integral, (string)$back_integral);
                $res2 = $userBillServices->income('pay_product_integral_back', $orderInfo['uid'], (int)$back_integral, (int)$balance, $orderInfo['id']);
                OrderStatusJob::dispatch([$orderInfo['id'], 'integral_back', ['change_message' => '商品退积分:' . $back_integral, 'change_manager_id' => request()->adminId(), 'change_manager_type' => 'admin']]);
                $res4 = $orderInfo->save();
                $res = $res1 && $res2 && $res4;
                if (!$res) {
                    throw new ValidateException('订单退积分失败');
                }
                return true;
            });
        }
        return true;
    }

    /**
     * 用户发起退款管理员短信提醒
     * 用户退款中模板消息
     * @param string $order_id
     */
    public function sendAdminRefund($order)
    {
        $switch = (bool)sys_config('admin_refund_switch');
        /** @var StoreServiceServices $services */
        $services = app()->make(StoreServiceServices::class);
        $adminList = $services->getStoreServiceOrderNotice();
        SmsAdminJob::dispatchDo('sendAdminRefund', [$switch, $adminList, $order]);
        /** @var WechatUserServices $wechatServices */
        $wechatServices = app()->make(WechatUserServices::class);
        if ($order['is_channel'] == 1) {
            //小程序
            $openid = $wechatServices->uidToOpenid($order['uid'], 'routine');
            if ($openid) RoutineTemplateJob::dispatchDo('sendOrderRefundStatus', [$openid, $order]);
        } else {
            $openid = $wechatServices->uidToOpenid($order['uid'], 'wechat');
            if ($openid) WechatTemplateJob::dispatchDo('sendOrderApplyRefund', [$openid, $order]);
        }
        return true;
    }

    /**
     * 写入退款快递单号
     * @param $order
     * @param $express
     * @return bool
     */
    public function editRefundExpress($data)
    {
        $id = (int)$data['id'];
        $refundOrder = $this->dao->get($id);
        if (!$refundOrder) {
            throw new ValidateException('退款订单不存在');
        }
        $this->transaction(function () use ($id, $refundOrder, $data) {
            $data['refund_type'] = 5;
            OrderStatusJob::dispatch([$refundOrder['store_order_id'], 'refund_express', ['change_message' => '用户已退货，快递单号：' . $data['refund_express'], 'change_manager_type' => 'user']]);
            $res1 = true;
            $res2 = false !== $this->dao->update(['id' => $id], $data);
            $res = $res1 && $res2;
            if (!$res)
                throw new ValidateException('提交失败!');
        });
        return true;
    }

    /**
     * 退款订单详情
     * @param $uni
     * @param array $field
     * @param array $with
     * @return mixed
     */
    public function refundDetail($uni, array $field = ['*'], array $with = ['invoice', 'virtual'])
    {
        if (!strlen(trim($uni))) throw new ValidateException('参数错误');
        $order = $this->dao->get(['id|order_id' => $uni], ['*']);
        if (!$order) throw new ValidateException('订单不存在');
        $order = $order->toArray();
        /** @var StoreOrderServices $orderServices */
        $orderServices = app()->make(StoreOrderServices::class);
        $orderInfo = $orderServices->get($order['store_order_id'], $field, $with);
        $orderInfo = $orderInfo->toArray();
        $orderInfo = $orderServices->tidyOrder($orderInfo, true, true);
        /** @var UserServices $userServices */
        $userServices = app()->make(UserServices::class);
        $userInfo = $userServices->getUserWithTrashedInfo($order['uid']);
        $order['mapKey'] = sys_config('tengxun_map_key');
        $order['yue_pay_status'] = (int)sys_config('balance_func_status') && (int)sys_config('yue_pay_status') == 1 ? (int)1 : (int)2;//余额支付 1 开启 2 关闭
        $order['pay_weixin_open'] = (int)sys_config('pay_weixin_open') ?? 0;//微信支付 1 开启 0 关闭
        $order['ali_pay_status'] = (bool)sys_config('ali_pay_status');//支付包支付 1 开启 0 关闭
        $orderData = $order;
        $orderData['type'] = $orderInfo['type'];
        $orderData['store_order_sn'] = $orderInfo['order_id'];
        $orderData['product_type'] = $orderInfo['product_type'];
        $orderData['store_id'] = $orderInfo['store_id'];
        $orderData['supplier_id'] = $orderInfo['supplier_id'] ?? 0;
        $orderData['supplierInfo'] = $orderInfo['supplierInfo'] ?? null;
        $orderData['cartInfo'] = $orderData['cart_info'];
        $orderData['invoice'] = $orderInfo['invoice'];
        $orderData['virtual'] = $orderInfo['virtual'];
        $orderData['virtual_info'] = $orderInfo['virtual_info'];
        $orderData['custom_form'] = is_string($orderInfo['custom_form']) ? json_decode($orderInfo['custom_form'], true) : $orderInfo['custom_form'];
        $orderData['first_order_price'] = $orderInfo['first_order_price'];
        $orderData['refund_price_type'] = $this->refundPriceType[$orderInfo['pay_type']] ?? '其他方式返还';
        $cateData = [];
        if (isset($orderData['cartInfo']) && $orderData['cartInfo']) {
            $productId = array_column($orderData['cartInfo'], 'product_id');
            /** @var StoreProductServices $productServices */
            $productServices = app()->make(StoreProductServices::class);
            $cateData = $productServices->productIdByProductCateName($productId);
        }
        //核算优惠金额
        $vipTruePrice = 0.00;
        $total_price = 0.00;
        $promotionsPrice = 0.00;
        foreach ($orderData['cartInfo'] ?? [] as $key => &$cart) {
            if (!isset($cart['sum_true_price'])) $cart['sum_true_price'] = bcmul((string)$cart['truePrice'], (string)$cart['cart_num'], 2);
            $cart['vip_sum_truePrice'] = bcmul($cart['vip_truePrice'], $cart['cart_num'] ? $cart['cart_num'] : 1, 2);
            $vipTruePrice = bcadd((string)$vipTruePrice, (string)$cart['vip_sum_truePrice'], 2);
            if (isset($order['split']) && $order['split']) {
                $orderData['cartInfo'][$key]['cart_num'] = $cart['surplus_num'];
                if (!$cart['surplus_num']) unset($orderData['cartInfo'][$key]);
            }
            $total_price = bcadd($total_price, bcmul((string)$cart['sum_price'], (string)$cart['cart_num'], 2), 2);
            $orderData['cartInfo'][$key]['class_name'] = $cateData[$cart['product_id']] ?? '';
            $promotionsPrice = bcadd($promotionsPrice, bcmul((string)($cart['promotions_true_price'] ?? 0), (string)$cart['cart_num'], 2), 2);
        }
        //优惠活动优惠详情
        /** @var StoreOrderPromotionsServices $storeOrderPromotiosServices */
        $storeOrderPromotiosServices = app()->make(StoreOrderPromotionsServices::class);
        if ($orderData['refund_type'] == 6) {
            $orderData['promotions_detail'] = $storeOrderPromotiosServices->getOrderPromotionsDetail((int)$orderData['store_order_id']);
        } else {
            $orderData['promotions_detail'] = $storeOrderPromotiosServices->applyRefundOrderPromotions((int)$orderData['store_order_id'], $orderData['cartInfo']);
        }
        if (!$orderData['promotions_detail'] && $promotionsPrice) {
            $orderData['promotions_detail'][] = [
                'name' => '优惠活动',
                'title' => '优惠活动',
                'promotions_price' => $promotionsPrice,
            ];
        }
        $orderData['use_integral'] = $this->getOrderSumPrice($orderData['cartInfo'], 'use_integral', false);
        $orderData['integral_price'] = $this->getOrderSumPrice($orderData['cartInfo'], 'integral_price', false);
        $orderData['coupon_id'] = $orderInfo['coupon_id'];
        $orderData['coupon_price'] = $this->getOrderSumPrice($orderData['cartInfo'], 'coupon_price', false);
        $orderData['deduction_price'] = $this->getOrderSumPrice($orderData['cartInfo'], 'integral_price', false);
        $orderData['vip_true_price'] = $vipTruePrice;
        $orderData['postage_price'] = 0.00;
        $orderData['pay_postage'] = '0.00';
        if (!in_array($orderInfo['shipping_type'], [2, 4])) {
            $orderData['pay_postage'] = $this->getOrderSumPrice($orderData['cart_info'], 'postage_price', false);
        }
        $orderData['member_price'] = 0;
        $orderData['routine_contact_type'] = sys_config('routine_contact_type', 0);
        $orderData['_add_time'] = date('Y-m-d H:i:s', $orderData['add_time']);
        $orderData['add_time_y'] = date('Y-m-d', $orderData['add_time']);
        $orderData['add_time_h'] = date('H:i:s', $orderData['add_time']);

        if ($orderData['apply_type'] == 3) {
            /** @var SystemStoreServices $storeServices */
            $storeServices = app()->make(SystemStoreServices::class);
            $storeInfo = $storeServices->search(['is_del' => 0])->find();
            $refund_name = $storeInfo['name'] ?? '';
            $refund_phone = $storeInfo['phone'] ?? '';
            $refund_address = ($storeInfo['address'] ?? '') . ($storeInfo['detailed_address'] ?? '');
            $latitude = $storeInfo['latitude'] ?? '';
            $longitude = $storeInfo['longitude'] ?? '';
        } elseif ($orderData['supplier_id']) {
            /** @var SystemSupplierServices $supplierServices */
            $supplierServices = app()->make(SystemSupplierServices::class);
            $supplierInfo = $supplierServices->get($orderData['supplier_id']);
            $refund_name = $supplierInfo['supplier_name'] ?? '';
            $refund_phone = $supplierInfo['phone'] ?? '';
            $refund_address = $supplierInfo['address'] . $supplierInfo['detailed_address'];
        } else {
            $refund_name = sys_config('refund_name', '');
            $refund_phone = sys_config('refund_phone', '');
            $refund_address = sys_config('refund_address', '');
        }
        [$type, $title, $status_name, $pic, $desc] = $this->tidyOrderStatus($orderData);

        // 直接使用 tidyOrder 已经生成的支付方式和支付明细
        $payTypeName = $orderInfo['_status']['_payType'] ?? '';
        $payDetailList = $orderInfo['pay_detail_list'] ?? [];

        $orderData['_status'] = [
            '_type' => $type,
            '_title' => $title,
            '_msg' => $status_name,
            'pic' => sys_config('site_url') . $pic,
            'desc' => $desc,
            '_payType' => $payTypeName,
            'pay_detail_list' => $payDetailList, // 使用 tidyOrder 生成的支付明细列表
            'refund_name' => $refund_name,
            'refund_phone' => $refund_phone,
            'refund_address' => $refund_address,
            'latitude' => $latitude ?? '',
            'longitude' => $longitude ?? '',
        ];
        $orderData['shipping_type'] = $orderInfo['shipping_type'];
        $orderData['real_name'] = $orderInfo['real_name'];
        $orderData['user_phone'] = $orderInfo['user_phone'];
        $orderData['user_address'] = $orderInfo['user_address'];
        $orderData['_pay_time'] = $orderInfo['pay_time'] ? date('Y-m-d H:i:s', $orderInfo['pay_time']) : '';
        $orderData['_refund_time'] = $orderData['add_time'] ? date('Y-m-d H:i:s', $orderData['add_time']) : '';
        $orderData['nickname'] = $userInfo['nickname'] ?? '';
        $orderData['total_num'] = $orderData['refund_num'];
        $orderData['pay_price'] = $orderData['refund_price'];
        $orderData['refund_status'] = in_array($orderData['refund_type'], [0, 1, 2, 4, 5]) ? 1 : 2;
        $orderData['total_price'] = floatval(bcsub((string)$total_price, (string)$vipTruePrice, 2));
        $orderData['paid'] = 1;
        $orderData['mark'] = $orderInfo['mark'];
        $orderData['express_list'] = $orderData['refund_type'] == 4 ? app()->make(ExpressServices::class)->expressList(['is_show' => 1]) : [];
        $orderData['spread_uid'] = $orderInfo['spread_uid'] ?? 0;
        $orderData['orderStatus'] = $orderInfo['_status'];
        return $orderData;
    }

    /**
     * 获取某个字段总金额
     * @param $cartInfo
     * @param string $key
     * @param bool $is_unit
     * @return int|string
     */
    public function getOrderSumPrice($cartInfo, $key = 'truePrice', $is_unit = true)
    {
        $SumPrice = 0;
        foreach ($cartInfo as $cart) {
            if (isset($cart['cart_info'])) $cart = $cart['cart_info'];
            if ($is_unit) {
                $SumPrice = bcadd($SumPrice, bcmul($cart['cart_num'] ?? 1, $cart[$key] ?? 0, 2), 2);
            } else {
                $SumPrice = bcadd($SumPrice, $cart[$key] ?? 0, 2);
            }
        }
        return $SumPrice;
    }


    /**
     * 删除已退款和拒绝退款的订单
     * @param int $uid
     * @param $uni
     * @return bool
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function delRefundOrder(int $uid, $uni)
    {
        $orderRefund = $this->dao->get(['order_id' => $uni, 'is_del' => 0]);
        if (!$orderRefund || $orderRefund['uid'] != $uid) {
            throw new ValidateException('订单不存在');
        }
        if (!in_array($orderRefund['refund_type'], [3, 6])) {
            throw new ValidateException('当前状态不能删除退款单');
        }
        $this->dao->update($orderRefund['id'], ['is_del' => 1]);
        /** @var StoreOrderServices $orderServices */
        $orderServices = app()->make(StoreOrderServices::class);
        $orderServices->update($orderRefund['store_order_id'], ['is_del' => 1]);
        //用户删除订单
        $id = (int)$orderRefund['store_order_id'];
        $orderInfo = $orderServices->get($id);
        //删子订单 修改主订单状态
        if ($orderInfo['pid']) {
            $pid = (int)$orderInfo['pid'];
            //检测原订单子订单是否 全部删除
            if (!$orderServices->count(['pid' => $pid, 'is_del' => 0])) {
                //改变原订单状态
                $orderServices->update($pid, ['is_del' => 1]);
            }
        }
        return true;
    }

    /**
     * 计算部分退款时应返还的福利金金额
     * 注意: 福利金支持小数(2位),保留2位小数
     *
     * @param array $order 订单信息
     * @param float $refundPrice 本次退款金额
     * @return float 应返还的福利金金额(保留2位小数)
     */
    private function calculateRefundWelfareAmount(array $order, float $refundPrice): float
    {
        // 1. 如果订单没有福利金支付,直接返回0
        if (!isset($order['welfare_pay_price']) || $order['welfare_pay_price'] <= 0) {
            return 0;
        }

        // 2. 如果退款金额为0,直接返回0
        if ($refundPrice <= 0) {
            return 0;
        }

        // 3. 计算退款比例 = 本次退款金额 / 订单总金额
        $refundRatio = bcdiv((string)$refundPrice, (string)$order['pay_price'], 4);

        // 4. 计算应返还的福利金 = 原福利金支付金额 × 退款比例
        $refundWelfareAmount = bcmul((string)$order['welfare_pay_price'], $refundRatio, 2);

        // 5. 福利金支持小数(2位),保留2位小数(不再取整)
        $refundWelfareAmount = (float)$refundWelfareAmount;

        // 6. 查询已返还的福利金总额
        $alreadyRefundedWelfare = $this->getAlreadyRefundedWelfare($order['id']);

        // 7. 计算最大可返还金额 = 原福利金支付金额 - 已返还金额
        $maxRefundWelfare = bcsub((string)$order['welfare_pay_price'], (string)$alreadyRefundedWelfare, 2);

        // 8. 确保返还金额不超过最大可返还金额
        if (bccomp((string)$refundWelfareAmount, $maxRefundWelfare, 2) > 0) {
            $refundWelfareAmount = (float)$maxRefundWelfare;
        }

        // 9. 确保返还金额不为负数
        if ($refundWelfareAmount < 0) {
            $refundWelfareAmount = 0;
        }

        return $refundWelfareAmount;
    }

    /**
     * 处理在线支付部分的退款(组合支付场景)
     *
     * @param array $refundOrder 退款订单信息
     * @param array $refundData 退款数据
     * @return void
     * @throws ValidateException
     */
    private function handleOnlinePayRefund(array $refundOrder, array $refundData): void
    {
        Log::info('进入 handleOnlinePayRefund 方法: ' . json_encode([
            'pay_type' => $refundOrder['pay_type'] ?? 'unknown',
            'online_pay_price' => $refundOrder['online_pay_price'] ?? 'unknown',
            'pay_type_detail' => $refundOrder['pay_type_detail'] ?? 'empty',
        ], JSON_UNESCAPED_UNICODE));

        // 优先使用已计算好的在线支付退款金额(包含差额补偿)
        $onlineRefundAmount = 0;
        if (isset($refundData['_calculated_online_refund_amount'])) {
            // 使用调用方已经计算好的金额(已包含差额补偿)
            $onlineRefundAmount = $refundData['_calculated_online_refund_amount'];
            Log::info('使用已计算好的在线支付退款金额(含差额补偿): ' . $onlineRefundAmount);
        } elseif (isset($refundData['refund_price']) && $refundData['refund_price'] > 0) {
            // 兼容旧逻辑: 如果没有预先计算,则按比例计算
            $refundRatio = bcdiv((string)$refundData['refund_price'], (string)$refundOrder['pay_price'], 4);
            if (isset($refundOrder['online_pay_price']) && $refundOrder['online_pay_price'] > 0) {
                $onlineRefundAmount = bcmul((string)$refundOrder['online_pay_price'], $refundRatio, 2);
            }
            Log::info('按比例计算在线支付退款金额: ' . $onlineRefundAmount);
        }

        Log::info('最终在线支付退款金额: ' . $onlineRefundAmount);

        // 如果有在线支付金额需要退款
        if ($onlineRefundAmount > 0) {
            // 修改退款金额为在线支付部分
            $originalRefundPrice = $refundData['refund_price'];
            $refundData['refund_price'] = $onlineRefundAmount;

            // 获取在线支付方式
            $payType = PayServices::WEIXIN_PAY; // 默认微信支付

            Log::info('开始判断在线支付方式...');

            // 如果是组合支付,从 pay_type_detail 中获取在线支付方式
            if ($refundOrder['pay_type'] === 'combination' && !empty($refundOrder['pay_type_detail'])) {
                Log::info('订单是组合支付,尝试从 pay_type_detail 获取 online_pay_type');
                $payTypeDetail = is_array($refundOrder['pay_type_detail'])
                    ? $refundOrder['pay_type_detail']
                    : json_decode($refundOrder['pay_type_detail'], true);

                Log::info('解析后的 pay_type_detail: ' . json_encode($payTypeDetail, JSON_UNESCAPED_UNICODE));

                if (isset($payTypeDetail['online_pay_type'])) {
                    $payType = $payTypeDetail['online_pay_type'];
                    Log::info('从 pay_type_detail 中获取到 online_pay_type: ' . $payType);

                    // 兼容旧数据: 如果 online_pay_type 是 weixin/alipay,但实际是银联支付
                    // 检查是否有 target_sys 字段,如果有说明是银联支付
                    if (isset($payTypeDetail['target_sys']) && in_array($payType, ['weixin', 'alipay'])) {
                        Log::info("检测到 target_sys: {$payTypeDetail['target_sys']},订单实际是银联支付,修正 payType 为 ums");
                        $payType = 'ums';
                    }
                } else {
                    // 兼容旧数据:如果 pay_type_detail 中没有 online_pay_type,默认使用银联支付
                    // 因为当前系统的在线支付都是银联支付
                    $payType = 'ums';
                    Log::info('pay_type_detail 中没有 online_pay_type,使用默认值: ' . $payType);
                }
            } elseif ($refundOrder['pay_type'] === 'ums') {
                // 兼容旧的银联支付订单(pay_type 直接是 'ums')
                $payType = 'ums';
                Log::info('订单 pay_type 是 ums');
            } else {
                // 非组合支付,使用订单的 pay_type
                $payType = $refundOrder['pay_type'] ?? PayServices::WEIXIN_PAY;
                Log::info('非组合支付,直接使用订单 pay_type: ' . $payType);
            }

            Log::info('最终确定的支付方式 payType: ' . $payType);
            Log::info('进入 switch 语句,payType: ' . $payType);

            switch ($payType) {
                case PayServices::WEIXIN_PAY:
                    Log::info('匹配到微信支付退款 case (组合支付)');
                    $no = $refundOrder['order_id'];
                    if ($refundOrder['trade_no'] && $refundOrder['trade_no'] != $refundOrder['order_id']) {
                        $no = $refundOrder['trade_no'];
                        $refundData['type'] = 'trade_no';
                    }
                    if ($refundOrder['is_channel'] == 1) {
                        //小程序退款
                        $pay_routine_open = (bool)sys_config('pay_routine_open', 0);
                        if ($pay_routine_open) {
                            $refundData['refund_no'] = $refundOrder['order_id'];
                            /** @var WechatUserServices $wechatUserServices */
                            $wechatUserServices = app()->make(WechatUserServices::class);
                            $refundData['open_id'] = $wechatUserServices->value(['uid' => (int)$refundOrder['uid']], 'openid');
                            if (in_array(substr($refundOrder['unique'], 0, 2), ['wx', 'cp', 'hy', 'cz'])) {
                                $refundData['routine_order_id'] = $refundOrder['unique'];
                            } else {
                                $refundData['routine_order_id'] = $refundOrder['order_id'];
                            }
                            $refundData['pay_routine_open'] = true;
                        }
                        Payment::instance()->setAccessEnd(Payment::MINI)->payOrderRefund($no, $refundData);
                    } else {
                        if (!sys_config('wechat_appid')) {
                            Payment::instance()->setAccessEnd(Payment::APP)->payOrderRefund($no, $refundData);
                        } else {
                            Payment::instance()->setAccessEnd(Payment::WEB)->payOrderRefund($no, $refundData);
                        }
                    }
                    break;
                case 'routine':
                case 'weixinh5':
                case 'ums':
                    // 银联商务支付退款(组合支付中的在线支付部分)
                    Log::info('匹配到银联支付退款 case (组合支付), payType: ' . $payType);
                    // 银联退款订单号使用累计方式: 订单号_R退款次数
                    if (isset($refundData['refund_id']) && $refundData['refund_id']) {
                        $refund_id = $refundData['refund_id'];
                    } else {
                        $umsRefundCount = $this->dao->getCount([['order_id', 'like', $refundOrder['order_id'] . '%']]);
                        $refund_id = $refundOrder['order_id'] . '_R' . ($umsRefundCount + 1);
                        Log::info("生成银联退款订单号(组合支付): order_id={$refundOrder['order_id']}, refund_count={$umsRefundCount}, refund_id={$refund_id}");
                    }
                    
                    // 确保退款订单号格式正确：如果退款订单号已经有3HD3前缀，直接使用；否则让UmsPayService内部处理
                    if (str_starts_with($refund_id, '3HD3')) {
                        $formattedRefundId = $refund_id;
                    } else {
                        $formattedRefundId = $refund_id;
                    }

                    // 使用实际支付单号（如果有的话）
                    // 注意: actual_pay_order_id 可能是空字符串,需要用 empty() 检查
                    // 如果 actual_pay_order_id 为空,使用 order_id + pay_attempt_count 构建
                    if (!empty($refundOrder['actual_pay_order_id'])) {
                        $actualPayOrderId = $refundOrder['actual_pay_order_id'];
                    } else {
                        $payAttemptCount = $refundOrder['pay_attempt_count'] ?? 1;
                        $actualPayOrderId = $refundOrder['order_id'] . '_' . $payAttemptCount;
                    }
                    
                    // 确保支付单号格式正确：如果支付单号没有3HD3前缀但需要添加，则由UmsPayService内部处理
                    // 如果支付单号已经有3HD3前缀，直接使用
                    if (str_starts_with($actualPayOrderId, '3HD3')) {
                        // 已经有前缀，直接使用
                        $formattedActualPayOrderId = $actualPayOrderId;
                    } else {
                        // 没有前缀，让UmsPayService内部处理（仅在生产环境中添加）
                        $formattedActualPayOrderId = $actualPayOrderId;
                    }

                    // 判断是否是H5支付
                    $isH5 = $this->isH5Payment($refundOrder);
                    $instMid = $isH5 ? 'H5DEFAULT' : '';

                    // 根据支付类型实例化对应配置的UmsPayService
                    $paymentType = $isH5 ? 'h5' : 'mini';
                    Log::info('退款使用配置类型(组合支付): ' . $paymentType);

                    // 构建分账退款参数(组合支付也需要检查供应商分账)
                    $divisionRefundData = $this->buildRefundDivisionData($refundOrder, $onlineRefundAmount);

                    Log::info("银联退款参数(组合支付) - 业务订单号: " . $refundOrder['order_id'] . ", 实际支付单号: " . $actualPayOrderId . ", 退款单号: " . $refund_id . ", 订单总金额: " . $refundOrder['pay_price'] . ", 退款金额: " . $onlineRefundAmount . ", instMid: " . $instMid);
                    if (!empty($divisionRefundData)) {
                        Log::info('分账退款数据(组合支付): ' . json_encode($divisionRefundData, JSON_UNESCAPED_UNICODE));
                    }

                    try {
                        // 使用支付类型参数实例化,确保退款时的mid/tid与支付时一致
                        $umsPay = new \crmeb\services\UmsPayService($paymentType);
                        $refundResult = $umsPay->refund(
                            $formattedActualPayOrderId,          // 使用格式化后的实际支付单号
                            $formattedRefundId,                  // 使用格式化后的退款订单号
                            (string)$refundOrder['pay_price'],  // 订单总金额
                            (string)$onlineRefundAmount,        // 退款金额(在线支付部分)
                            '订单退款',                          // 退款原因
                            $divisionRefundData,                // 分账退款数据
                            $instMid                            // H5支付需要传instMid
                        );
                        Log::info('银联退款返回结果(组合支付): ' . json_encode($refundResult, JSON_UNESCAPED_UNICODE));
                        Log::info('银联退款调用成功(组合支付)');
                    } catch (\Exception $e) {
                        Log::info('银联退款调用失败(组合支付): ' . $e->getMessage());
                        Log::info('异常堆栈: ' . $e->getTraceAsString());

                        // 提取银联返回的错误信息
                        $errorMsg = $e->getMessage();
                        $userFriendlyMsg = '退款失败，请联系客服处理';

                        if (str_contains($errorMsg, '已退') && str_contains($errorMsg, '还可退')) {
                            $userFriendlyMsg = $errorMsg;
                        } elseif (str_contains($errorMsg, '退货金额校验不通过')) {
                            $userFriendlyMsg = $errorMsg;
                        } elseif (str_contains($errorMsg, '子商户')) {
                            $userFriendlyMsg = $errorMsg;
                        }

                        Log::error('银联退款失败(组合支付),用户可见错误信息: ' . $userFriendlyMsg);
                        throw new ValidateException($userFriendlyMsg);
                    }
                    break;
                case PayServices::ALIPAY_PAY:
                    Log::info('匹配到支付宝支付退款 case (组合支付)');
                    mt_srand();
                    $refund_id = $refundData['refund_id'] ?? $refundOrder['order_id'] . rand(100, 999);
                    AliPayService::instance()->refund(
                        strpos($refundOrder['trade_no'], '_') !== false ? $refundOrder['trade_no'] : $refundOrder['order_id'],
                        floatval($onlineRefundAmount),
                        $refund_id
                    );
                    break;
                default:
                    Log::info('未匹配到任何支付方式 case, payType: ' . $payType);
                    throw new ValidateException('不支持的支付方式: ' . $payType);
            }

            // 恢复原始退款金额
            $refundData['refund_price'] = $originalRefundPrice;
            Log::info('=== handleOnlinePayRefund 方法执行完成 ===');
        } else {
            Log::info('在线支付退款金额为0,跳过退款处理');
        }
    }

    /**
     * 检查平台子订单是否在支付时创建了分账记录
     * @param array $order 订单信息
     * @param string $platformSubOrderId 平台子订单号
     * @return bool
     */
    private function checkPlatformSubOrderExists(array $order, string $platformSubOrderId): bool
    {
        try {
            // 方法1: 检查供应商分账记录中是否存在平台分账记录
            /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
            $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);

            // 检查是否存在平台分账记录
            $platformShareRecords = $shareRecordServices->getShareRecords([
                'order_id' => $order['id'],
                'division_type' => 'platform'  // 平台分账记录
            ]);

            // 如果找到了平台分账记录，说明支付时创建了平台子订单
            if ($platformShareRecords && count($platformShareRecords) > 0) {
                Log::info("订单 {$order['order_id']} 在供应商分账记录中找到平台分账记录，平台子订单存在");
                return true;
            }

            // 方法2: 检查划付订单记录
            /** @var \app\dao\pay\WechatTransferOrderDao $transferOrderDao */
            $transferOrderDao = app()->make(\app\dao\pay\WechatTransferOrderDao::class);
            
            // 检查是否存在平台划付记录（包括成功、处理中、待处理等状态）
            $platformTransferExists = $transferOrderDao->existsByOrderNoTypeAndStatuses(
                $order['order_id'], 
                'platform',
                ['pending', 'processing', 'success']
            );

            if ($platformTransferExists) {
                Log::info("订单 {$order['order_id']} 在划付订单记录中找到平台记录，平台子订单存在");
                return true;
            }

            // 方法3: 检查订单本身是否是平台订单（非供应商订单）
            // 如果订单没有供应商ID，但有在线支付金额，则可能是平台订单
            if (empty($order['supplier_id']) || $order['supplier_id'] <= 0) {
                // 非供应商订单，检查是否有平台分账配置
                $configFile = config_path() . 'UmsPayConfig.json';
                if (file_exists($configFile)) {
                    $config = json_decode(file_get_contents($configFile), true);
                    $platformDivision = $config['platform_division'] ?? null;
                    
                    if ($platformDivision && !empty($platformDivision['mid'])) {
                        // 如果有平台分账配置，且订单有在线支付金额，说明可能创建了平台子订单
                        if (isset($order['online_pay_price']) && $order['online_pay_price'] > 0) {
                            Log::info("订单 {$order['order_id']} 是平台订单且有在线支付金额，平台子订单可能存在");
                            return true;
                        }
                    }
                }
            }

            Log::info("订单 {$order['order_id']} 未找到平台子订单记录，平台子订单不存在");
            return false;

        } catch (\Exception $e) {
            Log::error('检查平台子订单存在性失败: ' . $e->getMessage());
            // 出错时默认返回false，避免错误地尝试退款不存在的子订单
            return false;
        }
    }

    /**
     * 查询订单已返还的福利金总额
     *
     * @param int $orderId 订单ID
     * @return float 已返还的福利金总额(保留2位小数)
     */
    private function getAlreadyRefundedWelfare(int $orderId): float
    {
        try {
            // 查询该订单所有已完成的退款单的福利金返还总额
            // refund_type: 1-已退款, 2-部分退款, 4-商家同意退货退款, 5-商家拒绝退款, 6-已退款
            $totalRefunded = $this->dao->value([
                'store_order_id' => $orderId,
                'refund_type' => [1, 2, 4, 5, 6]
            ], 'SUM(refund_welfare_price)');

            return (float)($totalRefunded ?: 0);
        } catch (\Exception $e) {
            Log::error('查询已返还福利金失败: ' . $e->getMessage());
            return 0;
        }
    }

    /**
     * 判断订单是否是H5支付
     * @param array $order 订单信息
     * @return bool
     */
    private function isH5Payment(array $order): bool
    {
        try {
            // 调试日志：输出订单支付相关信息
            $payType = $order['pay_type'] ?? 'N/A';
            $payChannel = $order['pay_channel'] ?? 'N/A';
            $payTypeDetail = $order['pay_type_detail'] ?? 'N/A';
            Log::info("isH5Payment判断 - order_id={$order['order_id']}, pay_type={$payType}, pay_channel={$payChannel}, pay_type_detail=" . json_encode($payTypeDetail));

            // 方法1: 通过pay_type判断
            if (isset($order['pay_type']) && $order['pay_type'] === 'weixinh5') {
                Log::info("isH5Payment判断结果: true (通过pay_type)");
                return true;
            }

            // 方法2: 通过pay_type_detail判断
            if (isset($order['pay_type_detail']) && !empty($order['pay_type_detail'])) {
                $payTypeDetail = is_string($order['pay_type_detail'])
                    ? json_decode($order['pay_type_detail'], true)
                    : $order['pay_type_detail'];

                if (isset($payTypeDetail['online_pay_type']) && $payTypeDetail['online_pay_type'] === 'weixinh5') {
                    Log::info("isH5Payment判断结果: true (通过pay_type_detail)");
                    return true;
                }
            }

            // 方法3: 通过pay_channel判断（新增）
            if (isset($order['pay_channel']) && $order['pay_channel'] === 'weixinh5') {
                Log::info("isH5Payment判断结果: true (通过pay_channel)");
                return true;
            }

            Log::info("isH5Payment判断结果: false");
            return false;
        } catch (\Exception $e) {
            Log::error('判断H5支付失败: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * 构建退款时的分账数据
     * @param array $order 订单信息
     * @param float $refundAmount 退款金额
     * @return array
     */
    private function buildRefundDivisionData(array $order, float $refundAmount): array
    {
        try {
            // 判断是否有供应商且有结算价
            if (!isset($order['supplier_id']) || !$order['supplier_id'] ||
                !isset($order['settle_price']) || !$order['settle_price'] || $order['settle_price'] <= 0) {
                return [];
            }

            // 获取供应商信息
            /** @var \app\services\supplier\SystemSupplierServices $supplierServices */
            $supplierServices = app()->make(\app\services\supplier\SystemSupplierServices::class);
            $supplierInfo = $supplierServices->get($order['supplier_id'], ['id', 'supplier_name', 'unionpay_mid']);

            // 判断供应商是否有银联商户号
            if (!$supplierInfo || !$supplierInfo['unionpay_mid']) {
                Log::warning("供应商ID:{$order['supplier_id']} 未配置银联商户号,无法分账退款");
                return [];
            }

            // 查询该订单所有已退款的供应商流水记录
            /** @var \app\dao\order\StoreOrderRefundDao $refundDao */
            $refundDao = app()->make(\app\dao\order\StoreOrderRefundDao::class);

            // 查询该订单的所有退款记录
            $refundRecords = $refundDao->search(['store_order_id' => $order['id'], 'is_del' => 0])
                ->where('refunded_price', '>', 0)
                ->column('refunded_price', 'id');

            $totalRefundedAmount = array_sum($refundRecords);
            Log::info("订单 {$order['order_id']} 已退款总金额: {$totalRefundedAmount} 元");

            // 计算供应商应退款金额
            // 退款金额 * (结算价 / 订单总金额) = 供应商应退款金额
            $supplierRefundAmount = bcmul(
                (string)$refundAmount,
                bcdiv((string)$order['settle_price'], (string)$order['pay_price'], 6),
                2
            );

            // 如果供应商退款金额为0,则不需要分账退款
            if ($supplierRefundAmount <= 0) {
                return [];
            }

            // 查询供应商已收到的在线支付金额（用于计算可退金额）
            // 从 eb_supplier_share_records 中查询 online 类型的分账记录
            /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
            $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);

            $onlineShareRecords = $shareRecordServices->getShareRecords([
                'order_id' => $order['id'],
                'division_type' => 'online'
            ]);

            $supplierOnlineReceived = 0;
            if ($onlineShareRecords) {
                foreach ($onlineShareRecords as $record) {
                    $supplierOnlineReceived = bcadd((string)$supplierOnlineReceived, (string)$record['share_amount'], 2);
                }
            }

            Log::info("订单 {$order['order_id']} 供应商在线支付已收金额: {$supplierOnlineReceived} 元");

            // 查询供应商流水，计算已退款金额
            /** @var \app\services\supplier\finance\SupplierFlowingWaterServices $waterServices */
            $waterServices = app()->make(\app\services\supplier\finance\SupplierFlowingWaterServices::class);

            // 查询该订单供应商的退款流水（type=2 表示退款）
            $supplierRefundWater = $waterServices->getRefundNumbersByOrder(
                (int)$order['supplier_id'],
                (string)$order['order_id']
            );

            $supplierRefundedAmount = array_sum($supplierRefundWater);
            Log::info("订单 {$order['order_id']} 供应商已退金额: {$supplierRefundedAmount} 元");

            // 计算供应商剩余可退金额
            $supplierAvailableRefund = bcsub((string)$supplierOnlineReceived, (string)$supplierRefundedAmount, 2);
            Log::info("订单 {$order['order_id']} 供应商剩余可退金额: {$supplierAvailableRefund} 元");

            // 限制供应商退款金额 <= 剩余可退金额
            if (bccomp((string)$supplierRefundAmount, (string)$supplierAvailableRefund, 2) > 0) {
                Log::warning("订单 {$order['order_id']} 计算的供应商退款金额({$supplierRefundAmount})超过剩余可退金额({$supplierAvailableRefund}),已自动调整");
                $supplierRefundAmount = $supplierAvailableRefund;
            }

            // 如果调整后供应商退款金额为0,则不需要供应商分账退款
            if ($supplierRefundAmount <= 0) {
                Log::info("订单 {$order['order_id']} 供应商退款金额调整为0,不需要供应商分账退款");
                
                // 将全部退款金额分配给平台
                $subOrders = [];
                
                // 读取平台分账配置
                $configFile = config_path() . 'UmsPayConfig.json';
                if (file_exists($configFile)) {
                    $config = json_decode(file_get_contents($configFile), true);
                    $platformDivision = $config['platform_division'] ?? null;

                    if ($platformDivision && !empty($platformDivision['mid']) && bccomp((string)$refundAmount, '0', 2) > 0) {
                        // 生成平台子订单号
                        // 如果 actual_pay_order_id 为空,使用 order_id + pay_attempt_count 构建
                        if (!empty($order['actual_pay_order_id'])) {
                            $payOrderId = $order['actual_pay_order_id'];
                        } else {
                            $payAttemptCount = $order['pay_attempt_count'] ?? 1;
                            $payOrderId = $order['order_id'] . '_' . $payAttemptCount;
                        }
                        $subOrderBase = $payOrderId;
                        $lastUnderscorePos = strrpos($subOrderBase, '_');
                        if ($lastUnderscorePos !== false) {
                            $lastPart = substr($subOrderBase, $lastUnderscorePos + 1);
                            if (is_numeric($lastPart) && strlen($lastPart) <= 4 && strlen($lastPart) > 1) {
                                $subOrderBase = substr($subOrderBase, 0, $lastUnderscorePos);
                            }
                        }

                        $platformSubOrderId = 'PLAT_' . $subOrderBase;
                        if (str_starts_with($subOrderBase, '3HD3')) {
                            $orderIdWithoutPrefix = substr($subOrderBase, 4);
                            $platformSubOrderId = '3HD3PLAT_' . $orderIdWithoutPrefix;
                        }

                        // 检查平台子订单是否在支付时创建了分账记录，如果不存在则不加入退款列表
                        $platformSubOrderExists = $this->checkPlatformSubOrderExists($order, $platformSubOrderId);
                        
                        if ($platformSubOrderExists) {
                            $platformRefundAmountFen = bcmul((string)$refundAmount, '100', 0);

                            $subOrders[] = [
                                'mid' => $platformDivision['mid'],
                                'merOrderId' => $platformSubOrderId,
                                'totalAmount' => $platformRefundAmountFen,
                            ];

                            Log::info("订单 {$order['order_id']} 供应商退款金额为0,全部退款金额({$refundAmount}元)分配给平台,平台子订单号={$platformSubOrderId}");
                        } else {
                            Log::info("订单 {$order['order_id']} 供应商退款金额为0,但平台子订单不存在: 平台子订单号={$platformSubOrderId}，跳过平台分账退款");
                        }
                    }
                }

                $divisionData = [
                    'platformAmount' => 0,
                    'subOrders' => $subOrders
                ];

                return $divisionData;
            }

            // 获取实际支付单号(用于生成子订单号)
            // 退款时需要使用支付时的支付单号来生成子订单号,以保持一致性
            // 注意: actual_pay_order_id 可能是空字符串,需要用 empty() 检查
            // 如果 actual_pay_order_id 为空,使用 order_id + pay_attempt_count 构建
            if (!empty($order['actual_pay_order_id'])) {
                $payOrderId = $order['actual_pay_order_id'];
            } else {
                $payAttemptCount = $order['pay_attempt_count'] ?? 1;
                $payOrderId = $order['order_id'] . '_' . $payAttemptCount;
            }

            // 生成子订单号: 基于支付单号,但去掉时间戳后缀
            // 支付单号格式: wx740228190735171584_1_0561 (业务订单号_支付次数_时间戳)
            // 子订单号格式: SUB_wx740228190735171584_1 (保留支付次数,去掉时间戳)
            $subOrderBase = $payOrderId;
            // 去掉时间戳后缀: 只有当最后一部分是纯数字且长度<=4时才去掉(时间戳特征)
            $lastUnderscorePos = strrpos($subOrderBase, '_');
            if ($lastUnderscorePos !== false) {
                $lastPart = substr($subOrderBase, $lastUnderscorePos + 1);
                // 检查是否是时间戳后缀: 纯数字且长度<=4
                if (is_numeric($lastPart) && strlen($lastPart) <= 4 && strlen($lastPart) > 1) {
                    $subOrderBase = substr($subOrderBase, 0, $lastUnderscorePos);
                }
            }

            // 生成供应商子订单号: 银联要求子订单号也必须以3HD3开头
            $subOrderId = 'SUB_' . $subOrderBase;
            // 如果支付单号以3HD3开头,子订单号也需要以3HD3开头
            if (str_starts_with($subOrderBase, '3HD3')) {
                // 截取支付单号去掉3HD3前缀的部分
                $orderIdWithoutPrefix = substr($subOrderBase, 4);
                // 子订单号格式: 3HD3SUB_订单号(去掉3HD3后的部分)
                $subOrderId = '3HD3SUB_' . $orderIdWithoutPrefix;
            }

            // 计算供应商退款金额(分)
            $supplierRefundAmountFen = bcmul($supplierRefundAmount, '100', 0);

            // 构造分账退款子订单列表
            // 注意: 银联退款接口的subOrders中使用totalAmount字段,不是refundAmount
            $subOrders = [
                [
                    'mid' => $supplierInfo['unionpay_mid'],  // 供应商银联商户号
                    'merOrderId' => $subOrderId,             // 子订单号(带3HD3前缀)
                    'totalAmount' => $supplierRefundAmountFen, // 退款金额(分) - 字段名是totalAmount
                ]
            ];

            // 读取平台分账配置
            $configFile = config_path() . 'UmsPayConfig.json';
            if (file_exists($configFile)) {
                $config = json_decode(file_get_contents($configFile), true);
                $platformDivision = $config['platform_division'] ?? null;

                // 如果配置了平台分账,添加平台分账退款
                if ($platformDivision && !empty($platformDivision['mid'])) {
                    // 计算平台应退款金额 = 退款金额 - 供应商退款金额
                    $platformRefundAmount = bcsub((string)$refundAmount, (string)$supplierRefundAmount, 2);

                    // 只有当平台退款金额大于0时才添加平台分账退款
                    if (bccomp($platformRefundAmount, '0', 2) > 0) {
                        // 生成平台子订单号: 与供应商子订单号使用相同的逻辑
                        // 支付单号格式: wx740228190735171584_1_0561 (业务订单号_支付次数_时间戳)
                        // 平台子订单号格式: 3HD3PLAT_wx740228190735171584_1 (保留支付次数,去掉时间戳)
                        $platformSubOrderId = 'PLAT_' . $subOrderBase;
                        // 如果支付单号以3HD3开头,平台子订单号也需要以3HD3开头
                        if (str_starts_with($subOrderBase, '3HD3')) {
                            // 截取支付单号去掉3HD3前缀的部分
                            $orderIdWithoutPrefix = substr($subOrderBase, 4);
                            // 平台子订单号格式: 3HD3PLAT_订单号(去掉3HD3后的部分)
                            $platformSubOrderId = '3HD3PLAT_' . $orderIdWithoutPrefix;
                        }

                        // 检查平台子订单是否在支付时创建了分账记录，如果不存在则不加入退款列表
                        $platformSubOrderExists = $this->checkPlatformSubOrderExists($order, $platformSubOrderId);
                        
                        if ($platformSubOrderExists) {
                            $platformRefundAmountFen = bcmul((string)$platformRefundAmount, '100', 0);

                            $subOrders[] = [
                                'mid' => $platformDivision['mid'],           // 平台银联商户号
                                'merOrderId' => $platformSubOrderId,         // 平台子订单号
                                'totalAmount' => $platformRefundAmountFen,   // 平台退款金额(分) - 字段名是totalAmount
                            ];

                            Log::info("订单 {$order['order_id']} 添加平台分账退款: 平台退款金额={$platformRefundAmount}元, 平台子订单号={$platformSubOrderId}");
                        } else {
                            Log::info("订单 {$order['order_id']} 平台子订单不存在: 平台子订单号={$platformSubOrderId}，跳过平台分账退款");
                        }
                    }
                }
            }

            // 构造分账退款参数
            $divisionData = [
                'platformAmount' => 0,  // 平台退款金额恒为0
                'subOrders' => $subOrders
            ];

            Log::info("订单 {$order['order_id']} 构建分账退款数据成功: 供应商={$supplierInfo['supplier_name']}, 供应商退款={$supplierRefundAmount}元, 分账退款子订单数=" . count($subOrders));

            return $divisionData;

        } catch (\Exception $e) {
            Log::error("构建分账退款数据失败: " . $e->getMessage());
            return [];
        }
    }
}
