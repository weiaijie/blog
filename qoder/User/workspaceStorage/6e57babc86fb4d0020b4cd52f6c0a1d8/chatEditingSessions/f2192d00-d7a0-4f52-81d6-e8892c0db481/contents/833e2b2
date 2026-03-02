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

namespace app\services\supplier\finance;


use app\dao\supplier\finance\SupplierFlowingWaterDao;
use app\services\BaseServices;
use app\services\order\StoreOrderCreateServices;
use app\services\order\StoreOrderCartInfoServices;
use app\services\order\StoreOrderRefundServices;
use app\services\order\StoreOrderServices;
use think\annotation\Inject;

/**
 * 供应商流水
 * Class SupplierFlowingWaterServices
 * @package app\services\supplier\finance
 * @mixin SupplierFlowingWaterDao
 */
class SupplierFlowingWaterServices extends BaseServices
{
    /**
     * 支付类型
     * @var string[]
     */
    public array $pay_type = [
        'weixin' => '微信支付',
        'yue' => '余额支付',
        'offline' => '线下支付',
        'alipay' => '支付宝支付',
        // 'ums' => '银联支付',
        'ums' => '微信支付',
        'cash' => '现金支付',
        'automatic' => '自动转账',
        'store' => '微信支付',
        'welfare' => '福利金支付',
        'combination' => '组合支付'  // 历史遗留数据,实际应该拆分
    ];

    /**
     * 交易类型
     * @var string[]
     */
    public array $type = [
        1 => '支付订单',
        2 => '退款订单'
    ];

    /**
     * 当前退款的供应商应扣金额（用于跨服务传递）
     * @var string
     */
    public string $currentSupplierDeduction = '0.00';

    /**
     * 当前退款的平台应扣金额（用于跨服务传递）
     * @var string
     */
    public string $currentPlatformDeduction = '0.00';

    /**
     * 当前退款的各支付方式扣减明细（用于跨服务传递）
     * @var array
     */
    public array $currentDeductions = [];

    /**
     * Cache of share records that already succeeded.
     * @var array
     */
    private array $shareRecordSuccessCache = [];

    /**
     * @var SupplierFlowingWaterDao
     */
    #[Inject]
    protected SupplierFlowingWaterDao $dao;


    /**
     * 显示资源列表
     * @param array $where
     * @return array
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function getList(array $where)
    {
        [$page, $limit] = $this->getPageValue();
        $list = $this->dao->getList($where, '*', $page, $limit, ['user', 'supplierName']);
        foreach ($list as &$item) {
            $item['type_name'] = isset($this->type[$item['type']]) ? $this->type[$item['type']] : '其他类型';
            $item['pay_type_name'] = isset($this->pay_type[$item['pay_type']]) ? $this->pay_type[$item['pay_type']] : '其他方式';

            $item['add_time'] = $item['add_time'] ? date('Y-m-d H:i:s', $item['add_time']) : '';
            $item['finish_time'] = $item['finish_time'] ? date('Y-m-d H:i:s', $item['finish_time']) : '';
            $item['trade_time'] = $item['trade_time'] ? date('Y-m-d H:i:s', $item['trade_time']) : $item['add_time'];
            $item['user_nickname'] = $item['user_nickname'] ?: '游客';
        }
        $count = $this->dao->count($where);
        return compact('list', 'count');
    }

    /**
     * 供应商账单
     * @param $where
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function getFundRecord($where)
    {
        [$page, $limit] = $this->getPageValue();
        $where['is_del'] = 0;
        $data = $this->dao->getFundRecord($where, $page, $limit);
        $i = 1;
        foreach ($data['list'] as &$item) {
            $item['id'] = $i;
            $i++;
            $item['entry_num'] = bcsub($item['income_num'], $item['exp_num'], 2);
            switch ($where['timeType']) {
                case "day" :
                    $item['title'] = "日账单";
                    $item['add_time'] = date('Y-m-d', $item['add_time']);
                    break;
                case "week" :
                    $item['title'] = "周账单";
                    $item['add_time'] = '第' . $item['day'] . '周(' . date('m', $item['add_time']) . '月)';
                    break;
                case "month" :
                    $item['title'] = "月账单";
                    $item['add_time'] = date('Y-m', $item['add_time']);
                    break;
            }
        }
        return $data;
    }

    /**
     * 获取百分比
     * @param $num
     * @return string|null
     */
    public function getPercent($num)
    {
        return bcdiv($num, '100', 4);
    }

    /**
     * 获取指定订单的供应商退款流水金额列表
     * @param int $supplierId
     * @param string $orderId
     * @return array
     */
    public function getRefundNumbersByOrder(int $supplierId, string $orderId): array
    {
        return $this->dao->search([
            'supplier_id' => $supplierId,
            'link_id' => $orderId,
            'type' => 2,
            'is_del' => 0
        ])->column('number', 'id');
    }

    /**
     * 写入流水账单
     * @param $oid
     * @param $type
     * @return bool
     * @throws \Exception
     */
    public function setSupplierFinance($oid, $type = 1): bool
    {
        /** @var SupplierTransactionsServices $transactionsServices */
        $transactionsServices = app()->make(SupplierTransactionsServices::class);
        /** @var StoreOrderCartInfoServices $cartInfoServices */
        $cartInfoServices = app()->make(StoreOrderCartInfoServices::class);
        /** @var StoreOrderServices $storeOrderServices */
        $storeOrderServices = app()->make(StoreOrderServices::class);
        /** @var StoreOrderRefundServices $storeOrderRefundServices */
        $storeOrderRefundServices = app()->make(StoreOrderRefundServices::class);
        $order = $storeOrderServices->get($oid);
        if (!$order) {
            return true;
        }
        if ($order['supplier_id'] <= 0) return true;
        $data = $cartInfoServices->getOrderCartInfoSettlePrice($order['id']);
        $pay_postage = 0;
        if (isset($order['shipping_type']) && !in_array($order['shipping_type'], [2, 4])) {
            $pay_postage = floatval($storeOrderRefundServices->getOrderSumPrice($data['info'], 'postage_price', false));
        }
        if ($order['type'] == 8) {
            $order['pay_price'] = $order['total_price'];
        }
        $append = [
            'pay_price' => $order['pay_price'],
            'pay_postage' => $pay_postage,
            'total_price' => $order['total_price'],
        ];
        switch ($type) {
            case 1 ://支付
                $number = bcadd((string)$data['settlePrice'], $pay_postage, 2);
                //支付订单
                $this->savaData($order, $number, 1, 1, $append);

                //交易订单记录
                $transactionsServices->savaData($order, 1, 1, $append);
                break;
            case 2://退款
                // 基于流水状态：冻结中(0) / 外部分账(2/3) 不创建退款流水
                $incomeFlowingWater = $this->dao->getList([
                    'link_id' => $order['order_id'],
                    'pm' => 1,
                    'type' => 1,
                ], 'id,status', 0, 0);
                if ($incomeFlowingWater) {
                    $hasReleased = false;
                    foreach ($incomeFlowingWater as $flow) {
                        if ((int)($flow['status'] ?? 1) === 1) {
                            $hasReleased = true;
                            break;
                        }
                    }
                    if (!$hasReleased) {
                        \think\facade\Log::info("供应商流水未放款/外部分账处理中，跳过创建退款流水: order_id={$order['order_id']}");
                        break;
                    }
                }
                $number = bcadd((string)$data['refundSettlePrice'], $pay_postage, 2);
                $this->savaData($order, $number, 0, 2, $append);

                //交易订单记录
                $transactionsServices->savaData($order, 0, 2, $append);
                break;
        }

        return true;
    }

    /**
     * 写入数据
     * @param $order
     * @param $number
     * @param $pm
     * @param $type
     * @param $trade_type
     * @param array $append
     * @throws \Exception
     */
    public function savaData($order, $number, $pm, $type, array $append = [])
    {
        /** @var StoreOrderCreateServices $storeOrderCreateServices */
        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);
        $order_id = $storeOrderCreateServices->getNewOrderId('ls');
        $data = [
            'supplier_id' => $order['supplier_id'] ?? 0,
            'uid' => $order['uid'] ?? 0,
            'order_id' => $order_id,
            'link_id' => $order['order_id'] ?? '',
            'pay_type' => $order['pay_type'] ?? '',
            'trade_time' => $order['pay_time'] ?? $order['add_time'] ?? '',
            'pm' => $pm,
            'number' => $number ?: 0,
            'type' => $type,
            'add_time' => time()
        ];
        if ($type == 1) {
            $payType = $data['pay_type'] ?? '';
            $data['division_status'] = 0; // 0=待触发(待收货后再改为1)
            if (in_array($payType, ['welfare', 'yue'], true)) {
                $data['status'] = 0;
            } elseif (in_array($payType, ['weixin', 'alipay'], true)) {
                $data['status'] = 2;
            } else {
                $data['status'] = 1;
                $data['finish_time'] = (int)($order['pay_time'] ?? time());
            }
        }
        if ($type == 2) {
            $data['status'] = 1;
            $data['finish_time'] = time();
        }
        $data = array_merge($data, $append);
        $this->dao->save($data);
    }

    /**
     * 关联门店店员
     * @param $link_id
     * @param int $staff_id
     * @return mixed
     */
    public function setStaff($link_id, int $staff_id)
    {
        return $this->dao->update(['link_id' => $link_id], ['staff_id' => $staff_id]);
    }

    /**
     * 可提现金额
     * @param array $where
     * @return int|string
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function getSumFinance(array $where, array $whereData)
    {
        $field = 'sum(if(pm = 1,number,0)) as income_num,sum(if(pm = 0,number,0)) as exp_num';
        $whereData['status'] = 1;
        $data = $this->dao->getList($whereData, $field);
        if (!$data) return 0;
        $income_num = $data[0]['income_num'] ?? 0;
        $exp_num = $data[0]['exp_num'] ?? 0;
        $number = bcsub($income_num, $exp_num, 2);
        //已提现金额
        /** @var SupplierExtractServices $extractServices */
        $extractServices = app()->make(SupplierExtractServices::class);
        $where['not_status'] = -1;
        $extract_price = $extractServices->getExtractMoneyByWhere($where, 'extract_price');
        $price_not = bcsub((string)$number, (string)$extract_price, 2);
        return $price_not;
    }

    /**
     * 待分账金额统计（统计所有还不能提现的金额）
     * @param int $supplierId 供应商ID，0表示所有供应商
     * @return array
     * @throws \think\db\exception\DataNotFoundException
     * @throws \think\db\exception\DbException
     * @throws \think\db\exception\ModelNotFoundException
     */
    public function getPendingDivisionAmount(int $supplierId = 0): array
    {
        // 统计所有还不能提现的金额
        // status: 0=冻结中(福利金/余额待放款), 2=外部分账待处理(在线支付待分账)
        // 排除 status=1(可提现)的记录

        $field = 'sum(number) as total_amount, count(*) as total_count';

        // 统计总金额和笔数 (status IN (0, 2))
        $data = $this->dao->getPendingDivisionStats($supplierId, [0, 2], $field);
        $totalAmount = $data[0]['total_amount'] ?? 0;
        $totalCount = $data[0]['total_count'] ?? 0;

        // 分别统计福利金/余额 (status=0)
        $welfareBalanceData = $this->dao->getPendingDivisionStats($supplierId, [0], $field);

        // 分别统计在线支付 (status=2)
        $onlinePaymentData = $this->dao->getPendingDivisionStats($supplierId, [2], $field);

        return [
            'total_amount' => $totalAmount,
            'total_count' => $totalCount,
            'welfare_balance_amount' => $welfareBalanceData[0]['total_amount'] ?? 0,
            'welfare_balance_count' => $welfareBalanceData[0]['total_count'] ?? 0,
            'online_payment_amount' => $onlinePaymentData[0]['total_amount'] ?? 0,
            'online_payment_count' => $onlinePaymentData[0]['total_count'] ?? 0,
        ];
    }

    /**
     * 创建组合支付的供应商流水记录
     * @param array $order 订单信息
     * @return bool
     * @throws \Exception
     */
    public function createCombinationPayFlowingWater(array $order): bool
    {
        if ($order['supplier_id'] <= 0) {
            return true;
        }

        // 防重复检查: 检查是否已经为该订单的某种支付方式创建过流水
        $existingFlows = $this->dao->search([
            'link_id' => $order['order_id'],
            'supplier_id' => $order['supplier_id'],
            'type' => 1,  // 支付订单
            'pm' => 1     // 收入
        ])->select()->toArray();

        // 检查是否已经为每种支付方式创建了流水
        $existingPayTypes = [];
        foreach ($existingFlows as $flow) {
            $existingPayTypes[] = $flow['pay_type'];
        }

        // 获取订单支付明细
        $welfarePayPrice = $order['welfare_pay_price'] ?? 0;  // 福利金支付
        $balancePayPrice = $order['balance_pay_price'] ?? 0;  // 余额支付
        $onlinePayPrice = $order['online_pay_price'] ?? 0;    // 在线支付

        // 统计有多少种支付方式
        $paymentCount = 0;
        if ($welfarePayPrice > 0) $paymentCount++;
        if ($balancePayPrice > 0) $paymentCount++;
        if ($onlinePayPrice > 0) $paymentCount++;

        // 检查是否每种支付方式都已经有对应的流水记录
        $missingPayTypes = [];
        if ($welfarePayPrice > 0 && !in_array('welfare', $existingPayTypes)) {
            $missingPayTypes[] = 'welfare';
        }
        if ($balancePayPrice > 0 && !in_array('yue', $existingPayTypes)) {
            $missingPayTypes[] = 'yue';
        }
        if ($onlinePayPrice > 0) {
            // 检查是否已经存在在线支付类型的流水（weixin, alipay, ums）
            $onlinePayTypes = ['weixin', 'alipay', 'ums'];
            $hasOnlineFlow = false;
            foreach ($onlinePayTypes as $type) {
                if (in_array($type, $existingPayTypes)) {
                    $hasOnlineFlow = true;
                    break;
                }
            }
            if (!$hasOnlineFlow) {
                $missingPayTypes[] = 'online';
            }
        }

        \think\facade\Log::info("组合支付流水创建检查: order_id={$order['order_id']}, payment_count={$paymentCount}, existing_types=" . json_encode($existingPayTypes) . ", missing_types=" . json_encode($missingPayTypes));

        // 如果所有支付方式都已经有流水，则跳过创建
        if (empty($missingPayTypes)) {
            \think\facade\Log::info("订单所有支付方式的供应商流水已存在,跳过创建: order_id={$order['order_id']}, existing_types=" . json_encode($existingPayTypes));
            return true;
        } else {
            \think\facade\Log::info("订单缺失部分支付方式的供应商流水,继续创建: order_id={$order['order_id']}, missing_types=" . json_encode($missingPayTypes));
        }

        // 获取订单支付明细
        $payPrice = $order['pay_price'] ?? 0;           // 订单总金额
        $settlePrice = $order['settle_price'] ?? 0;     // 供应商应得金额

        // 如果订单金额为0或没有供应商分成,直接返回
        if ($payPrice <= 0 || $settlePrice <= 0) {
            \think\facade\Log::warning("订单金额或结算价为0,跳过流水创建: pay_price={$payPrice}, settle_price={$settlePrice}");
            return true;
        }

        $welfarePayPrice = $order['welfare_pay_price'] ?? 0;  // 福利金支付
        $balancePayPrice = $order['balance_pay_price'] ?? 0;  // 余额支付
        $onlinePayPrice = $order['online_pay_price'] ?? 0;    // 在线支付

        // 统计有多少种支付方式
        $paymentCount = 0;
        if ($welfarePayPrice > 0) $paymentCount++;
        if ($balancePayPrice > 0) $paymentCount++;
        if ($onlinePayPrice > 0) $paymentCount++;

        // 检查是否为单一支付方式，如果是，则确定具体支付类型
        $singlePayType = null;
        if ($welfarePayPrice > 0) {
            $singlePayType = 'welfare';
        } elseif ($balancePayPrice > 0) {
            $singlePayType = 'yue';
        } elseif ($onlinePayPrice > 0) {
            $singlePayType = 'weixin'; // 默认微信，后面会根据实际情况调整
        }
        
        // 如果不是组合支付(只有1种或0种支付方式)，但仍需根据实际支付类型创建流水
        if ($paymentCount <= 1) {
            \think\facade\Log::info("单一支付方式,创建对应流水: payment_count={$paymentCount}, actual_pay_type={$singlePayType}");
            
            // 如果没有实际支付金额，直接返回
            if ($paymentCount === 0) {
                \think\facade\Log::info("无实际支付金额，跳过流水创建: order_id={$order['order_id']}");
                return true;
            }
            
            // 根据实际支付类型创建对应的流水
            return $this->createSinglePayFlowingWater($order, $singlePayType);
        }

        \think\facade\Log::info("开始创建组合支付供应商流水: order_id={$order['order_id']}, missing_pay_types=" . json_encode($missingPayTypes));

        // 获取分账记录作为金额的“唯一真值”
        /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
        $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);
        $shareRecords = $shareRecordServices->getShareRecords(['order_no' => $order['order_id']]);

        if (!empty($shareRecords)) {
            \think\facade\Log::info("检测到分账记录，切换到镜像生成模式: order_id={$order['order_id']}");
            return $this->createFlowingWaterFromShareRecords($order, $shareRecords, $missingPayTypes);
        }

        \think\facade\Log::info("未发现分账记录，回退到比例计算模式: order_id={$order['order_id']}");
        $settleRatio = bcdiv((string)$settlePrice, (string)$payPrice, 4);

        // 防止除法返回null
        if ($settleRatio === null || $settleRatio === false) {
            \think\facade\Log::error("计算分成比例失败: settle_price={$settlePrice}, pay_price={$payPrice}");
            return false;
        }

        \think\facade\Log::info('=== 创建组合支付供应商流水 ===');
        \think\facade\Log::info("订单号: {$order['order_id']}");
        \think\facade\Log::info("订单总金额: {$payPrice}");
        \think\facade\Log::info("供应商应得: {$settlePrice}");
        \think\facade\Log::info("分成比例: {$settleRatio}");
        \think\facade\Log::info("福利金支付: {$welfarePayPrice}");
        \think\facade\Log::info("余额支付: {$balancePayPrice}");
        \think\facade\Log::info("在线支付: {$onlinePayPrice}");

        // 使用统一的按支付方式金额分配计算方法，与createSinglePayFlowingWater保持一致
        $onlineSettle = bcmul((string)$onlinePayPrice, $settleRatio, 2);
        \think\facade\Log::info("组合支付在线部分计算: {$onlinePayPrice} * {$settleRatio} = {$onlineSettle}");

        // 余额和福利金: 用总额减去在线支付,避免精度问题
        // 因为: 供应商应得 = 在线分账 + 余额分账 + 福利金分账
        $remainSettle = bcsub((string)$settlePrice, $onlineSettle, 2);  // 剩余应分账金额

        // 如果有福利金和余额,按比例分配剩余金额
        if ($welfarePayPrice > 0 && $balancePayPrice > 0) {
            // 福利金和余额都有,按比例分配
            $welfareBalanceTotal = bcadd((string)$welfarePayPrice, (string)$balancePayPrice, 2);
            $welfareRatio = bcdiv((string)$welfarePayPrice, $welfareBalanceTotal, 4);
            $welfareSettle = bcmul($remainSettle, $welfareRatio, 2);
            $balanceSettle = bcsub($remainSettle, $welfareSettle, 2);
        } elseif ($welfarePayPrice > 0) {
            // 只有福利金
            $welfareSettle = $remainSettle;
            $balanceSettle = '0.00';
        } elseif ($balancePayPrice > 0) {
            // 只有余额
            $welfareSettle = '0.00';
            $balanceSettle = $remainSettle;
        } else {
            // 都没有
            $welfareSettle = '0.00';
            $balanceSettle = '0.00';
        }

        \think\facade\Log::info("初始计算 - 在线应分账: {$onlineSettle}");
        \think\facade\Log::info("初始计算 - 剩余应分账: {$remainSettle}");
        \think\facade\Log::info("初始计算 - 福利金应分账: {$welfareSettle}");
        \think\facade\Log::info("初始计算 - 余额应分账: {$balanceSettle}");

        // 计算总分账金额
        $totalCalculated = bcadd(bcadd($welfareSettle, $balanceSettle, 2), $onlineSettle, 2);
        \think\facade\Log::info("分账总额: {$totalCalculated}");

        // 检查精度误差(理论上不应该有误差了)
        $diff = bcsub((string)$settlePrice, $totalCalculated, 2);
        if ($diff != 0) {
            \think\facade\Log::warning("=== 检测到分账金额精度误差 ===");
            \think\facade\Log::warning("供应商应得: {$settlePrice}");
            \think\facade\Log::warning("计算总额: {$totalCalculated}");
            \think\facade\Log::warning("差额: {$diff}");

            // 差额兜底: 优先调整福利金,其次余额,最后在线支付
            // 原则: 尽量保持各部分比例关系，同时确保总额平衡
            if ($welfareSettle > 0 || $welfarePayPrice > 0) {
                $welfareSettle = bcadd($welfareSettle, $diff, 2);
                \think\facade\Log::warning("差额由福利金承担,调整后: {$welfareSettle}");
            } elseif ($balanceSettle > 0 || $balancePayPrice > 0) {
                $balanceSettle = bcadd($balanceSettle, $diff, 2);
                \think\facade\Log::warning("差额由余额承担,调整后: {$balanceSettle}");
            } elseif ($onlineSettle > 0 || $onlinePayPrice > 0) {
                $onlineSettle = bcadd($onlineSettle, $diff, 2);
                \think\facade\Log::warning("差额由在线支付承担,调整后: {$onlineSettle}");
            } else {
                // 如果所有部分都是0,精度误差由系统承担
                \think\facade\Log::warning("所有支付部分均为0,精度误差由系统承担");
            }
        }

        \think\facade\Log::info("最终 - 福利金应分账: {$welfareSettle}");
        \think\facade\Log::info("最终 - 余额应分账: {$balanceSettle}");
        \think\facade\Log::info("最终 - 在线应分账: {$onlineSettle}");
        \think\facade\Log::info("最终 - 分账总额: " . bcadd(bcadd($welfareSettle, $balanceSettle, 2), $onlineSettle, 2));

        /** @var StoreOrderCreateServices $storeOrderCreateServices */
        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);

        // 1. 在线支付部分 (微信/支付宝 - 外部分账，不可提现)
        if ($onlinePayPrice > 0 && bccomp((string)$onlineSettle, '0', 2) > 0 && in_array('online', $missingPayTypes)) {
            // 只有在线支付金额>0 且 供应商分账金额>0 且缺失在线支付流水时才创建流水
            // 如果供应商分账金额为0,说明所有钱都归平台,不需要创建供应商流水

            // 只有在线支付才需要获取支付渠道和银联商户号
            $payChannel = $this->getPayChannel($order);
            $umsMerNo = $this->getUmsMerNo($payChannel);

            // 获取实际的在线支付方式
            $actualPayType = 'weixin';  // 默认微信

            if ($order['pay_type'] === 'combination' && !empty($order['pay_type_detail'])) {
                // 组合支付: 从 pay_type_detail 中获取在线支付方式
                $payTypeDetail = is_array($order['pay_type_detail'])
                    ? $order['pay_type_detail']
                    : json_decode($order['pay_type_detail'], true);

                // 优先从 target_sys 获取
                if (isset($payTypeDetail['target_sys'])) {
                    $targetSys = $payTypeDetail['target_sys'];
                    if ($targetSys === 'WXPay') {
                        $actualPayType = 'weixin';
                    } elseif ($targetSys === 'Alipay') {
                        $actualPayType = 'alipay';
                    }
                } elseif (isset($payTypeDetail['online_pay_type'])) {
                    // 从 online_pay_type 获取
                    $onlinePayType = $payTypeDetail['online_pay_type'];
                    if ($onlinePayType === 'ums') {
                        // 银联支付,需要从 pay_channel 或其他字段判断是微信还是支付宝
                        // 默认使用微信
                        $actualPayType = 'weixin';
                    } elseif ($onlinePayType === 'weixin') {
                        $actualPayType = 'weixin';
                    } elseif ($onlinePayType === 'alipay') {
                        $actualPayType = 'alipay';
                    }
                }
            } elseif ($order['pay_type'] === 'ums') {
                // 单一银联支付,默认微信
                $actualPayType = 'weixin';
            } else {
                // 其他单一支付方式
                $actualPayType = $order['pay_type'] ?? 'weixin';
            }

            \think\facade\Log::info("在线支付方式: {$actualPayType} (原始pay_type={$order['pay_type']})");

            // 计算平台分账金额 = 在线支付总额 - 供应商分账金额
            $platformAmount = bcsub((string)$onlinePayPrice, (string)$onlineSettle, 2);

            // 创建在线支付流水(包含供应商和平台金额)
            $orderId = $storeOrderCreateServices->getNewOrderId('ls');
            $this->dao->save([
                'supplier_id' => $order['supplier_id'],
                'uid' => $order['uid'],
                'order_id' => $orderId,
                'link_id' => $order['order_id'],
                'pay_type' => $actualPayType,  // 使用实际的支付方式
                'pay_channel' => $payChannel,  // 记录支付渠道
                'ums_mer_no' => $umsMerNo,     // 记录银联商户号
                'trade_time' => $order['pay_time'] ?? time(),
                'pm' => 1,  // 收入
                'number' => $onlineSettle,  // 供应商实收金额
                'platform_amount' => $platformAmount,  // 平台分账金额
                'type' => 1,  // 支付订单
                'status' => 2,  // 2=外部分账待处理（不可提现）
                'division_status' => 0,  // 0=无需分账(支付时已设置divisionFlag=true)
                'add_time' => time(),
                // 'remark' => '在线支付'
            ]);
            \think\facade\Log::info("创建在线支付流水: 供应商{$onlineSettle}元, 平台{$platformAmount}元 (pay_type={$actualPayType}, status=2 外部分账)");
        } elseif ($onlinePayPrice > 0 && bccomp((string)$onlineSettle, '0', 2) <= 0) {
            // 有在线支付但供应商分账金额为0,记录日志
            \think\facade\Log::info("在线支付{$onlinePayPrice}元,但供应商分账金额为0,不创建供应商流水,所有金额归平台");
        } elseif ($onlinePayPrice > 0 && !in_array('online', $missingPayTypes)) {
            \think\facade\Log::info("在线支付{$onlinePayPrice}元,但该支付方式的流水已存在,跳过创建");
        }

        // 2. 福利金部分 (冻结中，待统一放款)
        if ($welfareSettle > 0 && in_array('welfare', $missingPayTypes)) {
            $orderId = $storeOrderCreateServices->getNewOrderId('ls');
            $this->dao->save([
                'supplier_id' => $order['supplier_id'],
                'uid' => $order['uid'],
                'order_id' => $orderId,
                'link_id' => $order['order_id'],
                'pay_type' => 'welfare',
                'pay_channel' => '',  // 福利金无支付渠道
                'ums_mer_no' => '',   // 福利金无需银联商户号
                'trade_time' => $order['pay_time'] ?? time(),
                'pm' => 1,
                'number' => $welfareSettle,
                'type' => 1,
                'status' => 0,  // 0=冻结中（不可提现，待放款）
                'division_status' => 0,  // 0=无需分账
                'add_time' => time(),
                // 'remark' => '福利金支付-待放款'
            ]);
            \think\facade\Log::info("创建福利金支付流水: {$welfareSettle}元 (status=0 冻结中)");
        } elseif ($welfareSettle > 0 && !in_array('welfare', $missingPayTypes)) {
            \think\facade\Log::info("福利金支付{$welfareSettle}元,但该支付方式的流水已存在,跳过创建");
        }

        // 3. 余额部分 (冻结中，待统一放款)
        if ($balanceSettle > 0 && in_array('yue', $missingPayTypes)) {
            $orderId = $storeOrderCreateServices->getNewOrderId('ls');
            $this->dao->save([
                'supplier_id' => $order['supplier_id'],
                'uid' => $order['uid'],
                'order_id' => $orderId,
                'link_id' => $order['order_id'],
                'pay_type' => 'yue',
                'pay_channel' => '',  // 余额无支付渠道
                'ums_mer_no' => '',   // 余额无需银联商户号
                'trade_time' => $order['pay_time'] ?? time(),
                'pm' => 1,
                'number' => $balanceSettle,
                'type' => 1,
                'status' => 0,  // 0=冻结中（不可提现，待放款）
                'division_status' => 0,  // 0=无需分账
                'add_time' => time(),
                // 'remark' => '余额支付-待放款'
            ]);
            \think\facade\Log::info("创建余额支付流水: {$balanceSettle}元 (status=0 冻结中)");
        } elseif ($balanceSettle > 0 && !in_array('yue', $missingPayTypes)) {
            \think\facade\Log::info("余额支付{$balanceSettle}元,但该支付方式的流水已存在,跳过创建");
        }

        \think\facade\Log::info('=== 组合支付供应商流水创建完成 ===');
        
        // 查询刚刚创建的流水记录
        $createdFlows = $this->dao->search([
            'link_id' => $order['order_id'],
            'supplier_id' => $order['supplier_id'],
            'type' => 1,  // 支付订单
            'pm' => 1     // 收入
        ])->select()->toArray();
        
        $createdPayTypes = [];
        foreach ($createdFlows as $flow) {
            $createdPayTypes[] = $flow['pay_type'];
        }
        \think\facade\Log::info("订单 {$order['order_id']} 当前供应商流水: " . json_encode($createdPayTypes));

        return true;
    }

    /**
     * 创建单一支付方式的供应商流水记录
     * @param array $order 订单信息
     * @param string $payType 支付类型 (welfare/yue/weixin/alipay)
     * @return bool
     */
    public function createSinglePayFlowingWater(array $order, string $payType): bool
    {
        if ($order['supplier_id'] <= 0) {
            return true;
        }
        
        \think\facade\Log::info("创建单一支付流水: order_id={$order['order_id']}, pay_type={$payType}");
        
        // 检查是否已存在对应支付类型的流水
        $existingFlow = $this->dao->getOne([
            'link_id' => $order['order_id'],
            'pay_type' => $payType,
        ]);
        
        if ($existingFlow) {
            \think\facade\Log::info("订单已存在相同支付类型的流水,跳过创建: order_id={$order['order_id']}, pay_type={$payType}, existing_id={$existingFlow['id']}");
            return true;
        }

        // 优先从分账记录表中获取“真值”金额
        /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
        $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);
        $shareRecords = $shareRecordServices->getShareRecords(['order_no' => $order['order_id']]);

        $supplierSettle = null;
        $platformAmount = null;

        if (!empty($shareRecords)) {
            // 匹配支付类型
            foreach ($shareRecords as $record) {
                $isMatch = false;
                if ($payType === 'weixin' || $payType === 'alipay' || $payType === 'ums') {
                    if ($record['division_type'] === 'online') $isMatch = true;
                } elseif ($payType === 'welfare') {
                    if ($record['division_type'] === 'subsidy' && (strpos($record['remarks'], '福利金') !== false || strpos($record['remarks'], '补贴') !== false)) $isMatch = true;
                } elseif ($payType === 'yue') {
                    if ($record['division_type'] === 'subsidy' && strpos($record['remarks'], '余额') !== false) $isMatch = true;
                }

                if ($isMatch) {
                    $supplierSettle = (string)$record['share_amount'];
                    $platformAmount = (string)$record['platform_amount'];
                    \think\facade\Log::info("单一支付流水从分账记录镜像获取金额: supplier_amount={$supplierSettle}, platform_amount={$platformAmount}");
                    break;
                }
            }
        }
        
        if ($supplierSettle === null) {
            // 核心修复：单一支付方式下，供应商应得金额直接等于结算价
            // 这样可以避免因比例计算和精度截断导致的金额不一致问题
            $supplierSettle = (string)($order['settle_price'] ?? '0.00');
            
            \think\facade\Log::info("单一支付流水金额无法匹配分账记录，回退取结算价: settle_price={$supplierSettle}, pay_type={$payType}");
            
            // 确定流水支付总额（用于计算平台金额）
            $totalPayAmount = '0.00';
            switch ($payType) {
                case 'welfare':
                    $totalPayAmount = (string)($order['welfare_pay_price'] ?? '0.00');
                    break;
                case 'yue':
                    $totalPayAmount = (string)($order['balance_pay_price'] ?? '0.00');
                    break;
                case 'weixin':
                case 'alipay':
                case 'ums':
                    $totalPayAmount = (string)($order['online_pay_price'] ?? '0.00');
                    break;
                default:
                    $totalPayAmount = (string)($order['pay_price'] ?? '0.00');
                    break;
            }
            
            // 平台金额 = 总支付金额 - 供应商结算金额
            $platformAmount = bcsub($totalPayAmount, $supplierSettle, 2);
        }
        
        // 确定流水状态
        $status = 1; // 默认可提现
        if ($payType === 'welfare' || $payType === 'yue') {
            $status = 0; // 福利金/余额冻结中，待放款
        } elseif ($payType === 'weixin' || $payType === 'alipay' || $payType === 'ums') {
            $status = 2; // 在线支付，外部分账待处理
        }
        
        /** @var StoreOrderCreateServices $storeOrderCreateServices */
        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);
        $orderId = $storeOrderCreateServices->getNewOrderId('ls');
        
        $this->dao->save([
            'supplier_id' => $order['supplier_id'],
            'uid' => $order['uid'],
            'order_id' => $orderId,
            'link_id' => $order['order_id'],
            'pay_type' => $payType,
            'trade_time' => $order['pay_time'] ?? time(),
            'pm' => 1,  // 收入
            'number' => $supplierSettle,  // 供应商实收金额
            'platform_amount' => $platformAmount,  // 平台分账金额
            'type' => 1,  // 支付订单
            'status' => $status,
            'division_status' => 0,  // 0=待触发(待收货后再改为1)
            'add_time' => time(),
        ]);
        
        \think\facade\Log::info("创建单一支付流水成功: order_id={$order['order_id']}, pay_type={$payType}, supplier_amount={$supplierSettle}, platform_amount={$platformAmount}, status={$status}");
        
        return true;
    }
    
    /**
     * 基于分账记录镜像生成供应商流水
     * @param array $order
     * @param array $shareRecords
     * @param array $missingPayTypes
     * @return bool
     */
    protected function createFlowingWaterFromShareRecords(array $order, array $shareRecords, array $missingPayTypes): bool
    {
        /** @var StoreOrderCreateServices $storeOrderCreateServices */
        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);

        foreach ($shareRecords as $record) {
            $payType = '';
            if ($record['division_type'] === 'online') {
                $payType = 'weixin'; // 默认
                // 尝试从备注或订单信息中细化支付方式
                if (strpos($record['remarks'], '支付宝') !== false) $payType = 'alipay';
            } elseif ($record['division_type'] === 'subsidy') {
                if (strpos($record['remarks'], '福利金') !== false) $payType = 'welfare';
                elseif (strpos($record['remarks'], '余额') !== false) $payType = 'yue';
                else $payType = 'welfare'; // 默认
            }

            if (!$payType) continue;

            // 检查是否在缺失列表中 (online 对应 weixin/alipay/ums)
            $isMissing = false;
            if ($payType === 'weixin' || $payType === 'alipay' || $payType === 'ums') {
                if (in_array('online', $missingPayTypes)) $isMissing = true;
            } else {
                if (in_array($payType, $missingPayTypes)) $isMissing = true;
            }

            if (!$isMissing) continue;

            $status = 1;
            if (in_array($payType, ['welfare', 'yue'])) $status = 0;
            elseif (in_array($payType, ['weixin', 'alipay', 'ums'])) $status = 2;

            $orderId = $storeOrderCreateServices->getNewOrderId('ls');
            $saveData = [
                'supplier_id' => $order['supplier_id'],
                'uid' => $order['uid'],
                'order_id' => $orderId,
                'link_id' => $order['order_id'],
                'pay_type' => $payType,
                'trade_time' => $order['pay_time'] ?? time(),
                'pm' => 1,
                'number' => $record['share_amount'],
                'platform_amount' => $record['platform_amount'],
                'type' => 1,
                'status' => $status,
                'division_status' => 0, // 待触发(待收货后再改为1)
                'add_time' => time(),
            ];

            if ($status === 2) {
                $saveData['pay_channel'] = $this->getPayChannel($order);
                $saveData['ums_mer_no'] = $this->getUmsMerNo($saveData['pay_channel']);
            }

            $this->dao->save($saveData);
            \think\facade\Log::info("镜像生成组合支付流水成功: order_id={$order['order_id']}, pay_type={$payType}, amount={$record['share_amount']}");
        }

        return true;
    }

    /**
     * 获取支付渠道
     *
     * @param array $order
     * @return string h5 或 mini
     */
    protected function getPayChannel(array $order): string
    {
        // 从订单的pay_channel字段获取支付渠道
        if (isset($order['pay_channel']) && in_array($order['pay_channel'], ['h5', 'mini'])) {
            return $order['pay_channel'];
        }

        // 如果没有pay_channel字段,尝试从pay_type判断
        $payType = $order['pay_type'] ?? '';
        if ($payType === 'weixinh5') {
            return 'h5';
        } elseif ($payType === 'routine' || $payType === 'weixin') {
            return 'mini';
        }

        // 默认返回mini
        \think\facade\Log::warning('无法确定支付渠道,使用默认值mini: order_id=' . ($order['order_id'] ?? ''));
        return 'mini';
    }

    /**
     * 根据支付渠道获取银联商户号
     *
     * @param string $payChannel
     * @return string
     */
    protected function getUmsMerNo(string $payChannel): string
    {
        try {
            /** @var \app\services\pay\UmsDivisionServices $umsDivisionServices */
            $umsDivisionServices = app()->make(\app\services\pay\UmsDivisionServices::class);
            return $umsDivisionServices->getMerNoByChannel($payChannel);
        } catch (\Exception $e) {
            \think\facade\Log::error('获取银联商户号失败: ' . $e->getMessage());
            return '';
        }
    }

    /**
     * 统一分账/放款定时任务
     *
     * 处理逻辑：
     * 1. 福利金/余额（status=0）：直接放款 → status=1
     * 2. 微信在线支付：调用 WechatAmountTransferServices 统一划付（202002按金额划付）
     *
     * 注意：202001按流水划付接口未开通，所有微信支付统一使用202002按金额划付
     *
     * @return bool
     */
    public function autoProcessDivision(): bool
    {
        \think\facade\Log::info('=== 开始执行统一分账/放款任务 ===');

        try {
            // 1. 处理福利金/余额放款
            $this->processAllWelfareBalanceRelease();

            // 2. 处理微信支付划付（使用202002按金额划付）
            $this->processWechatTransfer();

            \think\facade\Log::info('=== 统一分账/放款任务执行完成 ===');
            return true;

        } catch (\Exception $e) {
            \think\facade\Log::error('统一分账/放款任务执行失败: ' . $e->getMessage());
            throw $e;
        }
    }

    /**
     * 批量处理福利金/余额放款
     * @return void
     */
    private function processAllWelfareBalanceRelease(): void
    {
        \think\facade\Log::info('--- 开始处理福利金/余额放款 ---');

        // 查询所有待放款的福利金/余额流水
        $records = $this->dao->getList([
            ['division_status', '=', 1],  // 待分账/待放款
            ['pm', '=', 1],  // 收入
            ['type', '=', 1],  // 支付订单
            ['status', '=', 0],  // 冻结中(福利金/余额)
            ['pay_type', 'in', ['welfare', 'yue']],  // 福利金或余额
        ], '*', 0, 0);

        if (empty($records)) {
            \think\facade\Log::info('没有待放款的福利金/余额流水');
            return;
        }

        \think\facade\Log::info('找到 ' . count($records) . ' 条待放款的福利金/余额流水');

        $successCount = 0;
        $failedCount = 0;

        foreach ($records as $record) {
            // 检查订单是否满足分账条件（特别是子订单的收货状态）
            if ($this->shouldSkipByOrderStatus($record)) {
                continue;
            }
            
            try {
                $this->processWelfareBalanceRelease($record);
                $successCount++;
            } catch (\Exception $e) {
                \think\facade\Log::error("福利金/余额放款失败: id={$record['id']}, error={$e->getMessage()}");
                $failedCount++;
            }
        }

        \think\facade\Log::info("福利金/余额放款完成: 成功 {$successCount} 条, 失败 {$failedCount} 条");
    }

    /**
     * 处理供应商微信支付划付（定时任务专用）
     *
     * 注意：此方法只处理供应商应得金额，平台部分由定时任务单独调用 WechatAmountTransferServices
     *
     * @return void
     */
    private function processWechatTransfer(): void
    {
        \think\facade\Log::info('--- 开始处理供应商微信支付划付（独立） ---');

        try {
            // 调用供应商专用的微信划付方法（从流水表查询，只处理供应商应得金额）
            // 定时任务不传时间范围，会自动检查免责期
            $result = $this->processSupplierWechatTransfer();

            \think\facade\Log::info("供应商微信划付完成: 成功 {$result['success']} 批次, 失败 {$result['failed']} 批次");

        } catch (\Exception $e) {
            \think\facade\Log::error('供应商微信支付划付失败: ' . $e->getMessage());
        }
    }

    /**
     * 处理福利金/余额放款
     * @param array $record 流水记录
     * @return bool
     */
    private function processWelfareBalanceRelease(array $record): bool
    {
        \think\facade\Log::info("福利金/余额放款: id={$record['id']}, order_id={$record['link_id']}, pay_type={$record['pay_type']}, amount={$record['number']}");

        // 直接更新状态为可提现
        $this->dao->update($record['id'], [
            'status' => 1,  // 可提现
            'division_status' => 2,  // 已处理
            'division_time' => time(),  // 记录处理时间
        ]);

        // 同步更新分账记录表状态 (福利金/余额属于平台补贴类型)
        $this->updateShareRecordStatus($record['link_id'], 'success', '', 'subsidy');

        \think\facade\Log::info("福利金/余额放款成功: id={$record['id']}");
        return true;
    }

    /**
     * 处理供应商微信支付划付（独立于平台划付）
     *
     * 从 eb_supplier_flowing_water 表查询微信支付流水，只处理供应商应得金额（number字段）
     * 平台部分金额由 WechatAmountTransferServices 处理
     *
     * @param string $startDate 开始日期
     * @param string $endDate 结束日期
     * @param int|null $supplierId 供应商ID（可选）
     * @return array ['success' => int, 'failed' => int, 'batches' => []]
     */
    public function processSupplierWechatTransfer(string $startDate = '', string $endDate = '', ?int $supplierId = null): array
    {
        \think\facade\Log::info('=== 开始处理供应商微信支付划付（独立） ===');
        \think\facade\Log::info("时间范围: {$startDate} ~ {$endDate}, 供应商ID: " . ($supplierId ?: '全部'));

        // 1. 从流水表查询待划付的微信支付流水
        $records = $this->collectSupplierWechatFlowingWater($startDate, $endDate, $supplierId);

        if (empty($records)) {
            \think\facade\Log::info('没有待划付的供应商微信支付流水');
            return ['success' => 0, 'failed' => 0, 'batches' => []];
        }

        \think\facade\Log::info('找到 ' . count($records) . ' 条待划付的供应商微信支付流水');

        // 🔒 关键：立即锁定这些流水，防止并发重复处理
        // 将 division_status 从 1(待处理) 更新为 3(处理中)
        $lockedRecords = $this->lockFlowingWaterRecords($records);
        if (empty($lockedRecords)) {
            \think\facade\Log::info('没有成功锁定的流水记录（可能已被其他进程处理）');
            return ['success' => 0, 'failed' => 0, 'batches' => []];
        }

        \think\facade\Log::info('成功锁定 ' . count($lockedRecords) . ' 条流水记录');

        // 2. 按供应商分组（使用锁定后的记录）
        $groups = $this->groupSupplierWechatRecords($lockedRecords);

        if (empty($groups)) {
            \think\facade\Log::info('没有有效的供应商分组');
            // 解锁流水（回滚到待处理状态）
            $this->unlockFlowingWaterRecords($lockedRecords);
            return ['success' => 0, 'failed' => 0, 'batches' => []];
        }

        // 3. 为每个分组创建批次并划付
        $batches = [];
        $successCount = 0;
        $failedCount = 0;

        /** @var \app\services\pay\WechatAmountTransferServices $transferServices */
        $transferServices = app()->make(\app\services\pay\WechatAmountTransferServices::class);

        foreach ($groups as $groupKey => $group) {
            $result = $this->processSupplierBatch($group, $transferServices);
            $batches[] = $result;

            if ($result['success']) {
                $successCount++;
                // 更新流水状态
                $this->updateFlowingWaterAfterTransfer($group['records'], true, $result['batch_id'] ?? 0);
            } else {
                $failedCount++;
                // 记录失败
                $this->updateFlowingWaterAfterTransfer($group['records'], false, $result['batch_id'] ?? 0, $result['error'] ?? '');
            }
        }

        \think\facade\Log::info("供应商微信支付划付完成: 成功 {$successCount} 批次, 失败 {$failedCount} 批次");

        return [
            'success' => $successCount,
            'failed' => $failedCount,
            'batches' => $batches,
        ];
    }

    /**
     * 采集待划付的供应商微信支付流水
     *
     * @param string $startDate 开始日期
     * @param string $endDate 结束日期
     * @param int|null $supplierId 供应商ID
     * @return array
     */
    private function collectSupplierWechatFlowingWater(string $startDate = '', string $endDate = '', ?int $supplierId = null): array
    {
        $isApiCall = $startDate && $endDate;

        $where = [
            ['division_status', '=', 1],  // 待分账/待划付
            ['pm', '=', 1],  // 收入
            ['type', '=', 1],  // 支付订单
            ['pay_type', 'in', ['weixin', 'ums']],  // 微信支付
            ['number', '>', 0],  // 供应商金额 > 0
        ];

        if ($supplierId) {
            $where[] = ['supplier_id', '=', $supplierId];
        }

        // 接口调用时，按时间范围查询
        if ($isApiCall) {
            $startTimeStamp = strtotime($startDate . ' 00:00:00');
            $endTimeStamp = strtotime($endDate . ' 23:59:59');
            $where[] = ['add_time', 'between', [$startTimeStamp, $endTimeStamp]];
        } else {
            // 定时任务：需要检查免责期
            // 流水的 finish_time（订单确认收货时间） + 免责期 < 当前时间
            $exemptionDays = (int)sys_config('wechat_transfer_exemption_days', 7);
            $exemptionEndTime = strtotime("-{$exemptionDays} days", time());
            $where[] = ['finish_time', '>', 0];
            $where[] = ['finish_time', '<', $exemptionEndTime];
        }

        $records = $this->dao->getList($where, '*', 0, 0, ['supplierName']);

        $filteredRecords = [];
        foreach ($records as $record) {
            // 检查订单是否满足分账条件（特别是子订单的收货状态）
            if ($this->shouldSkipByOrderStatus($record)) {
                continue;
            }
            
            if ($this->shouldSkipSupplierWechatRecord($record)) {
                continue;
            }
            $filteredRecords[] = $record;
        }

        return $filteredRecords;
    }

    private function shouldSkipByOrderStatus(array $record): bool
    {
        $orderNo = $record['link_id'] ?? '';
        if (!$orderNo) {
            return true;
        }

        try {
            // 检查订单是否存在以及是否满足分账条件
            /** @var \app\services\order\StoreOrderServices $orderServices */
            $orderServices = app()->make(\app\services\order\StoreOrderServices::class);
            
            // 查询订单信息
            $orderInfo = $orderServices->getOne(['order_id' => $orderNo]);
            
            if (!$orderInfo) {
                \think\facade\Log::warning("订单不存在，跳过分账: order_id={$orderNo}");
                return true;
            }
            
            $orderInfo = $orderInfo->toArray();
            
            // 检查订单状态是否满足分账条件
            // 1. 订单必须已经支付 (paid = 1)
            if (empty($orderInfo['paid'])) {
                \think\facade\Log::info("订单未支付，跳过分账: order_id={$orderNo}");
                return true;
            }
            
            // 2. 如果是子订单（包含下划线和数字后缀），需要检查子订单本身的收货状态
            if (strpos($orderNo, '_') !== false) {
                // 检查子订单本身的状态
                // 订单状态 0=待发货, 1=待收货, 2=已收货, 3=待评价, 4=部分发货, 5=部分核销
                // 根据业务要求，只有状态为2（已收货）或3（待评价）的子订单才能参与分账
                if ((int)$orderInfo['status'] != 2 && (int)$orderInfo['status'] != 3) {  // 只有状态为2或3的子订单才能分账
                    \think\facade\Log::info("子订单状态不符合分账要求，跳过分账: order_id={$orderNo}, status={$orderInfo['status']}");
                    return true;
                }
                

            } else {
                // 根据业务逻辑，主订单不参与分账，只有子订单参与分账
                // 所以主订单应该跳过分账处理
                \think\facade\Log::info("主订单不参与分账，跳过: order_id={$orderNo}");
                return true;
            }
            
            // 3. 检查订单是否在退款流程中
            if ((int)$orderInfo['refund_status'] !== 0) {
                \think\facade\Log::info("订单处于退款状态，跳过分账: order_id={$orderNo}, refund_status={$orderInfo['refund_status']}");
                return true;
            }
            
        } catch (\Exception $e) {
            \think\facade\Log::error("检查订单状态时发生异常，跳过分账: order_id={$orderNo}, error=" . $e->getMessage());
            return true;  // 异常情况下安全起见跳过
        }
        
        return false;
    }
    
    private function shouldSkipSupplierWechatRecord(array $record): bool
    {
        $orderNo = $record['link_id'] ?? '';
        $flowingWaterId = $record['id'] ?? 0;
        if (!$orderNo) {
            return false;
        }

        // 检查1: share_records 表是否已有成功记录
        if ($this->isShareRecordAlreadySuccess($orderNo, 'online')) {
            return true;
        }

        // 检查2: wechat_transfer_orders 表是否已有该流水的 supplier 类型记录
        // 这是防止重复划付的关键检查！
        if ($this->isTransferOrderAlreadyExists($orderNo, $flowingWaterId)) {
            return true;
        }

        return false;
    }

    /**
     * 检查是否已有划付记录（检查 wechat_transfer_orders 表）
     * @param string $orderNo 订单号
     * @param int $flowingWaterId 流水ID
     * @return bool
     */
    private function isTransferOrderAlreadyExists(string $orderNo, int $flowingWaterId): bool
    {
        try {
            /** @var \app\dao\pay\WechatTransferOrderDao $transferOrderDao */
            $transferOrderDao = app()->make(\app\dao\pay\WechatTransferOrderDao::class);

            // 检查是否已有该订单的 supplier 类型划付记录（排除失败状态，允许重试）
            $exists = $transferOrderDao->existsByOrderNoTypeAndStatuses($orderNo, 'supplier', ['pending', 'processing', 'success']);

            if ($exists) {
                \think\facade\Log::info("订单已有供应商划付记录,跳过: order_no={$orderNo}, flowing_water_id={$flowingWaterId}");
            }

            // 额外检查：同一流水ID是否已处理过
            if (!$exists && $flowingWaterId > 0) {
                $existsByFlowingWater = $transferOrderDao->existsByFlowingWaterIdTypeAndStatuses(
                    $flowingWaterId,
                    'supplier',
                    ['pending', 'processing', 'success']
                );

                if ($existsByFlowingWater) {
                    \think\facade\Log::info("流水已有划付记录,跳过: flowing_water_id={$flowingWaterId}, order_no={$orderNo}");
                    return true;
                }
            }

            return $exists;
        } catch (\Exception $e) {
            \think\facade\Log::error("检查划付记录失败: order_no={$orderNo}, error={$e->getMessage()}");
            // 出错时保守处理，不跳过（让后续逻辑处理）
            return false;
        }
    }

    /**
     * 锁定流水记录（更新 division_status 为处理中）
     * 使用 WHERE division_status=1 条件更新，确保原子性
     *
     * @param array $records 流水记录数组
     * @return array 成功锁定的记录
     */
    private function lockFlowingWaterRecords(array $records): array
    {
        $lockedRecords = [];
        foreach ($records as $record) {
            $recordId = $record['id'];
            try {
                // 使用 WHERE division_status=1 条件更新，确保原子性
                // 只有状态为 1(待处理) 的记录才会被锁定
                $affected = $this->dao->lockDivisionStatus($recordId, 1, 3);

                if ($affected > 0) {
                    $record['division_status'] = 3;
                    $lockedRecords[] = $record;
                    \think\facade\Log::info("锁定流水记录: id={$recordId}, order_no={$record['link_id']}");
                } else {
                    \think\facade\Log::warning("流水记录锁定失败（可能已被处理）: id={$recordId}, order_no={$record['link_id']}");
                }
            } catch (\Exception $e) {
                \think\facade\Log::error("锁定流水记录异常: id={$recordId}, error={$e->getMessage()}");
            }
        }
        return $lockedRecords;
    }

    /**
     * 解锁流水记录（回滚到待处理状态）
     * 用于分组失败等场景的回滚
     *
     * @param array $records 流水记录数组
     * @return void
     */
    private function unlockFlowingWaterRecords(array $records): void
    {
        foreach ($records as $record) {
            $recordId = $record['id'];
            try {
                // 只回滚处理中(3)的记录到待处理(1)
                $this->dao->unlockDivisionStatus($recordId, 3, 1);
                \think\facade\Log::info("解锁流水记录: id={$recordId}, order_no={$record['link_id']}");
            } catch (\Exception $e) {
                \think\facade\Log::error("解锁流水记录异常: id={$recordId}, error={$e->getMessage()}");
            }
        }
    }

    private function isShareRecordAlreadySuccess(string $orderNo, string $divisionType = 'online'): bool
    {
        $cacheKey = $orderNo . '_' . $divisionType;
        if (array_key_exists($cacheKey, $this->shareRecordSuccessCache)) {
            return $this->shareRecordSuccessCache[$cacheKey];
        }

        $hasSuccess = false;
        try {
            $shareRecordDao = app()->make(\app\dao\supplier\SupplierShareRecordDao::class);
            $record = $shareRecordDao->getOne([
                ['order_no', '=', $orderNo],
                ['division_type', '=', $divisionType],
                ['status', '=', 'success'],
            ], 'id');
            $hasSuccess = (bool)$record;
        } catch (\Exception $e) {
            \think\facade\Log::error("检查分账记录状态失败: order_no={$orderNo}, division_type={$divisionType}, error={$e->getMessage()}");
        }

        if ($hasSuccess) {
            \think\facade\Log::info("订单已有成功分账记录,跳过划付: order_no={$orderNo}, division_type={$divisionType}");
        }

        $this->shareRecordSuccessCache[$cacheKey] = $hasSuccess;
        return $hasSuccess;
    }

    /**
     * 进一步过滤手动触发的福利金/余额记录（因为 dao->getList(..., false) 不会自动应用条件）。
     *
     * @param array $records
     * @return array
     */
    private function filterWelfareRecords(array $records): array
    {
        $filtered = [];
        foreach ($records as $record) {
            $payType = $record['pay_type'] ?? '';
            if (!in_array($payType, ['welfare', 'yue'], true)) {
                continue;
            }
            if ((int)($record['division_status'] ?? 0) !== 1) {
                continue;
            }
            if ((int)($record['status'] ?? 0) !== 0) {
                continue;
            }
            $filtered[] = $record;
        }
        return $filtered;
    }

    private function logWelfareRecordSummary(array $records, string $context): void
    {
        $summary = array_map(function ($record) {
            return [
                'order_id' => $record['order_id'] ?? '',
                'link_id' => $record['link_id'] ?? '',
                'pay_type' => $record['pay_type'] ?? ''
            ];
        }, $records);

        \think\facade\Log::info("福利金/余额候选（{$context}）: " . json_encode($summary, JSON_UNESCAPED_UNICODE));
    }

    /**
     * 按供应商分组微信支付流水
     *
     * @param array $records 流水记录
     * @return array
     */
    private function groupSupplierWechatRecords(array $records): array
    {
        $groups = [];

        /** @var \app\services\supplier\SystemSupplierServices $supplierServices */
        $supplierServices = app()->make(\app\services\supplier\SystemSupplierServices::class);

        foreach ($records as $record) {
            $supplierId = $record['supplier_id'];
            $payChannel = $record['pay_channel'] ?? 'mini';

            if ($supplierId <= 0) {
                \think\facade\Log::warning("流水ID:{$record['id']} 供应商ID无效,跳过");
                continue;
            }

            // 获取供应商企业用户号
            $supplierInfo = $supplierServices->get($supplierId, ['id', 'supplier_name', 'ums_mer_no']);
            if (!$supplierInfo || !$supplierInfo['ums_mer_no']) {
                \think\facade\Log::warning("供应商ID:{$supplierId} 未配置企业用户号(ums_mer_no),跳过");
                continue;
            }

            $merNo = $supplierInfo['ums_mer_no'];
            $groupKey = (string)$supplierId;

            if (!isset($groups[$groupKey])) {
                $groups[$groupKey] = [
                    'supplier_id' => $supplierId,
                    'supplier_name' => $supplierInfo['supplier_name'] ?? '',
                    'mer_no' => $merNo,
                    'pay_channel' => $payChannel,
                    'batch_type' => 'supplier',
                    'records' => [],
                    'total_amount' => 0,
                ];
            } elseif (($groups[$groupKey]['pay_channel'] ?? '') !== $payChannel) {
                $groups[$groupKey]['pay_channel'] = 'mixed';
            }

            $groups[$groupKey]['records'][] = $record;
            $groups[$groupKey]['total_amount'] += floatval($record['number']);
        }

        return $groups;
    }

    /**
     * 处理单个供应商批次划付
     *
     * @param array $group 分组信息
     * @param \app\services\pay\WechatAmountTransferServices $transferServices
     * @return array
     */
    private function processSupplierBatch(array $group, $transferServices): array
    {
        $supplierId = $group['supplier_id'];
        $supplierName = $group['supplier_name'];
        $merNo = $group['mer_no'];
        $payChannel = $group['pay_channel'];
        $totalAmount = $group['total_amount'];
        $records = $group['records'];

        \think\facade\Log::info("处理供应商批次: 供应商ID={$supplierId}, 名称={$supplierName}, 商户号={$merNo}, 渠道={$payChannel}, 金额={$totalAmount}");

        if ($totalAmount <= 0) {
            \think\facade\Log::warning("供应商金额为0,跳过: supplier_id={$supplierId}");
            return ['success' => false, 'batch_id' => 0, 'error' => '金额为0'];
        }

        // 使用 WechatAmountTransferServices 的批次处理逻辑
        // 构建 group 结构兼容 processBatch 方法
        $orders = [];
        foreach ($records as $record) {
            $orders[] = [
                'order' => [
                    'id' => $record['order_id'] ?? 0,
                    'order_id' => $record['link_id'],
                    'supplier_id' => $supplierId,
                ],
                'amount' => floatval($record['number']),
                'flowing_water_id' => $record['id'],
                'pay_channel' => $record['pay_channel'] ?? $payChannel,
            ];
        }

        $batchGroup = [
            'mer_no' => $merNo,
            'pay_channel' => $payChannel,
            'batch_type' => 'supplier',
            'orders' => $orders,
        ];

        // 调用 processBatch 方法（需要通过反射或新增公开方法）
        // 这里直接创建批次记录和调用划付接口
        return $this->executeSupplierBatchTransfer($batchGroup, $transferServices);
    }

    /**
     * 执行供应商批次划付
     *
     * @param array $group 分组信息
     * @param \app\services\pay\WechatAmountTransferServices $transferServices
     * @return array
     */
    private function executeSupplierBatchTransfer(array $group, $transferServices): array
    {
        $merNo = $group['mer_no'];
        $payChannel = $group['pay_channel'];
        $batchType = $group['batch_type'];
        $orders = $group['orders'];

        // 计算总金额
        $totalAmount = 0;
        foreach ($orders as $item) {
            $totalAmount += $item['amount'];
        }

        \think\facade\Log::info("执行供应商划付: mer_no={$merNo}, channel={$payChannel}, amount={$totalAmount}");

        try {
            // 使用反射调用 processBatch 方法
            $reflection = new \ReflectionMethod($transferServices, 'processBatch');
            $reflection->setAccessible(true);
            $result = $reflection->invoke($transferServices, $group);

            return $result;
        } catch (\Exception $e) {
            \think\facade\Log::error("供应商批次划付失败: {$e->getMessage()}");
            return [
                'success' => false,
                'batch_id' => 0,
                'error' => $e->getMessage(),
            ];
        }
    }

    /**
     * 划付后更新流水状态
     *
     * @param array $records 流水记录
     * @param bool $success 是否成功
     * @param int $batchId 批次ID
     * @param string $error 错误信息
     * @return void
     */
    private function updateFlowingWaterAfterTransfer(array $records, bool $success, int $batchId = 0, string $error = ''): void
    {
        foreach ($records as $record) {
            if ($success) {
                $this->dao->update($record['id'], [
                    'status' => 1,  // 可提现
                    'division_status' => 2,  // 已处理
                    'division_time' => time(),
                ]);

                // 更新分账记录状态
                $this->updateShareRecordStatus($record['link_id'], 'success', '', 'online');

                \think\facade\Log::info("供应商流水划付成功: id={$record['id']}, link_id={$record['link_id']}");
            } else {
                // 失败时将 division_status 从 3(处理中) 回滚到 1(待处理)，允许后续重试
                $this->dao->update($record['id'], [
                    'division_status' => 1,  // 回滚到待处理，允许重试
                ]);

                \think\facade\Log::error("供应商流水划付失败: id={$record['id']}, link_id={$record['link_id']}, error={$error}");

                // 更新分账记录状态
                $this->updateShareRecordStatus($record['link_id'], 'failed', $error, 'online');
            }
        }
    }

    /**
     * 更新分账记录表状态
     * @param string $orderNo 订单号
     * @param string $status 状态：success-成功, failed-失败
     * @param string $error 错误信息
     * @param string $divisionType 分账类型：online-在线分账, subsidy-平台补贴
     * @return void
     */
    private function updateShareRecordStatus(string $orderNo, string $status, string $error = '', string $divisionType = ''): void
    {
        try {
            /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
            $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);

            // 构建查询条件
            $where = ['order_no' => $orderNo];
            if ($divisionType) {
                $where['division_type'] = $divisionType;
            }

            // 查询匹配的记录 (通过 __call 魔术方法调用 dao 的 getList 方法)
            $records = $shareRecordServices->getList($where, '*', 0, 0);

            if (empty($records)) {
                \think\facade\Log::warning("未找到分账记录: order_no={$orderNo}, division_type={$divisionType}");
                return;
            }

            // 更新所有匹配的记录
            foreach ($records as $record) {
                // 已经成功的不被失败覆盖，避免不同子流水相互影响
                if (($record['status'] ?? '') === 'success' && $status === 'failed') {
                    \think\facade\Log::warning("分账记录已成功，跳过失败覆盖: id={$record['id']}, order_no={$orderNo}");
                    continue;
                }

                $updateData = [
                    'status' => $status,
                    'updated_at' => time(),
                ];

                if ($status === 'failed' && $error) {
                    $updateData['last_unionpay_error'] = $error;
                }

                // 使用 update 方法更新单条记录
                $shareRecordServices->update(['id' => $record['id']], $updateData);
                \think\facade\Log::info("同步更新分账记录状态: id={$record['id']}, order_no={$orderNo}, division_type={$divisionType}, status={$status}");
            }
        } catch (\Exception $e) {
            \think\facade\Log::error("更新分账记录状态失败: order_no={$orderNo}, error={$e->getMessage()}");
        }
    }

    /**
     * 更新分账记录退款状态（支持部分退款）
     *
     * 修复问题：子订单退款时不再直接将主订单分账标记为refund_cancelled
     * 而是累计退款金额，只有完全退款时才标记为refund_cancelled
     *
     * @param string $orderNo 订单号（主订单号）
     * @param string $refundAmount 本次退款金额
     * @param string $divisionType 分账类型：online-在线分账, subsidy-平台补贴
     * @param string $payType 支付类型：welfare-福利金, yue-余额, weixin/alipay/ums-在线支付
     * @return void
     */
    private function updateShareRecordRefundAmount(string $orderNo, string $refundAmount, string $divisionType = '', string $payType = ''): void
    {
        try {
            /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
            $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);

            // 构建查询条件
            $where = ['order_no' => $orderNo];
            if ($divisionType) {
                $where['division_type'] = $divisionType;
            }

            // 查询匹配的记录
            $records = $shareRecordServices->getList($where, '*', 0, 0);

            if (empty($records)) {
                \think\facade\Log::warning("未找到分账记录，跳过退款状态更新: order_no={$orderNo}, division_type={$divisionType}");
                return;
            }

            \think\facade\Log::info("分账记录查询: order_no={$orderNo}, division_type={$divisionType}, pay_type={$payType}, 匹配数量=" . count($records));

            // 根据payType精确匹配对应的分账记录
            // welfare -> 匹配remarks包含'福利金'的记录
            // yue -> 匹配remarks包含'余额'的记录
            // weixin/alipay/ums -> 匹配online类型的记录
            $targetRecord = null;
            if ($payType === 'welfare') {
                foreach ($records as $record) {
                    if (strpos($record['remarks'] ?? '', '福利金') !== false) {
                        $targetRecord = $record;
                        break;
                    }
                }
            } elseif ($payType === 'yue') {
                foreach ($records as $record) {
                    if (strpos($record['remarks'] ?? '', '余额') !== false) {
                        $targetRecord = $record;
                        break;
                    }
                }
            } elseif (in_array($payType, ['weixin', 'alipay', 'ums'])) {
                foreach ($records as $record) {
                    if (($record['division_type'] ?? '') === 'online') {
                        $targetRecord = $record;
                        break;
                    }
                }
            }

            // 如果没有精确匹配到，且只有一条记录，就使用这条记录
            if (!$targetRecord && count($records) === 1) {
                $targetRecord = $records[0];
            }

            if (!$targetRecord) {
                \think\facade\Log::warning("未找到匹配的分账记录: order_no={$orderNo}, pay_type={$payType}");
                return;
            }

            \think\facade\Log::info("精确匹配分账记录: id={$targetRecord['id']}, remarks={$targetRecord['remarks']}, pay_type={$payType}");

            // 更新单条记录
            $record = $targetRecord;
            $currentRefunded = $record['refunded_amount'] ?? '0.00';
            $originalShareAmount = $record['share_amount'] ?? '0.00';
            $originalTotalAmount = $record['total_amount'] ?? '0.00';
            $originalPlatformAmount = $record['platform_amount'] ?? '0.00';

            // 累计退款金额
            $newRefundedAmount = bcadd($currentRefunded, $refundAmount, 2);

            // 直接从原金额中扣减本次退款金额
            // share_amount = 原share_amount - 本次退款金额（供应商应退部分）
            // total_amount = 原total_amount - 本次退款金额（保持与share_amount同步扣减，避免精度误差）
            // platform_amount = 原platform_amount - 对应的平台扣减金额

            // 计算新的 share_amount（供应商实收）
            $newShareAmount = bcsub($originalShareAmount, $refundAmount, 2);
            if (bccomp($newShareAmount, '0', 2) < 0) {
                $newShareAmount = '0.00';
            }

            // total_amount 直接扣减退款金额，与 share_amount 保持一致
            // 避免使用比例计算导致的精度误差
            $newTotalAmount = bcsub($originalTotalAmount, $refundAmount, 2);
            if (bccomp($newTotalAmount, '0', 2) < 0) {
                $newTotalAmount = '0.00';
            }

            $refundRatio = '0';
            
            if (bccomp($originalTotalAmount, '0', 2) > 0) {
                $refundRatio = bcdiv($refundAmount, $originalTotalAmount, 6);
            }

            // platform_amount 按比例计算扣减金额
            $newPlatformAmount = $originalPlatformAmount;
            if (bccomp($originalTotalAmount, '0', 2) > 0 && bccomp($originalPlatformAmount, '0', 2) > 0) {
                $platformAmountDeduction = bcmul($originalPlatformAmount, $refundRatio, 2);
                $newPlatformAmount = bcsub($originalPlatformAmount, $platformAmountDeduction, 2);
                if (bccomp($newPlatformAmount, '0', 2) < 0) {
                    $newPlatformAmount = '0.00';
                }
            }

            // 直接使用传入的退款金额作为总退款金额
            // 因为传入的 refundAmount 已经是该支付方式的总退款（供应商+平台）
            $newRefundedAmount = bcadd($currentRefunded, $refundAmount, 2);

            \think\facade\Log::info("分账金额重新计算: 原share={$originalShareAmount}, 退款金额={$refundAmount}, 新share={$newShareAmount}");
            \think\facade\Log::info("订单金额重新计算: 原total={$originalTotalAmount}, 扣减={$refundAmount}, 新total={$newTotalAmount}");
            \think\facade\Log::info("平台金额重新计算: 原platform={$originalPlatformAmount}, 新platform={$newPlatformAmount}");
            \think\facade\Log::info("refunded_amount更新: 原值={$currentRefunded}, 本期退款={$refundAmount}, 新值={$newRefundedAmount}");

            // 判断退款状态
            $refundStatus = 'none';
            $newStatus = $record['status'] ?? 'pending';

            if (bccomp($newRefundedAmount, '0', 2) > 0) {
                if (bccomp($newShareAmount, '0', 2) <= 0) {
                    // 全额退款（share_amount 已经为0）
                    $refundStatus = 'full';
                    $newStatus = 'refund_cancelled';
                    // 全额退款时，platform_amount 和 total_amount 也应该清零
                    $newPlatformAmount = '0.00';
                    $newTotalAmount = '0.00';
                    \think\facade\Log::info("分账记录全额退款: id={$record['id']}, order_no={$orderNo}, platform和total已清零");
                } else {
                    // 部分退款
                    $refundStatus = 'partial';
                    \think\facade\Log::info("分账记录部分退款: id={$record['id']}, order_no={$orderNo}, 剩余share={$newShareAmount}");
                }
            }

            $updateData = [
                'total_amount' => $newTotalAmount,
                'share_amount' => $newShareAmount,
                'platform_amount' => $newPlatformAmount,
                'refunded_amount' => $newRefundedAmount,
                'refund_status' => $refundStatus,
                'updated_at' => time(),
            ];

            // 只有全额退款时才更新主状态为refund_cancelled
            if ($refundStatus === 'full') {
                $updateData['status'] = $newStatus;
            }

            $shareRecordServices->update(['id' => $record['id']], $updateData);
            \think\facade\Log::info("更新分账记录完成: id={$record['id']}, total={$newTotalAmount}, share={$newShareAmount}, platform={$newPlatformAmount}, refunded={$newRefundedAmount}");
        } catch (\Exception $e) {
            \think\facade\Log::error("更新分账记录退款状态失败: order_no={$orderNo}, error={$e->getMessage()}");
        }
    }

    /**
     * 更新所有分账记录的 refunded_amount（仅本次实际退款的支付方式）
     *
     * 原因：
     * 当分账记录的 share_amount=0 时，createCombinationRefundFlowingWater 中会跳过创建退款流水
     * 但退款金额中平台的份额需要被记录到 refunded_amount
     *
     * 解决方案：
     * 这个方法只更新本次退款中**实际创建了退款流水**的支付方式对应的分账记录
     * 通过 $successCount 来跟踪实际处理成功的支付方式数量
     *
     * @param string $orderNo 订单号
     * @param array $refundAmounts 各支付方式的退款金额 ['welfare' => x, 'balance' => x, 'online' => x]
     * @param int $actualProcessedCount 实际创建退款流水的数量
     */
    private function updateAllShareRecordRefundedAmount(string $orderNo, array $refundAmounts, int $actualProcessedCount = 0): void
    {
        try {
            \think\facade\Log::info("开始更新 refunded_amount: order_no={$orderNo}, refund_amounts=" . json_encode($refundAmounts) . ", 实际处理数={$actualProcessedCount}");

            /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
            $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);

            // 查询该订单的所有分账记录
            $records = $shareRecordServices->getList(['order_no' => $orderNo], '*', 0, 0);

            if (empty($records)) {
                \think\facade\Log::warning("未找到分账记录，跳过更新: order_no={$orderNo}");
                return;
            }

            \think\facade\Log::info("找到 " . count($records) . " 条分账记录");

            // 获取各支付方式的退款金额
            $welfareRefund = $refundAmounts['welfare'] ?? '0.00';
            $balanceRefund = $refundAmounts['balance'] ?? '0.00';
            $onlineRefund = $refundAmounts['online'] ?? '0.00';

            // 如果本次没有实际处理任何退款流水，直接返回
            if ($actualProcessedCount == 0) {
                \think\facade\Log::info("本次没有创建任何退款流水，跳过更新 refunded_amount");
                return;
            }

            foreach ($records as $record) {
                $recordId = $record['id'] ?? 0;
                $divisionType = $record['division_type'] ?? '';
                $remarks = $record['remarks'] ?? '';
                $currentRefunded = $record['refunded_amount'] ?? '0.00';

                // 根据分账记录类型确定需要累加的退款金额
                $refundToAdd = '0.00';

                if (strpos($remarks, '福利金') !== false) {
                    $refundToAdd = $welfareRefund;
                } elseif (strpos($remarks, '余额') !== false) {
                    $refundToAdd = $balanceRefund;
                } elseif ($divisionType === 'online') {
                    $refundToAdd = $onlineRefund;
                } else {
                    if ($divisionType === 'subsidy') {
                        $refundToAdd = $welfareRefund;
                    } elseif ($divisionType === 'online') {
                        $refundToAdd = $onlineRefund;
                    }
                }

                // 如果退款金额为 0，跳过
                if (bccomp($refundToAdd, '0', 2) <= 0) {
                    \think\facade\Log::info("分账记录退款金额为0，跳过: id={$recordId}, division_type={$divisionType}");
                    continue;
                }

                // 计算新的 refunded_amount（累加）
                $newRefundedAmount = bcadd($currentRefunded, $refundToAdd, 2);

                // 判断退款状态
                $currentShareAmount = $record['share_amount'] ?? '0.00';
                $newShareAmount = $currentShareAmount;
                $refundStatus = 'none';
                $updateStatus = false;

                if (bccomp($newRefundedAmount, '0', 2) > 0) {
                    if (bccomp($newShareAmount, '0', 2) <= 0) {
                        $refundStatus = 'full';
                        $updateStatus = true;
                        \think\facade\Log::info("分账记录全额退款: id={$recordId}, order_no={$orderNo}");
                    } else {
                        $refundStatus = 'partial';
                        \think\facade\Log::info("分账记录部分退款: id={$recordId}, order_no={$orderNo}, 新refunded={$newRefundedAmount}");
                    }
                }

                // 构建更新数据（只更新 refunded_amount，不修改其他字段）
                $updateData = [
                    'refunded_amount' => $newRefundedAmount,
                    'refund_status' => $refundStatus,
                    'updated_at' => time(),
                ];

                if ($updateStatus) {
                    $updateData['status'] = 'refund_cancelled';
                }

                $shareRecordServices->update(['id' => $recordId], $updateData);

                \think\facade\Log::info("更新 refunded_amount 完成: id={$recordId}, refunded={$newRefundedAmount}");
            }

            \think\facade\Log::info("更新 refunded_amount 完成: order_no={$orderNo}");
        } catch (\Exception $e) {
            \think\facade\Log::error("更新 refunded_amount 失败: order_no={$orderNo}, error={$e->getMessage()}");
        }
    }

    /**
     * 手动触发分账/放款（按时间范围）
     *
     * 处理逻辑：
     * 1. 福利金/余额(status=0)：查询流水表，直接放款 → status=1
     * 2. 供应商微信支付：从 eb_supplier_flowing_water 表查询，只处理供应商应得金额（number字段）
     *
     * 注意：
     * - 供应商微信支付只处理供应商部分，平台部分由 WechatAmountTransferServices 处理
     * - 传了时间范围就不检查免责期
     *
     * @param array $params 参数：start_time, end_time, supplier_id
     * @return array
     */
    public function manualProcessDivision(array $params): array
    {
        $startTime = $params['start_time'] ?? '';
        $endTime = $params['end_time'] ?? '';
        $supplierId = $params['supplier_id'] ?? '';

        // 将前端传递的斜杠格式转换为横杠格式（2026/01/01 -> 2026-01-01）
        if ($startTime) {
            $startTime = str_replace('/', '-', $startTime);
        }
        if ($endTime) {
            $endTime = str_replace('/', '-', $endTime);
        }

        // 提取日期部分
        $startDate = $startTime ? date('Y-m-d', strtotime($startTime)) : '';
        $endDate = $endTime ? date('Y-m-d', strtotime($endTime)) : '';

        \think\facade\Log::info('=== 手动触发供应商分账/放款任务 ===');
        \think\facade\Log::info("时间范围: {$startDate} ~ {$endDate}");
        \think\facade\Log::info("供应商ID: " . ($supplierId ?: '全部'));

        try {
            // ========== 1. 处理福利金/余额放款 ==========
            \think\facade\Log::info('--- 开始处理福利金/余额放款 ---');

            $welfareWhere = [
                ['division_status', '=', 1],  // 待放款
                ['pm', '=', 1],  // 收入
                ['type', '=', 1],  // 支付订单
                ['status', '=', 0],  // 冻结中(福利金/余额)
                ['pay_type', 'in', ['welfare', 'yue']],  // 福利金/余额
            ];

            if ($supplierId) {
                $welfareWhere[] = ['supplier_id', '=', $supplierId];
            }

            if ($startDate && $endDate) {
                $startTimeStamp = strtotime($startDate . ' 00:00:00');
                $endTimeStamp = strtotime($endDate . ' 23:59:59');
                $welfareWhere[] = ['add_time', 'between', [$startTimeStamp, $endTimeStamp]];
            }

            $welfareRecords = $this->dao->getList($welfareWhere, '*', 0, 0);
            $this->logWelfareRecordSummary($welfareRecords, '原始查询');
            \think\facade\Log::info('找到 ' . count($welfareRecords) . ' 条福利金/余额流水记录（原始查询）');
            $welfareRecords = $this->filterWelfareRecords($welfareRecords);
            \think\facade\Log::info('过滤后保留 ' . count($welfareRecords) . ' 条实际福利金/余额流水记录');
            foreach ($welfareRecords as $record) {
                \think\facade\Log::info("福利金/余额候选流水: id={$record['id']}, order_id={$record['link_id']}, pay_type={$record['pay_type']}, status={$record['status']}, division_status={$record['division_status']}");
            }

            $welfareBalanceProcessed = 0;
            $welfareBalanceSuccess = 0;
            foreach ($welfareRecords as $record) {
                // 检查订单是否满足分账条件（特别是子订单的收货状态）
                if ($this->shouldSkipByOrderStatus($record)) {
                    continue;
                }
                
                $orderNo = $record['link_id'] ?? '';
                if ($orderNo && $this->isShareRecordAlreadySuccess($orderNo, 'subsidy')) {
                    \think\facade\Log::info("订单已有成功分账记录（补贴），跳过福利金/余额放款: order_id={$orderNo}");
                    continue;
                }
                $welfareBalanceProcessed++;
                try {
                    $this->processWelfareBalanceRelease($record);
                    $welfareBalanceSuccess++;
                } catch (\Exception $e) {
                    \think\facade\Log::error("福利金/余额放款失败: id={$record['id']}, error={$e->getMessage()}");
                }
            }
            \think\facade\Log::info("福利金/余额放款完成: 成功 {$welfareBalanceSuccess} 条");

            // ========== 2. 处理供应商微信支付划付（独立于平台） ==========
            \think\facade\Log::info('--- 开始处理供应商微信支付划付（独立） ---');

            // 调用供应商专用的微信划付方法（只处理供应商应得金额）
            $supplierTransferResult = $this->processSupplierWechatTransfer(
                $startDate,
                $endDate,
                $supplierId ? (int)$supplierId : null
            );

            $supplierBatches = count($supplierTransferResult['batches'] ?? []);
            $supplierSuccess = $supplierTransferResult['success'] ?? 0;
            $supplierFailed = $supplierTransferResult['failed'] ?? 0;

            \think\facade\Log::info("供应商微信划付完成: 成功 {$supplierSuccess} 批次, 失败 {$supplierFailed} 批次");

            $result = [
                'welfare_balance_total' => $welfareBalanceProcessed,
                'welfare_balance_success' => $welfareBalanceSuccess,
                'supplier_online_batches' => $supplierBatches,
                'supplier_online_success' => $supplierSuccess,
                'supplier_online_failed' => $supplierFailed,
            ];

            \think\facade\Log::info("手动分账/放款完成: " . json_encode($result, JSON_UNESCAPED_UNICODE));
            \think\facade\Log::info('=== 手动供应商分账/放款任务执行完成 ===');

            return $result;

        } catch (\Exception $e) {
            \think\facade\Log::error('手动分账/放款任务执行失败: ' . $e->getMessage());
            throw $e;
        }
    }



    /**
     * 创建组合支付退款的供应商流水记录（基于原流水状态处理）
     * @param array $order 订单信息
     * @param float $refundPrice 退款金额
     * @return bool
     * @throws \Exception
     */
    public function createCombinationRefundFlowingWater(array $order, float $refundPrice, array $refundAmounts = []): bool
    {
        \think\facade\Log::info('========================================');
        \think\facade\Log::info('=== 开始创建供应商退款流水 ===');
        \think\facade\Log::info("订单号: {$order['order_id']}");
        \think\facade\Log::info("供应商ID: {$order['supplier_id']}");
        \think\facade\Log::info("退款金额: {$refundPrice}");
        \think\facade\Log::info("各支付方式实际退款金额: " . json_encode($refundAmounts));

        if ($order['supplier_id'] <= 0) {
            \think\facade\Log::info('供应商ID为0，跳过退款流水创建');
            return true;
        }

        $payPrice = $order['pay_price'] ?? 0;
        if ($payPrice <= 0) {
            \think\facade\Log::warning("订单支付金额异常，后续将尝试使用收入流水金额: order_id={$order['order_id']}, pay_price={$payPrice}");
        }

        $settlePrice = $order['settle_price'] ?? 0;

        // 对于子订单退款，应该查找与该子订单关联的收入流水
        // 即使 settle_price=0 也需要正确处理分账记录
        $currentOrderId = $order['order_id'];
        $originalOrderId = preg_replace('/_\d+$/', '', $currentOrderId);
        $isSubOrder = ($originalOrderId !== $currentOrderId);

        \think\facade\Log::info('=== 订单支付信息 ===');
        \think\facade\Log::info("订单总金额(原始pay_price): {$payPrice}");
        \think\facade\Log::info("供应商结算价: {$settlePrice}");
        \think\facade\Log::info("是否子订单: " . ($isSubOrder ? '是' : '否'));

        if ($isSubOrder) {
            \think\facade\Log::info("检测到子订单号，使用子订单号查询收入流水: {$currentOrderId}");
        }

        // 查询该订单的所有收入流水（对于子订单，使用子订单号；对于主订单，使用原订单号）
        \think\facade\Log::info('=== 查询订单收入流水 ===');
        \think\facade\Log::info("查询link_id: {$currentOrderId}");
        $incomeRecords = $this->dao->getList([
            'link_id' => $currentOrderId,  // 使用当前订单号，无论是主订单还是子订单
            'pm' => 1,  // 收入
            'type' => 1,  // 支付订单
        ], '*', 0, 0);

        if (empty($incomeRecords)) {
            \think\facade\Log::warning("未找到订单的收入流水记录: {$order['order_id']}，尝试使用原订单号查询");
            
            // 如果没找到，尝试使用原订单号查询（兼容历史数据）
            $incomeRecords = $this->dao->getList([
                'link_id' => $originalOrderId,
                'pm' => 1,  // 收入
                'type' => 1,  // 支付订单
            ], '*', 0, 0);
            
            if (empty($incomeRecords)) {
                \think\facade\Log::warning("仍未找到订单的收入流水记录: {$order['order_id']}");
                return false;
            } else {
                \think\facade\Log::info("使用原订单号查询到收入流水: {$originalOrderId}");
            }
        } else {
            \think\facade\Log::info("使用子订单号查询到收入流水: {$currentOrderId}");
        }

        \think\facade\Log::info("找到 " . count($incomeRecords) . " 条收入流水记录");

        // 直接使用收入流水的金额来计算各支付方式的比例
        // 这样可以避免子订单支付金额字段不正确导致的问题
        $totalFlowingAmount = '0.00';
        $flowingAmounts = [];
        foreach ($incomeRecords as $record) {
            $payType = $record['pay_type'];
            $amount = $record['number'] ?? '0.00';
            $flowingAmounts[$payType] = $amount;
            $totalFlowingAmount = bcadd($totalFlowingAmount, $amount, 2);
            \think\facade\Log::info("流水ID: {$record['id']}, 支付方式: {$payType}, 金额: {$amount}, 状态: {$record['status']}, 分账状态: {$record['division_status']}");
        }

        \think\facade\Log::info("收入流水总金额: {$totalFlowingAmount}");

        // 以收入流水为准的实际支付金额（用于子订单/组合支付纠偏）
        $effectivePayPrice = (string)$payPrice;
        if (bccomp($totalFlowingAmount, '0', 2) > 0) {
            if (bccomp((string)$payPrice, '0', 2) <= 0 || bccomp($totalFlowingAmount, (string)$payPrice, 2) != 0) {
                \think\facade\Log::warning("使用收入流水总金额作为实际支付金额: pay_price={$payPrice}, flowing_total={$totalFlowingAmount}");
            }
            $effectivePayPrice = $totalFlowingAmount;
        }
        if (bccomp($effectivePayPrice, '0', 2) <= 0) {
            \think\facade\Log::warning("订单支付金额异常，跳过创建退款流水: order_id={$order['order_id']}, effective_pay_price={$effectivePayPrice}");
            return false;
        }

        // ================================================================
        // 先定责任，不看渠道
        // ================================================================
        \think\facade\Log::info('=== 新方案：计算责任分担 ===');

        // 步骤1: 计算责任分担
        // 供应商应扣 = 该商品对应的"供应商结算额"（按比例）
        // 平台应扣 = 商品退款额 − 供应商应扣
        // 使用先乘后除的方式，避免精度损失
        $supplierDeduction = '0.00';
        if (bccomp((string)$effectivePayPrice, '0', 2) > 0) {
            // 先计算 settlePrice * refundPrice，再除以 payPrice
            $temp = bcmul((string)$settlePrice, (string)$refundPrice, 4);
            $supplierDeduction = bcdiv($temp, (string)$effectivePayPrice, 2);
        }
        
        // 安全检查：供应商应扣不应超过退款金额
        if (bccomp($supplierDeduction, (string)$refundPrice, 2) > 0) {
            \think\facade\Log::warning("供应商应扣超过退款金额: {$supplierDeduction} > {$refundPrice}，使用退款金额");
            $supplierDeduction = (string)$refundPrice;
        }

        $platformDeduction = bcsub((string)$refundPrice, $supplierDeduction, 2);
        
        // 计算结算比例用于日志
        $settleRatio = '0.0000';
        if (bccomp((string)$effectivePayPrice, '0', 2) > 0) {
            $settleRatio = bcdiv((string)$settlePrice, (string)$effectivePayPrice, 4);
        }

        \think\facade\Log::info("退款金额: {$refundPrice}");
        \think\facade\Log::info("结算比例: {$settleRatio}");
        \think\facade\Log::info("供应商应扣（责任）: {$supplierDeduction}");
        \think\facade\Log::info("平台应扣（责任）: {$platformDeduction}");

        // 步骤2: 查询分账记录余额
        // 对于子订单，使用子订单号查询分账记录
        $queryOrderId = $isSubOrder ? $currentOrderId : $originalOrderId;
        
        /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
        $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);
        $shareRecords = $shareRecordServices->getList(['order_no' => $queryOrderId], '*', 0, 0);

        \think\facade\Log::info("查询分账记录: order_no={$queryOrderId}, 找到 " . count($shareRecords) . " 条");

        // 构建分账余额映射: [division_type => [pay_type => remaining_amount]]
        $shareBalances = [];
        $totalShareBalance = '0.00';

        foreach ($shareRecords as $r) {
            $divType = $r['division_type'] ?? '';
            $shareAmt = $r['share_amount'] ?? '0.00';
            $remarks = $r['remarks'] ?? '';

            // 从分账记录推断支付类型
            $inferredPayType = $this->inferPayTypeFromDivision($divType, $remarks);

            if (!isset($shareBalances[$divType])) {
                $shareBalances[$divType] = [];
            }
            $shareBalances[$divType][$inferredPayType] = $shareAmt;
            $totalShareBalance = bcadd($totalShareBalance, $shareAmt, 2);

            $logShareAmt = $shareAmt;
            \think\facade\Log::info("分账记录: division_type={$divType}, share_amount={$logShareAmt}, remarks={$remarks}, inferred_pay_type={$inferredPayType}");
        }

        \think\facade\Log::info("分账余额总计: {$totalShareBalance}");

// 步骤3: 按分账余额比例分配供应商应扣
        // 同时计算平台应扣的分配，确保 Welfare 能处理平台的退款部分
        $actualSupplierDeduction = '0.00';
        $actualPlatformDeduction = '0.00';
        $deductions = []; // [division_type => [pay_type => ['supplier' => x, 'platform' => x]]]

        if (bccomp($totalShareBalance, '0', 2) > 0) {
            // 按分账余额比例分配供应商应扣
            if (bccomp($supplierDeduction, '0', 2) > 0) {
                foreach ($shareBalances as $divType => $payTypes) {
                    $deductions[$divType] = [];
                    foreach ($payTypes as $pType => $balance) {
                        if (bccomp($balance, '0', 2) <= 0) {
                            $deductions[$divType][$pType] = ['supplier' => '0.00', 'platform' => '0.00'];
                            continue;
                        }

                        // 计算该分账记录应承担的扣减比例
                        $ratio = bcdiv($balance, $totalShareBalance, 6);
                        $supplierDed = bcmul($supplierDeduction, $ratio, 2);

                        // 转换为新的结构
                        $deductions[$divType][$pType] = ['supplier' => $supplierDed, 'platform' => '0.00'];
                        $actualSupplierDeduction = bcadd($actualSupplierDeduction, $supplierDed, 2);

                        \think\facade\Log::info("分配供应商扣减: division_type={$divType}, pay_type={$pType}, ratio={$ratio}, deduction={$supplierDed}");
                    }
                }

                // 精度补偿：如果计算结果与预期不符，补偿到余额最大的分账记录
                $deductionDiff = bcsub($supplierDeduction, $actualSupplierDeduction, 2);
                if (bccomp($deductionDiff, '0', 2) > 0 && bccomp($deductionDiff, '0.05', 2) <= 0) {
                    \think\facade\Log::info("供应商扣减精度补偿: diff={$deductionDiff}");
                    // 找到余额最大的分账记录进行补偿
                    $maxBalance = '0.00';
                    $maxDivType = '';
                    $maxPayType = '';
                    foreach ($shareBalances as $divType => $payTypes) {
                        foreach ($payTypes as $pType => $balance) {
                            $currentDeduction = $deductions[$divType][$pType]['supplier'] ?? '0.00';
                            $available = bcsub($balance, $currentDeduction, 2);
                            if (bccomp($available, $maxBalance, 2) > 0) {
                                $maxBalance = $available;
                                $maxDivType = $divType;
                                $maxPayType = $pType;
                            }
                        }
                    }
                    if ($maxDivType && $maxPayType && bccomp($maxBalance, $deductionDiff, 2) >= 0) {
                        $deductions[$maxDivType][$maxPayType]['supplier'] = bcadd($deductions[$maxDivType][$maxPayType]['supplier'], $deductionDiff, 2);
                        $actualSupplierDeduction = bcadd($actualSupplierDeduction, $deductionDiff, 2);
                        \think\facade\Log::info("供应商扣减补偿到: division_type={$maxDivType}, pay_type={$maxPayType}");
                    }
                }
            }

            // 按分账余额比例分配平台应扣（使用原始的 platformDeduction，不是 finalPlatformDeduction）
            if (bccomp($platformDeduction, '0', 2) > 0) {
                foreach ($shareBalances as $divType => $payTypes) {
                    foreach ($payTypes as $pType => $balance) {
                        if (bccomp($balance, '0', 2) <= 0) {
                            continue;
                        }
                        if (!isset($deductions[$divType][$pType])) {
                            $deductions[$divType][$pType] = ['supplier' => '0.00', 'platform' => '0.00'];
                        }

                        // 计算该分账记录应承担的平台扣减比例
                        $ratio = bcdiv($balance, $totalShareBalance, 6);
                        $platformDed = bcmul($platformDeduction, $ratio, 2);

                        // 限制供应商+平台不超过余额
                        $currentTotal = bcadd($deductions[$divType][$pType]['supplier'], $deductions[$divType][$pType]['platform'], 2);
                        $available = bcsub($balance, $currentTotal, 2);
                        // 确保可用余额不为负数
                        if (bccomp($available, '0', 2) < 0) {
                            $available = '0.00';
                        }
                        if (bccomp($platformDed, $available, 2) > 0) {
                            $platformDed = $available;
                        }

                        $deductions[$divType][$pType]['platform'] = $platformDed;
                        $actualPlatformDeduction = bcadd($actualPlatformDeduction, $platformDed, 2);

                        \think\facade\Log::info("分配平台扣减: division_type={$divType}, pay_type={$pType}, ratio={$ratio}, deduction={$platformDed}");
                    }
                }

                // 平台扣减精度补偿
                $platformDiff = bcsub($platformDeduction, $actualPlatformDeduction, 2);
                if (bccomp($platformDiff, '0', 2) > 0 && bccomp($platformDiff, '0.05', 2) <= 0) {
                    \think\facade\Log::info("平台扣减精度补偿: diff={$platformDiff}");
                    // 找到可用余额最大的分账记录进行补偿
                    $maxAvailable = '0.00';
                    $maxDivType = '';
                    $maxPayType = '';
                    foreach ($shareBalances as $divType => $payTypes) {
                        foreach ($payTypes as $pType => $balance) {
                            $currentTotal = bcadd($deductions[$divType][$pType]['supplier'] ?? '0.00', $deductions[$divType][$pType]['platform'] ?? '0.00', 2);
                            $available = bcsub($balance, $currentTotal, 2);
                            // 确保可用余额不为负数
                            if (bccomp($available, '0', 2) < 0) {
                                $available = '0.00';
                            }
                            if (bccomp($available, $maxAvailable, 2) > 0) {
                                $maxAvailable = $available;
                                $maxDivType = $divType;
                                $maxPayType = $pType;
                            }
                        }
                    }
                    if ($maxDivType && $maxPayType && bccomp($maxAvailable, '0', 2) > 0 && bccomp($maxAvailable, $platformDiff, 2) >= 0) {
                        $deductions[$maxDivType][$maxPayType]['platform'] = bcadd($deductions[$maxDivType][$maxPayType]['platform'], $platformDiff, 2);
                        $actualPlatformDeduction = bcadd($actualPlatformDeduction, $platformDiff, 2);
                        \think\facade\Log::info("平台扣减补偿到: division_type={$maxDivType}, pay_type={$maxPayType}");
                    }
                }
            }
        }

        // 如果分账余额不足，平台需要临时垫付
        $platformSubsidy = '0.00';
        if (bccomp($actualSupplierDeduction, $supplierDeduction, 2) < 0) {
            $platformSubsidy = bcsub($supplierDeduction, $actualSupplierDeduction, 2);
            \think\facade\Log::warning("分账余额不足，平台需临时垫付: {$platformSubsidy}");
        }

        // 最终平台应扣 = 原平台应扣 + 垫付金额
        $finalPlatformDeduction = bcadd($platformDeduction, $platformSubsidy, 2);

        \think\facade\Log::info("=== 责任分担计算结果 ===");
        \think\facade\Log::info("供应商实际应扣: {$actualSupplierDeduction}");
        \think\facade\Log::info("平台最终应扣: {$finalPlatformDeduction}");
        \think\facade\Log::info("扣减明细: " . json_encode($deductions, JSON_UNESCAPED_UNICODE));

        // 保存到实例变量，供外部调用者获取
        $this->currentSupplierDeduction = $actualSupplierDeduction;
        $this->currentPlatformDeduction = $finalPlatformDeduction;
        $this->currentDeductions = $deductions;

        // ================================================================
        //  settle_price=0 时特殊处理
        // 供应商流水不需要创建，但分账记录仍需更新（退款金额全部归属平台）
        if ($settlePrice <= 0) {
            \think\facade\Log::info("供应商结算价为0，仅更新分账记录，不创建供应商流水: settle_price={$settlePrice}");

            // 确定支付类型用于更新分账记录
            $payType = $order['pay_type'] ?? 'ums';
            if (in_array($payType, ['weixin', 'alipay', 'ums'])) {
                $divisionType = 'online';
            } else {
                $divisionType = 'subsidy';
            }

            // 更新分账记录的退款金额（这个退款金额全部是平台的）
            $this->updateShareRecordRefundAmount($currentOrderId, (string)$refundPrice, $divisionType, $payType);

            \think\facade\Log::info('========================================');
            \think\facade\Log::info('=== ✅ 供应商退款流水处理完成（settle_price=0，仅更新分账记录）===');
            \think\facade\Log::info('========================================');

            return true;
        }

        // 计算供应商应退款金额
        \think\facade\Log::info('=== 计算退款金额 ===');
        $settleRatio = bcdiv((string)$settlePrice, (string)$effectivePayPrice, 4);

        // 结算比例不应超过1（100%），如果超过说明数据有问题
        // 这种情况通常发生在子订单的 settle_price 错误地使用了主订单的值
        if (bccomp($settleRatio, '1', 4) > 0) {
            \think\facade\Log::warning("⚠️ 结算比例异常: {$settleRatio} > 1，settle_price={$settlePrice}, pay_price={$effectivePayPrice}");
            \think\facade\Log::warning("⚠️ 将使用 1.0 作为结算比例（供应商应退 = 实际退款金额）");
            $settleRatio = '1.0000';
        }

// 使用先乘后除的方式计算供应商应退，避免精度损失
        $temp = bcmul((string)$settlePrice, (string)$refundPrice, 4);
        $supplierRefund = bcdiv($temp, (string)$effectivePayPrice, 2);
        
        // 安全检查
        if (bccomp($supplierRefund, (string)$refundPrice, 2) > 0) {
            $supplierRefund = (string)$refundPrice;
        }

        \think\facade\Log::info("结算比例: {$settleRatio}");
        \think\facade\Log::info("供应商应退总额: {$supplierRefund}");

        // 根据实际退款支付方式决定供应商分账扣款
        // 如果传入了 refundAmounts，表示已知各支付方式的实际退款金额
        // 只需要处理有实际退款的支付方式，而不是按比例分配
        $welfareSupplierRefund = '0.00';
        $balanceSupplierRefund = '0.00';
        $onlineSupplierRefund = '0.00';

        // 获取实际退款金额
        $actualWelfareRefund = $refundAmounts['welfare'] ?? '0.00';
        $actualBalanceRefund = $refundAmounts['balance'] ?? '0.00';
        $actualOnlineRefund = $refundAmounts['online'] ?? '0.00';

        \think\facade\Log::info("实际退款金额: welfare={$actualWelfareRefund}, balance={$actualBalanceRefund}, online={$actualOnlineRefund}");

        // 计算实际退款的总金额
        $actualRefundTotal = bcadd(bcadd($actualWelfareRefund, $actualBalanceRefund, 2), $actualOnlineRefund, 2);

// 只使用供应商应退金额创建退款流水
        // 平台应扣金额不体现在退款流水中，由平台自己承担
        if (!empty($refundAmounts) && bccomp($actualRefundTotal, '0', 2) > 0) {
            \think\facade\Log::info("使用责任分担结果计算各支付方式退款金额（仅供应商部分）");

            // 找出实际有退款的支付方式（金额>0的）
            $hasWelfareRefund = bccomp($actualWelfareRefund, '0', 2) > 0;
            $hasBalanceRefund = bccomp($actualBalanceRefund, '0', 2) > 0;
            $hasOnlineRefund = bccomp($actualOnlineRefund, '0', 2) > 0;

            // 从 deductions 中获取各支付方式应退金额（仅供应商部分）
            $welfareSupplierRefund = $deductions['subsidy']['welfare']['supplier'] ?? '0.00';
            $welfarePlatformRefund = '0.00'; // 平台部分不创建退款流水
            $welfareRefund = $welfareSupplierRefund; // 退款流水只用供应商部分

            $balanceSupplierRefund = $deductions['subsidy']['yue']['supplier'] ?? '0.00';
            $balancePlatformRefund = '0.00';
            $balanceRefund = $balanceSupplierRefund;

            $onlineSupplierRefund = $deductions['online']['weixin']['supplier'] ?? '0.00';
            $onlinePlatformRefund = '0.00';
            $onlineRefund = $onlineSupplierRefund;

            \think\facade\Log::info("福利金退款: 供应商={$welfareSupplierRefund}, 平台={$welfarePlatformRefund}");
            \think\facade\Log::info("余额退款: 供应商={$balanceSupplierRefund}, 平台={$balancePlatformRefund}");
            \think\facade\Log::info("在线支付退款: 供应商={$onlineSupplierRefund}, 平台={$onlinePlatformRefund}");
        } else {
            // 兜底逻辑：如果没有传入实际退款金额，使用原来的流水比例分配逻辑
            \think\facade\Log::info("未提供实际退款金额，使用流水比例分配（兜底逻辑）");

            $welfareFlowing = $flowingAmounts['welfare'] ?? '0.00';
            $balanceFlowing = $flowingAmounts['yue'] ?? '0.00';
            $onlineFlowing = '0.00';
            foreach (['weixin', 'alipay', 'ums'] as $onlineType) {
                if (isset($flowingAmounts[$onlineType])) {
                    $onlineFlowing = bcadd($onlineFlowing, $flowingAmounts[$onlineType], 2);
                }
            }

            \think\facade\Log::info("流水金额: welfare={$welfareFlowing}, balance={$balanceFlowing}, online={$onlineFlowing}");

            if (bccomp($totalFlowingAmount, '0', 2) > 0 && bccomp($supplierRefund, '0', 2) > 0) {
                $welfareRatio = bcdiv($welfareFlowing, $totalFlowingAmount, 6);
                $balanceRatio = bcdiv($balanceFlowing, $totalFlowingAmount, 6);
                $onlineRatio = bcdiv($onlineFlowing, $totalFlowingAmount, 6);

                \think\facade\Log::info("流水比例: welfare={$welfareRatio}, balance={$balanceRatio}, online={$onlineRatio}");

                $welfareSupplierRefund = bcmul($supplierRefund, $welfareRatio, 2);
                $balanceSupplierRefund = bcmul($supplierRefund, $balanceRatio, 2);
                $onlineSupplierRefund = bcmul($supplierRefund, $onlineRatio, 2);
                $welfarePlatformRefund = '0.00';
                $balancePlatformRefund = '0.00';
                $onlinePlatformRefund = '0.00';

                $welfareRefund = $welfareSupplierRefund;
                $balanceRefund = $balanceSupplierRefund;
                $onlineRefund = $onlineSupplierRefund;

                // 精度补偿
                $totalCalculated = bcadd(bcadd($welfareSupplierRefund, $balanceSupplierRefund, 2), $onlineSupplierRefund, 2);
                if (bccomp($totalCalculated, '0', 2) == 0 && bccomp($supplierRefund, '0', 2) > 0) {
                    if (bccomp($balanceRatio, $welfareRatio, 6) >= 0 && bccomp($balanceRatio, $onlineRatio, 6) >= 0) {
                        $balanceSupplierRefund = $supplierRefund;
                        $balanceRefund = $supplierRefund;
                    } elseif (bccomp($welfareRatio, $onlineRatio, 6) >= 0) {
                        $welfareSupplierRefund = $supplierRefund;
                        $welfareRefund = $supplierRefund;
                    } else {
                        $onlineSupplierRefund = $supplierRefund;
                        $onlineRefund = $supplierRefund;
                    }
                } else {
                    $diff = bcsub($supplierRefund, $totalCalculated, 2);
                    if (bccomp($diff, '0', 2) != 0) {
                        if (bccomp($balanceRatio, $welfareRatio, 6) >= 0 && bccomp($balanceRatio, $onlineRatio, 6) >= 0) {
                            $balanceSupplierRefund = bcadd($balanceSupplierRefund, $diff, 2);
                            $balanceRefund = bcadd($balanceRefund, $diff, 2);
                        } elseif (bccomp($welfareRatio, $onlineRatio, 6) >= 0) {
                            $welfareSupplierRefund = bcadd($welfareSupplierRefund, $diff, 2);
                            $welfareRefund = bcadd($welfareRefund, $diff, 2);
                        } else {
                            $onlineSupplierRefund = bcadd($onlineSupplierRefund, $diff, 2);
                            $onlineRefund = bcadd($onlineRefund, $diff, 2);
                        }
                    }
                }
            }
        }

        // 查询分账记录剩余金额，确保扣减不超过剩余
        // 对于子订单，使用子订单号查询分账记录
        $queryOrderId = $isSubOrder ? $currentOrderId : $originalOrderId;
        
        /** @var \app\services\supplier\SupplierShareRecordServices $shareRecordServices */
        $shareRecordServices = app()->make(\app\services\supplier\SupplierShareRecordServices::class);
        $shareRecords = $shareRecordServices->getList(['order_no' => $queryOrderId], '*', 0, 0);

        // 获取各支付方式的分账记录剩余金额
        $welfareRemaining = '0.00';
        $balanceRemaining = '0.00';
        $onlineRemaining = '0.00';

        foreach ($shareRecords as $record) {
            $remarks = $record['remarks'] ?? '';
            $divisionType = $record['division_type'] ?? '';
            $shareAmount = $record['share_amount'] ?? '0.00';

            if (strpos($remarks, '福利金') !== false) {
                $welfareRemaining = $shareAmount;
            } elseif (strpos($remarks, '余额') !== false) {
                $balanceRemaining = $shareAmount;
            } elseif ($divisionType === 'online') {
                $onlineRemaining = $shareAmount;
            }
        }

        \think\facade\Log::info("分账记录剩余金额: 福利金={$welfareRemaining}, 余额={$balanceRemaining}, 在线={$onlineRemaining}");

        // 限制扣减金额不超过剩余金额，超出部分重新分配
        $overflow = '0.00';

        // 检查福利金是否超额
        if (bccomp($welfareRefund, $welfareRemaining, 2) > 0) {
            $overflow = bcadd($overflow, bcsub($welfareRefund, $welfareRemaining, 2), 2);
            \think\facade\Log::info("福利金超额: 应退={$welfareRefund}, 剩余={$welfareRemaining}, 超出=" . bcsub($welfareRefund, $welfareRemaining, 2));
            $welfareRefund = $welfareRemaining;
        }

        // 检查余额是否超额
        if (bccomp($balanceRefund, $balanceRemaining, 2) > 0) {
            $overflow = bcadd($overflow, bcsub($balanceRefund, $balanceRemaining, 2), 2);
            \think\facade\Log::info("余额超额: 应退={$balanceRefund}, 剩余={$balanceRemaining}, 超出=" . bcsub($balanceRefund, $balanceRemaining, 2));
            $balanceRefund = $balanceRemaining;
        }

        // 检查在线支付是否超额
        if (bccomp($onlineRefund, $onlineRemaining, 2) > 0) {
            $overflow = bcadd($overflow, bcsub($onlineRefund, $onlineRemaining, 2), 2);
            \think\facade\Log::info("在线支付超额: 应退={$onlineRefund}, 剩余={$onlineRemaining}, 超出=" . bcsub($onlineRefund, $onlineRemaining, 2));
            $onlineRefund = $onlineRemaining;
        }

        // 将超出部分分配到其他有剩余的支付方式
        if (bccomp($overflow, '0', 2) > 0) {
            \think\facade\Log::info("需要重新分配超出金额: {$overflow}");

            // 计算各支付方式的可用剩余（剩余 - 已分配的应退）
            $welfareAvailable = bcsub($welfareRemaining, $welfareRefund, 2);
            $balanceAvailable = bcsub($balanceRemaining, $balanceRefund, 2);
            $onlineAvailable = bcsub($onlineRemaining, $onlineRefund, 2);

            \think\facade\Log::info("可用剩余: 福利金={$welfareAvailable}, 余额={$balanceAvailable}, 在线={$onlineAvailable}");

            // 优先分配到余额，然后福利金，最后在线
            if (bccomp($overflow, '0', 2) > 0 && bccomp($balanceAvailable, '0', 2) > 0) {
                $toBalance = bccomp($overflow, $balanceAvailable, 2) <= 0 ? $overflow : $balanceAvailable;
                $balanceRefund = bcadd($balanceRefund, $toBalance, 2);
                $overflow = bcsub($overflow, $toBalance, 2);
                \think\facade\Log::info("分配到余额: {$toBalance}, 剩余溢出: {$overflow}");
            }

            if (bccomp($overflow, '0', 2) > 0 && bccomp($welfareAvailable, '0', 2) > 0) {
                $toWelfare = bccomp($overflow, $welfareAvailable, 2) <= 0 ? $overflow : $welfareAvailable;
                $welfareRefund = bcadd($welfareRefund, $toWelfare, 2);
                $overflow = bcsub($overflow, $toWelfare, 2);
                \think\facade\Log::info("分配到福利金: {$toWelfare}, 剩余溢出: {$overflow}");
            }

            if (bccomp($overflow, '0', 2) > 0 && bccomp($onlineAvailable, '0', 2) > 0) {
                $toOnline = bccomp($overflow, $onlineAvailable, 2) <= 0 ? $overflow : $onlineAvailable;
                $onlineRefund = bcadd($onlineRefund, $toOnline, 2);
                $overflow = bcsub($overflow, $toOnline, 2);
                \think\facade\Log::info("分配到在线支付: {$toOnline}, 剩余溢出: {$overflow}");
            }

            if (bccomp($overflow, '0', 2) > 0) {
                \think\facade\Log::warning("⚠️ 仍有未分配的溢出金额: {$overflow}，可能是分账记录金额不足");
            }
        }

        \think\facade\Log::info("调整后福利金总应退: {$welfareRefund}");
        \think\facade\Log::info("调整后余额总应退: {$balanceRefund}");
        \think\facade\Log::info("调整后在线支付总应退: {$onlineRefund}");
        \think\facade\Log::info("调整后总应退总额验证: " . bcadd(bcadd($welfareRefund, $balanceRefund, 2), $onlineRefund, 2));

        /** @var StoreOrderCreateServices $storeOrderCreateServices */
        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);

        // 根据原流水状态处理退款
        \think\facade\Log::info('=== 开始处理各支付方式退款流水 ===');
        
        $successCount = 0;
        $failedCount = 0;
        
        foreach ($incomeRecords as $record) {
            try {
                $payType = $record['pay_type'];
                $recordStatus = $record['status'];
                $refundAmount = 0;

                \think\facade\Log::info("处理流水ID: {$record['id']}, 支付方式: {$payType}, 状态: {$recordStatus}");

                // 确定该流水对应的退款金额
                if ($payType == 'welfare') {
                    $refundAmount = $welfareSupplierRefund;
                } elseif ($payType == 'yue') {
                    $refundAmount = $balanceSupplierRefund;
                } elseif (in_array($payType, ['weixin', 'alipay', 'ums'])) {
                    $refundAmount = $onlineSupplierRefund;
                } elseif ($payType == 'combination') {
                    $refundAmount = $record['number'];
                    \think\facade\Log::warning("⚠️ 检测到组合支付流水(历史遗留数据): 流水ID={$record['id']}, 金额={$refundAmount}");
                }

                \think\facade\Log::info("该流水应退金额: {$refundAmount}");

                if ($refundAmount <= 0) {
                    \think\facade\Log::info("退款金额为0，跳过");
                    $successCount++;
                    continue;
                }

// division_status=3 表示收入流水已分账完成，这是正常状态
                // 退款时应该可以对已分账完成的流水进行退款
                // 不再检查 division_status，而是在创建退款流水时检查是否重复

                // 根据原流水状态处理退款
                \think\facade\Log::info("根据流水状态处理退款: status={$recordStatus}");

                $refundId = null;

                if ($recordStatus == 0) {
                    $refundId = $this->processRefundForStatus0($record, $order, $refundAmount, $payType, $currentOrderId);
                } elseif ($recordStatus == 1) {
                    $refundId = $this->processRefundForStatus1($record, $order, $refundAmount, $payType, $currentOrderId);
                } elseif ($recordStatus == 2 || $recordStatus == 3) {
                    $refundId = $this->processRefundForStatus2Or3($record, $order, $refundAmount, $payType, $recordStatus, $currentOrderId);
                } else {
                    \think\facade\Log::warning("⚠️ 未知的流水状态: status={$recordStatus}, 跳过处理");
                    $successCount++;
                    continue;
                }
                
                if ($refundId) {
                    // 标记原流水为已处理
                    $this->dao->update($record['id'], [
                        'division_status' => 3,
                    ]);
                    \think\facade\Log::info("原收入流水已标记为已完成: 流水ID={$record['id']}");
                    $successCount++;
                }
                
            } catch (\Exception $e) {
                \think\facade\Log::error("❌ 处理退款流水失败: 流水ID={$record['id']}, 错误: {$e->getMessage()}");
                \think\facade\Log::error("异常堆栈: {$e->getTraceAsString()}");
                $failedCount++;
            }
        }

        \think\facade\Log::info('========================================');
        \think\facade\Log::info('=== ✅ 供应商退款流水处理完成 ===');
        \think\facade\Log::info("成功: {$successCount} 条, 失败: {$failedCount} 条");
        \think\facade\Log::info('========================================');

        return $failedCount == 0;
    }

    /**
     * 处理状态0（冻结中）的退款流水
     * @param string $orderNo 订单号（用于link_id关联）
     */
    private function processRefundForStatus0(array $record, array $order, string $refundAmount, string $payType, string $orderNo): ?int
    {
        \think\facade\Log::info("【状态0-冻结中】创建退款流水抵消收入记录");

        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);
        $orderId = $storeOrderCreateServices->getNewOrderId('ls');
        \think\facade\Log::info("生成退款流水单号: {$orderId}");

        $refundData = [
            'supplier_id' => $order['supplier_id'],
            'uid' => $order['uid'],
            'order_id' => $orderId,
            'link_id' => $orderNo,  // 使用当前订单号，与收入流水对应
            'pay_type' => $payType,
            'trade_time' => time(),
            'pm' => 0,
            'number' => $refundAmount,
            'type' => 2,
            'status' => 0,
            'finish_time' => 0,
            'add_time' => time(),
        ];

        $refundRecord = $this->dao->save($refundData);
        if (!$refundRecord) {
            throw new \Exception("创建退款流水失败");
        }

        \think\facade\Log::info("✅ 退款流水创建成功: pay_type={$payType}, amount={$refundAmount}, link_id={$orderNo}");

        // 使用累计退款金额方式更新分账记录，支持部分退款
        // 只有全额退款时才标记为 refund_cancelled，部分退款时仅累加已退款金额
        // 根据支付类型映射到分账类型：在线支付(weixin/alipay/ums) -> online，福利金/余额 -> subsidy
        $divisionType = $this->mapPayTypeToDivisionType($payType);
        $this->updateShareRecordRefundAmount($orderNo, $refundAmount, $divisionType, $payType);

        return $refundRecord->id;
    }

    /**
     * 根据支付类型映射到分账类型
     * @param string $payType 支付类型 (weixin/alipay/ums/welfare/yue)
     * @return string 分账类型 (online/subsidy)
     */
    private function mapPayTypeToDivisionType(string $payType): string
    {
        if (in_array($payType, ['weixin', 'alipay', 'ums'])) {
            return 'online';  // 在线支付类型
        } elseif (in_array($payType, ['welfare', 'yue'])) {
            return 'subsidy'; // 平台补贴类型
        }
        return '';  // 未知类型，不限制
    }

    /**
     * 处理状态1（已放款）的退款流水
     * @param string $orderNo 订单号（用于link_id关联）
     */
    private function processRefundForStatus1(array $record, array $order, string $refundAmount, string $payType, string $orderNo): ?int
    {
        \think\facade\Log::info("【状态1-已放款】创建退款流水扣减供应商金额");

        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);
        $orderId = $storeOrderCreateServices->getNewOrderId('ls');
        \think\facade\Log::info("生成退款流水单号: {$orderId}");

        $refundData = [
            'supplier_id' => $order['supplier_id'],
            'uid' => $order['uid'],
            'order_id' => $orderId,
            'link_id' => $orderNo,  // 使用当前订单号，与收入流水对应
            'pay_type' => $payType,
            'trade_time' => time(),
            'pm' => 0,
            'number' => $refundAmount,
            'type' => 2,
            'status' => 1,
            'finish_time' => time(),
            'add_time' => time(),
        ];

        $refundRecord = $this->dao->save($refundData);
        if (!$refundRecord) {
            throw new \Exception("创建退款流水失败");
        }

        \think\facade\Log::info("✅ 退款流水创建成功: pay_type={$payType}, amount={$refundAmount}, link_id={$orderNo}");

        // 状态1也需要更新分账记录的退款金额
        // 根据支付类型映射到分账类型：在线支付(weixin/alipay/ums) -> online，福利金/余额 -> subsidy
        $divisionType = $this->mapPayTypeToDivisionType($payType);
        $this->updateShareRecordRefundAmount($orderNo, $refundAmount, $divisionType, $payType);

        return $refundRecord->id;
    }

    /**
     * 处理状态2或3（外部分账）的退款流水
     * @param string $orderNo 订单号（用于link_id关联）
     */
    private function processRefundForStatus2Or3(array $record, array $order, string $refundAmount, string $payType, int $recordStatus, string $orderNo): ?int
    {
        $statusName = $recordStatus == 2 ? '外部分账待处理' : '外部已分账';
        \think\facade\Log::info("【状态{$recordStatus}-{$statusName}】创建退款流水");

        $storeOrderCreateServices = app()->make(StoreOrderCreateServices::class);
        $orderId = $storeOrderCreateServices->getNewOrderId('ls');
        \think\facade\Log::info("生成退款流水单号: {$orderId}");

        $refundData = [
            'supplier_id' => $order['supplier_id'],
            'uid' => $order['uid'],
            'order_id' => $orderId,
            'link_id' => $orderNo,  // 使用当前订单号，与收入流水对应
            'pay_type' => $payType,
            'trade_time' => time(),
            'pm' => 0,
            'number' => $refundAmount,
            'type' => 2,
            'status' => $recordStatus,
            'division_status' => 0,
            'add_time' => time(),
        ];

        $refundRecord = $this->dao->save($refundData);
        if (!$refundRecord) {
            throw new \Exception("创建退款流水失败");
        }

        \think\facade\Log::info("✅ 退款流水创建成功: pay_type={$payType}, amount={$refundAmount}, link_id={$orderNo}");

        // 使用累计退款金额方式更新分账记录，支持部分退款
        // 只有全额退款时才标记为 refund_cancelled，部分退款时仅累加已退款金额
        // 根据支付类型映射到分账类型
        $divisionType = $this->mapPayTypeToDivisionType($payType);
        $this->updateShareRecordRefundAmount($orderNo, $refundAmount, $divisionType, $payType);

        return $refundRecord->id;
    }

    /**
     * 批量确认外部分账（手动操作）
     * 将 status=2（外部分账待处理）的流水更新为 status=3（外部已分账）
     * @param array $ids 流水ID数组
     * @return bool
     */
    public function batchConfirmExternal(array $ids): bool
    {
        if (empty($ids)) {
            throw new \Exception('请选择要确认的流水记录');
        }

        \think\facade\Log::info('=== 开始批量确认外部分账 ===');
        \think\facade\Log::info('流水ID: ' . implode(',', $ids));

        $successCount = 0;
        $failedCount = 0;

        foreach ($ids as $id) {
            try {
                $record = $this->dao->get($id);
                if (!$record) {
                    \think\facade\Log::warning("流水记录不存在: id={$id}");
                    $failedCount++;
                    continue;
                }

                if ($record['status'] != 2) {
                    \think\facade\Log::warning("流水状态不是待处理: id={$id}, status={$record['status']}");
                    $failedCount++;
                    continue;
                }

                // 更新状态为已分账
                $this->dao->update($id, [
                    'status' => 3,  // 3=外部已分账
                    'finish_time' => time(),
                ]);

                \think\facade\Log::info("确认成功: id={$id}, order_id={$record['link_id']}, amount={$record['number']}");
                $successCount++;
            } catch (\Exception $e) {
                \think\facade\Log::error("确认失败: id={$id}, error={$e->getMessage()}");
                $failedCount++;
            }
        }

        \think\facade\Log::info("批量确认完成: 成功 {$successCount} 条, 失败 {$failedCount} 条");

        return true;
    }

    /**
     * 获取外部分账待处理列表
     * @param array $where 查询条件
     * @return array
     */
    public function getExternalPendingList(array $where = []): array
    {
        $where['status'] = 2;  // 外部分账待处理
        $where['pm'] = 1;  // 收入
        $where['type'] = 1;  // 支付订单

        return $this->dao->getList($where, '*', 0, 0);
    }

    /**
     * 从分账类型和备注推断支付类型
     * @param string $divisionType 分账类型 (online/subsidy)
     * @param string $remarks 备注信息
     * @return string 支付类型 (weixin/yue/welfare/unknown)
     */
    private function inferPayTypeFromDivision(string $divisionType, string $remarks): string
    {
        // 根据备注信息推断
        if (strpos($remarks, '福利金') !== false || strpos($remarks, 'welfare') !== false) {
            return 'welfare';
        }
        if (strpos($remarks, '余额') !== false || strpos($remarks, 'yue') !== false || strpos($remarks, 'balance') !== false) {
            return 'yue';
        }

        // 根据分账类型推断
        if ($divisionType === 'online') {
            return 'weixin';  // 在线支付默认归类为微信
        }
        if ($divisionType === 'subsidy') {
            return 'yue';  // 补贴类型默认归类为余额
        }

        return 'unknown';
    }

    /**
     * 获取当前退款的供应商扣减金额
     * @return string
     */
    public function getCurrentSupplierDeduction(): string
    {
        return $this->currentSupplierDeduction;
    }

    /**
     * 获取当前退款的平台扣减金额
     * @return string
     */
    public function getCurrentPlatformDeduction(): string
    {
        return $this->currentPlatformDeduction;
    }

    /**
     * 获取当前退款的扣减明细
     * @return array
     */
    public function getCurrentDeductions(): array
    {
        return $this->currentDeductions;
    }
}
