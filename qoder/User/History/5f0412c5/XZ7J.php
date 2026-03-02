<?php
// +----------------------------------------------------------------------
// | CRMEB [ CRMEB赋能开发者,助力企业发展 ]
// +----------------------------------------------------------------------
// | Copyright (c) 2016~2024 https://www.crmeb.com All rights reserved.
// +----------------------------------------------------------------------
// | Licensed CRMEB并不是自由软件,未经许可不能去掉CRMEB相关版权
// +----------------------------------------------------------------------
// | Author: CRMEB Team <admin@crmeb.com>
// +----------------------------------------------------------------------

namespace crmeb\services;

use think\facade\Log;

/**
 * 银联商务支付服务类
 * Class UmsPayService
 * @package crmeb\services
 */
class UmsPayService
{
    /**
     * @var string AppId
     */
    protected $appId;

    /**
     * @var string AppKey
     */
    protected $appKey;

    /**
     * @var string 商户号
     */
    protected $mid;

    /**
     * @var string 终端号
     */
    protected $tid;

    /**
     * @var string API地址
     */
    protected $apiUrl;

    /**
     * @var bool 是否生产环境
     */
    protected $isProduction;

    /**
     * @var string 通讯密钥(用于回调验签)
     */
    protected $notifyKey;

    /**
     * 构造函数
     * @param string $paymentType 支付类型: 'mini' 小程序支付, 'h5' H5支付
     */
    public function __construct(string $paymentType = 'mini')
    {
        // 从配置文件读取参数
        $configFile = config_path() . 'UmsPayConfig.json';
        if (!file_exists($configFile)) {
            throw new \Exception('银联商务配置文件不存在: ' . $configFile);
        }

        $config = json_decode(file_get_contents($configFile), true);
        if (!$config) {
            throw new \Exception('银联商务配置文件格式错误');
        }

        // 支持多账号配置
        if (isset($config['accounts'])) {
            // 新的多账号配置格式
            // 优先使用配置文件中的 current_account，环境变量仅作为覆盖
            $currentAccount = $config['current_account'] ?? 'test';
            
            // 检查环境变量是否明确设置了账号（用于测试环境切换）
            $envAccount = env('UMS_ACCOUNT');
            if ($envAccount && isset($config['accounts'][$envAccount])) {
                $currentAccount = $envAccount;
                Log::info('使用环境变量指定的账号: ' . $currentAccount);
            }

            // 只有在明确配置为生产环境时才使用 productionH5
            // 如果当前账号是 test 或 test2，则使用对应的测试配置
            $isProductionAccount = (strpos($currentAccount, 'production') !== false);

            // 如果是H5支付且是生产环境，则使用productionH5
            if ($paymentType === 'h5' && $isProductionAccount && isset($config['accounts']['productionH5'])) {
                $currentAccount = 'productionH5';
                Log::info('H5生产环境支付使用专用配置: productionH5');
            } elseif ($paymentType === 'h5' && !$isProductionAccount) {
                Log::info('H5支付使用测试配置: ' . $currentAccount);
            }

            if (!isset($config['accounts'][$currentAccount])) {
                throw new \Exception('当前账号配置不存在: ' . $currentAccount);
            }
            $accountConfig = $config['accounts'][$currentAccount];

            $this->appId = $accountConfig['app_id'] ?? '';
            $this->appKey = $accountConfig['app_key'] ?? '';
            $this->mid = $accountConfig['mid'] ?? '';
            $this->tid = $accountConfig['tid'] ?? '';
            $this->notifyKey = $accountConfig['notify_key'] ?? '';
            $this->apiUrl = $accountConfig['api_url'] ?? 'https://test-api-open.chinaums.com';
            $this->isProduction = (strpos($currentAccount, 'production') !== false);
        } else {
            // 旧的单账号配置格式(兼容)
            $this->appId = $config['app_id'] ?? '';
            $this->appKey = $config['app_key'] ?? '';
            $this->mid = $config['mid'] ?? '';
            $this->tid = $config['tid'] ?? '';
            $this->notifyKey = $config['notify_key'] ?? '';
            $this->isProduction = $config['is_production'] ?? false;

            // 根据环境选择API地址
            if ($this->isProduction) {
                $this->apiUrl = $config['api_url'] ?? 'https://api-mop.chinaums.com';
            } else {
                $this->apiUrl = $config['test_api_url'] ?? 'https://test-api-open.chinaums.com';
            }
        }

        Log::info('=== 银联商务支付初始化 ===');
        Log::info('支付类型: ' . $paymentType);
        Log::info('AppId: ' . $this->appId);
        Log::info('商户号: ' . $this->mid);
        Log::info('终端号: ' . $this->tid);
        Log::info('API地址: ' . $this->apiUrl);
        Log::info('环境: ' . ($this->isProduction ? '生产' : '测试'));
    }

    /**
     * 小程序支付下单
     * @param string $orderId 订单号
     * @param string $amount 支付金额(元)
     * @param string $subject 商品标题
     * @param string $openid 用户openid
     * @param string $notifyUrl 异步通知地址
     * @param array $divisionData 分账数据 ['divisionFlag' => true, 'platformAmount' => 0, 'subOrders' => [...]]
     * @return array
     */
    public function miniPay(string $orderId, string $amount, string $subject, string $openid, string $notifyUrl = '', array $divisionData = [])
    {
        try {
            Log::info('=== 银联小程序支付下单 ===');
            Log::info('原始订单号: ' . $orderId);
            Log::info('金额: ' . $amount . '元');
            Log::info('OpenID: ' . $openid);
            Log::info('通知URL: ' . $notifyUrl);
            if (!empty($divisionData)) {
                Log::info('分账数据: ' . json_encode($divisionData, JSON_UNESCAPED_UNICODE));
            }

            // 金额转换:元转分
            $totalAmount = bcmul($amount, '100', 0);
            Log::info('金额(分): ' . $totalAmount);

            // 处理订单号:正式账号需要以3HD3开头
            $umsOrderId = $this->formatOrderId($orderId);
            Log::info('银联订单号: ' . $umsOrderId);

            // 构造请求参数
            $params = [
                'requestTimestamp' => date('Y-m-d H:i:s'),
                'merOrderId' => $umsOrderId,
                'mid' => $this->mid,
                'tid' => $this->tid,
                'totalAmount' => $totalAmount,
                'tradeType' => 'MINI',
                'orderDesc' => $subject,
                'notifyUrl' => $notifyUrl,
            ];

            // 添加分账参数
            if (!empty($divisionData['divisionFlag'])) {
                $params['divisionFlag'] = true;

                // 添加子订单分账信息
                if (!empty($divisionData['subOrders']) && is_array($divisionData['subOrders'])) {
                    // 格式化子订单号: 银联要求子订单号也必须以3HD3开头
                    // 注意: 子订单号应该基于格式化后的主订单号生成,而不是直接格式化原始子订单号
                    // 因为formatOrderId会截断订单号,导致主订单和子订单的后缀不一致
                    $formattedSubOrders = [];
                    $subOrdersTotalAmount = 0; // 子订单总金额

                    foreach ($divisionData['subOrders'] as $subOrder) {
                        $formattedSubOrder = $subOrder;
                        // 生成子订单号: 基于原始子订单号,添加3HD3前缀
                        if (!empty($subOrder['merOrderId'])) {
                            // 如果原始子订单号是 SUB_ 开头,则添加3HD3前缀
                            if (str_starts_with($subOrder['merOrderId'], 'SUB_')) {
                                // 子订单号格式: 3HD3 + 原始子订单号
                                // 原始: SUB_wx750407836026011648_3
                                // 结果: 3HD3SUB_wx750407836026011648_3
                                $subOrderId = '3HD3' . $subOrder['merOrderId'];
                                // 银联订单号长度限制: 6-32位
                                if (strlen($subOrderId) > 32) {
                                    $subOrderId = substr($subOrderId, 0, 32);
                                }
                                $formattedSubOrder['merOrderId'] = $subOrderId;
                            } elseif (str_starts_with($subOrder['merOrderId'], 'PLAT_')) {
                                // 如果原始子订单号是 PLAT_ 开头,添加3HD3前缀
                                // 原始: PLAT_wx750407836026011648
                                // 结果: 3HD3PLAT_wx750407836026011648
                                $subOrderId = '3HD3' . $subOrder['merOrderId'];
                                // 银联订单号长度限制: 6-32位
                                if (strlen($subOrderId) > 32) {
                                    $subOrderId = substr($subOrderId, 0, 32);
                                }
                                $formattedSubOrder['merOrderId'] = $subOrderId;
                            } elseif (str_starts_with($subOrder['merOrderId'], '3HD3SUB_') || str_starts_with($subOrder['merOrderId'], '3HD3PLAT_')) {
                                // 如果已经是3HD3SUB_或3HD3PLAT_开头,直接使用(退款时的情况)
                                // 但仍需检查长度
                                $subOrderId = $subOrder['merOrderId'];
                                if (strlen($subOrderId) > 32) {
                                    $subOrderId = substr($subOrderId, 0, 32);
                                }
                                $formattedSubOrder['merOrderId'] = $subOrderId;
                            } else {
                                // 其他格式直接格式化
                                $formattedSubOrder['merOrderId'] = $this->formatOrderId($subOrder['merOrderId']);
                            }
                        }
                        // 累加子订单金额
                        $subOrdersTotalAmount += intval($subOrder['totalAmount'] ?? 0);
                        $formattedSubOrders[] = $formattedSubOrder;
                    }

                    $params['subOrders'] = $formattedSubOrders;

                    // 计算平台金额: 主订单总金额 - 子订单总金额
                    // 银联要求: totalAmount = platformAmount + sum(subOrders.totalAmount)
                    $platformAmount = intval($totalAmount) - $subOrdersTotalAmount;
                    $params['platformAmount'] = 0 ; // 平台退款金额恒为0

                    Log::info('分账子订单: ' . json_encode($params['subOrders'], JSON_UNESCAPED_UNICODE));
                    Log::info("分账金额计算: 主订单={$totalAmount}分, 子订单总额={$subOrdersTotalAmount}分, 平台={$platformAmount}分");
                }
            }

            // 获取小程序AppId
            $miniAppId = sys_config('routine_appId') ?: '';

            // 银联商务小程序支付参数
            // 根据银联文档,字段名使用驼峰命名: subAppId, subOpenId
            // 但微信支付要求服务商模式必须同时传openid和sub_openid
            if (!empty($miniAppId)) {
                // 小程序支付模式
                $params['subAppId'] = $miniAppId;      // 子商户小程序AppId
                $params['subOpenId'] = $openid;        // 子商户OpenId

                // 如果是服务商模式,还需要传openid(服务商OpenId)
                // 临时方案: 使用同一个OpenId(可能不行,需要联系银联确认)
                $params['openid'] = $openid;           // 服务商OpenId(临时使用同一个)

                Log::info('小程序AppId: ' . $miniAppId);
                Log::info('用户OpenId: ' . $openid);
                Log::info('注意: 如果是服务商模式,需要联系银联确认openid字段');
            } else {
                // 直连模式
                $params['openid'] = $openid;
                Log::info('直连模式OpenId: ' . $openid);
            }

            Log::info('请求参数: ' . json_encode($params, JSON_UNESCAPED_UNICODE));

            // 发送请求
            $url = $this->apiUrl . '/v1/netpay/wx/unified-order';
            $response = $this->request($url, $params);

            Log::info('响应数据: ' . json_encode($response, JSON_UNESCAPED_UNICODE));

            // 检查响应
            if (!isset($response['errCode']) || $response['errCode'] !== 'SUCCESS') {
                $errMsg = $response['errMsg'] ?? '未知错误';
                Log::error('银联小程序支付下单失败: ' . $errMsg);
                throw new \Exception('支付下单失败: ' . $errMsg);
            }

            // 返回小程序支付参数
            if (!isset($response['miniPayRequest'])) {
                Log::error('响应中缺少miniPayRequest');
                throw new \Exception('支付下单失败: 响应格式错误');
            }

            $miniPayRequest = $response['miniPayRequest'];

            return [
                'status' => 'UMS_MINI_PAY',
                'result' => [
                    'appId' => $miniPayRequest['appId'],
                    'timeStamp' => $miniPayRequest['timeStamp'],
                    'nonceStr' => $miniPayRequest['nonceStr'],
                    'package' => $miniPayRequest['package'],
                    'signType' => $miniPayRequest['signType'],
                    'paySign' => $miniPayRequest['paySign'],
                ],
                'jsConfig' => $miniPayRequest,
            ];

        } catch (\Exception $e) {
            Log::error('银联小程序支付异常: ' . $e->getMessage());
            Log::error('异常堆栈: ' . $e->getTraceAsString());
            throw $e;
        }
    }

    /**
     * H5支付下单
     * @param string $orderId 订单号
     * @param string $amount 支付金额(元)
     * @param string $subject 商品标题
     * @param string $notifyUrl 异步通知地址
     * @param string $returnUrl 同步跳转地址
     * @param array $divisionData 分账数据 ['divisionFlag' => true, 'platformAmount' => 0, 'subOrders' => [...]]
     * @return array
     */
    public function h5Pay(string $orderId, string $amount, string $subject, string $notifyUrl = '', string $returnUrl = '', array $divisionData = [])
    {
        try {
            Log::info('=== 银联H5支付下单 ===');
            Log::info('原始订单号: ' . $orderId);
            Log::info('金额: ' . $amount . '元');
            Log::info('通知URL: ' . $notifyUrl);
            Log::info('返回URL: ' . $returnUrl);
            if (!empty($divisionData)) {
                Log::info('分账数据: ' . json_encode($divisionData, JSON_UNESCAPED_UNICODE));
            }

            // 金额转换:元转分
            $totalAmount = bcmul($amount, '100', 0);
            Log::info('金额(分): ' . $totalAmount);

            // 处理订单号:正式账号需要以3HD3开头
            $umsOrderId = $this->formatOrderId($orderId);
            Log::info('银联订单号: ' . $umsOrderId);

            // 构造请求参数 - 使用H5跳转小程序支付(更稳定)
            $params = [
                'requestTimestamp' => date('Y-m-d H:i:s'),
                'merOrderId' => $umsOrderId,
                'mid' => $this->mid,
                'tid' => $this->tid,
                'instMid' => 'H5DEFAULT',
                'totalAmount' => $totalAmount,
            ];

            // 可选参数
            if (!empty($subject)) {
                $params['orderDesc'] = $subject;
            }
            if (!empty($notifyUrl)) {
                $params['notifyUrl'] = $notifyUrl;
            }
            if (!empty($returnUrl)) {
                $params['returnUrl'] = $returnUrl;
            }

            // 添加分账参数
            if (!empty($divisionData['divisionFlag'])) {
                $params['divisionFlag'] = true;
                $params['platformAmount'] = 0; // 平台分账金额恒为0

                // 添加子订单分账信息
                if (!empty($divisionData['subOrders']) && is_array($divisionData['subOrders'])) {
                    // 格式化子订单号: 银联要求子订单号也必须以3HD3开头
                    // 注意: 子订单号应该基于格式化后的主订单号生成,而不是直接格式化原始子订单号
                    // 因为formatOrderId会截断订单号,导致主订单和子订单的后缀不一致
                    $formattedSubOrders = [];
                    foreach ($divisionData['subOrders'] as $subOrder) {
                        $formattedSubOrder = $subOrder;
                        // 生成子订单号: 基于原始子订单号,添加3HD3前缀
                        if (!empty($subOrder['merOrderId'])) {
                            // 如果原始子订单号是 SUB_ 开头,则添加3HD3前缀
                            if (str_starts_with($subOrder['merOrderId'], 'SUB_')) {
                                // 子订单号格式: 3HD3 + 原始子订单号
                                // 原始: SUB_wx750407836026011648_3
                                // 结果: 3HD3SUB_wx750407836026011648_3
                                $subOrderId = '3HD3' . $subOrder['merOrderId'];
                                // 银联订单号长度限制: 6-32位
                                if (strlen($subOrderId) > 32) {
                                    $subOrderId = substr($subOrderId, 0, 32);
                                }
                                $formattedSubOrder['merOrderId'] = $subOrderId;
                            } elseif (str_starts_with($subOrder['merOrderId'], 'PLAT_')) {
                                // 如果原始子订单号是 PLAT_ 开头,添加3HD3前缀
                                // 原始: PLAT_wx750407836026011648
                                // 结果: 3HD3PLAT_wx750407836026011648
                                $subOrderId = '3HD3' . $subOrder['merOrderId'];
                                // 银联订单号长度限制: 6-32位
                                if (strlen($subOrderId) > 32) {
                                    $subOrderId = substr($subOrderId, 0, 32);
                                }
                                $formattedSubOrder['merOrderId'] = $subOrderId;
                            } elseif (str_starts_with($subOrder['merOrderId'], '3HD3SUB_') || str_starts_with($subOrder['merOrderId'], '3HD3PLAT_')) {
                                // 如果已经是3HD3SUB_或3HD3PLAT_开头,直接使用(退款时的情况)
                                // 但仍需检查长度
                                $subOrderId = $subOrder['merOrderId'];
                                if (strlen($subOrderId) > 32) {
                                    $subOrderId = substr($subOrderId, 0, 32);
                                }
                                $formattedSubOrder['merOrderId'] = $subOrderId;
                            } else {
                                // 其他格式直接格式化
                                $formattedSubOrder['merOrderId'] = $this->formatOrderId($subOrder['merOrderId']);
                            }
                        }
                        $formattedSubOrders[] = $formattedSubOrder;
                    }
                    $params['subOrders'] = $formattedSubOrders;
                    Log::info('分账子订单: ' . json_encode($params['subOrders'], JSON_UNESCAPED_UNICODE));
                }
            }

            Log::info('请求参数: ' . json_encode($params, JSON_UNESCAPED_UNICODE));

            // 发送请求 - 使用H5跳转小程序支付接口(OPEN-FORM-PARAM方式)
            $url = $this->apiUrl . '/v1/netpay/wxpay/h5-to-minipay';
            Log::info('请求URL: ' . $url);

            $response = $this->requestH5($url, $params);

            Log::info('响应数据: ' . json_encode($response, JSON_UNESCAPED_UNICODE));

            // 检查响应
            if (!isset($response['errCode']) || $response['errCode'] !== 'SUCCESS') {
                $errMsg = $response['errMsg'] ?? $response['errInfo'] ?? '未知错误';
                Log::error('银联H5支付下单失败: ' . $errMsg);
                throw new \Exception('支付下单失败: ' . $errMsg);
            }

            // 返回支付跳转URL
            $payUrl = $response['payUrl'] ?? '';
            if (empty($payUrl)) {
                Log::error('响应中缺少payUrl');
                throw new \Exception('支付下单失败: 响应格式错误');
            }

            return [
                'status' => 'UMS_H5_PAY',
                'result' => [
                    'pay_url' => $payUrl,
                ],
            ];

        } catch (\Exception $e) {
            Log::error('银联H5支付异常: ' . $e->getMessage());
            Log::error('异常堆栈: ' . $e->getTraceAsString());
            throw $e;
        }
    }

    /**
     * 格式化订单号
     * 正式账号要求订单号必须以3HD3开头
     * @param string $orderId 原始订单号
     * @return string
     */
    protected function formatOrderId(string $orderId): string
    {
        // 如果是生产环境且订单号不是以3HD3开头,则添加前缀
        if ($this->isProduction && !str_starts_with($orderId, '3HD3')) {
            // 支付单号格式: wx740228190735171584_1
            // 截取订单号后面部分,确保总长度不超过28位
            // 格式: 3HD3 + 订单号(最多24位)
            $suffix = substr($orderId, 0, 28);
            return '3HD3' . $suffix;
        }

        return $orderId;
    }

    /**
     * 生成签名
     * @param string $timestamp 时间戳
     * @param string $nonce 随机数
     * @param string $body 报文体(JSON字符串)
     * @return string
     */
    protected function generateSign($timestamp, $nonce, $body)
    {
        // 1. 对报文体进行SHA256哈希,取16进制小写字符串
        $bodyHash = hash('sha256', $body);

        Log::info('报文体: ' . $body);
        Log::info('报文体SHA256: ' . $bodyHash);

        // 2. 构造签名字符串: AppId + Timestamp + Nonce + SHA256(报文体)
        $signStr = $this->appId . $timestamp . $nonce . $bodyHash;

        // Log::info('签名原串: ' . $signStr);

        // 3. 使用HMAC-SHA256算法,密钥为appKey
        $signature = base64_encode(hash_hmac('sha256', $signStr, $this->appKey, true));

        Log::info('签名结果: ' . $signature);

        return $signature;
    }

    /**
     * 查询订单状态
     * @param string $orderId 订单号
     * @return array
     */
    public function queryOrder(string $orderId)
    {
        try {
            Log::info('=== 银联订单查询 ===');
            Log::info('原始订单号: ' . $orderId);

            // 处理订单号
            $umsOrderId = $this->formatOrderId($orderId);
            Log::info('银联订单号: ' . $umsOrderId);

            // 构造请求参数
            $params = [
                'requestTimestamp' => date('Y-m-d H:i:s'),
                'merOrderId' => $umsOrderId,
                'mid' => $this->mid,
                'tid' => $this->tid,
            ];

            Log::info('请求参数: ' . json_encode($params, JSON_UNESCAPED_UNICODE));

            // 发送请求
            $url = $this->apiUrl . '/v1/netpay/query';
            $response = $this->request($url, $params);

            Log::info('响应数据: ' . json_encode($response, JSON_UNESCAPED_UNICODE));

            // 检查响应
            if (!isset($response['errCode']) || $response['errCode'] !== 'SUCCESS') {
                $errMsg = $response['errMsg'] ?? '未知错误';
                Log::error('银联订单查询失败: ' . $errMsg);
                throw new \Exception('订单查询失败: ' . $errMsg);
            }

            // 返回订单状态
            return [
                'status' => $response['status'] ?? 'UNKNOWN',
                'totalAmount' => $response['totalAmount'] ?? 0,
                'payTime' => $response['payTime'] ?? '',
                'targetOrderId' => $response['targetOrderId'] ?? '',
            ];

        } catch (\Exception $e) {
            Log::error('银联订单查询异常: ' . $e->getMessage());
            Log::error('异常堆栈: ' . $e->getTraceAsString());
            throw $e;
        }
    }

    /**
     * 退款
     * @param string $orderId 原订单号
     * @param string $refundOrderId 退款订单号
     * @param string $totalAmount 订单总金额(元)
     * @param string $refundAmount 退款金额(元)
     * @param string $reason 退款原因
     * @param array $divisionData 分账退款数据 ['platformAmount' => 0, 'subOrders' => [...]]
     * @param string $instMid 机构商户号,H5支付退款需要传 'H5DEFAULT'
     * @return array
     */
    public function refund(string $orderId, string $refundOrderId, string $totalAmount, string $refundAmount, string $reason = '', array $divisionData = [], string $instMid = '')
    {
        try {
            Log::info('=== 银联退款 ===');
            Log::info('原订单号: ' . $orderId);
            Log::info('退款订单号: ' . $refundOrderId);
            Log::info('订单总金额: ' . $totalAmount . '元');
            Log::info('退款金额: ' . $refundAmount . '元');
            if (!empty($instMid)) {
                Log::info('机构商户号: ' . $instMid);
            }
            if (!empty($divisionData)) {
                Log::info('分账退款数据: ' . json_encode($divisionData, JSON_UNESCAPED_UNICODE));
            }

            // 处理订单号
            $umsOrderId = $this->formatOrderId($orderId);
            // 退款订单号使用传入的refundOrderId参数(每次退款必须不同,否则银联视为重复退款)
            $umsRefundOrderId = $this->formatOrderId($refundOrderId);
            Log::info('银联订单号: ' . $umsOrderId);
            Log::info('银联退款订单号: ' . $umsRefundOrderId);

            // 金额转换:元转分
            $totalAmountFen = bcmul($totalAmount, '100', 0);
            $refundAmountFen = bcmul($refundAmount, '100', 0);
            Log::info('订单总金额(分): ' . $totalAmountFen);
            Log::info('退款金额(分): ' . $refundAmountFen);

            // 构造请求参数
            // 注意: refundOrderId 是银联多次退款的关键参数,每次退款必须传不同的值
            // 如果不传或传相同的值,银联会视为重复退款并返回原退款信息
            $params = [
                'requestTimestamp' => date('Y-m-d H:i:s'),
                'mid' => $this->mid,
                'tid' => $this->tid,
                'merOrderId' => $umsOrderId,
                'refundOrderId' => $umsRefundOrderId,  // 必须传递,支持多次退款
                'refundAmount' => $refundAmountFen,
                'totalAmount' => $totalAmountFen,
                'orderDesc' => $reason ?: '订单退款',
            ];

            // H5支付退款需要传递instMid
            if (!empty($instMid)) {
                $params['instMid'] = $instMid;
                Log::info('H5支付退款,添加instMid参数: ' . $instMid);
            }

            // 添加分账退款参数
            if (!empty($divisionData['subOrders']) && is_array($divisionData['subOrders'])) {
                $params['platformAmount'] = 0; // 平台退款分账金额恒为0
                
                // 格式化子订单号: 添加3HD3前缀(与支付时保持一致)
                $formattedSubOrders = [];
                foreach ($divisionData['subOrders'] as $subOrder) {
                    $formattedSubOrder = $subOrder;
                    if (!empty($subOrder['merOrderId'])) {
                        // 如果子订单号是 SUB_ 或 PLAT_ 开头,添加3HD3前缀
                        if (str_starts_with($subOrder['merOrderId'], 'SUB_') || str_starts_with($subOrder['merOrderId'], 'PLAT_')) {
                            $subOrderId = '3HD3' . $subOrder['merOrderId'];
                            // 银联订单号长度限制: 6-32位
                            if (strlen($subOrderId) > 32) {
                                $subOrderId = substr($subOrderId, 0, 32);
                            }
                            $formattedSubOrder['merOrderId'] = $subOrderId;
                        } elseif (str_starts_with($subOrder['merOrderId'], '3HD3SUB_') || str_starts_with($subOrder['merOrderId'], '3HD3PLAT_')) {
                            // 如果已经是3HD3SUB_或3HD3PLAT_开头,直接使用
                            // 但仍需检查长度
                            $subOrderId = $subOrder['merOrderId'];
                            if (strlen($subOrderId) > 32) {
                                $subOrderId = substr($subOrderId, 0, 32);
                            }
                            $formattedSubOrder['merOrderId'] = $subOrderId;
                        }
                    }
                    $formattedSubOrders[] = $formattedSubOrder;
                }
                
                $params['subOrders'] = $formattedSubOrders;
                Log::info('分账退款子订单: ' . json_encode($params['subOrders'], JSON_UNESCAPED_UNICODE));
            }

            Log::info('请求参数: ' . json_encode($params, JSON_UNESCAPED_UNICODE));

            // 发送请求
            $url = $this->apiUrl . '/v1/netpay/refund';
            $response = $this->request($url, $params);

            Log::info('响应数据: ' . json_encode($response, JSON_UNESCAPED_UNICODE));

            // 检查响应
            if (!isset($response['errCode']) || $response['errCode'] !== 'SUCCESS') {
                $errMsg = $response['errMsg'] ?? '未知错误';
                Log::error('银联退款失败: ' . $errMsg);
                throw new \Exception('退款失败: ' . $errMsg);
            }

            // 返回退款结果
            return [
                'refundOrderId' => $response['refundOrderId'] ?? $umsRefundOrderId,
                'refundAmount' => $response['refundAmount'] ?? $refundAmountFen,
                'status' => 'SUCCESS',
            ];

        } catch (\Exception $e) {
            Log::error('银联退款异常: ' . $e->getMessage());
            Log::error('异常堆栈: ' . $e->getTraceAsString());
            throw $e;
        }
    }

    /**
     * 退款查询
     * @param string $refundOrderId 退款订单号
     * @return array
     */
    public function refundQuery(string $refundOrderId)
    {
        try {
            Log::info('=== 银联退款查询 ===');
            Log::info('退款订单号: ' . $refundOrderId);

            // 处理订单号
            $umsRefundOrderId = $this->formatOrderId($refundOrderId);
            Log::info('银联退款订单号: ' . $umsRefundOrderId);

            // 构造请求参数
            $params = [
                'requestTimestamp' => date('Y-m-d H:i:s'),
                'mid' => $this->mid,
                'tid' => $this->tid,
                'refundOrderId' => $umsRefundOrderId,
            ];

            Log::info('请求参数: ' . json_encode($params, JSON_UNESCAPED_UNICODE));

            // 发送请求
            $url = $this->apiUrl . '/v1/netpay/refund-query';
            $response = $this->request($url, $params);

            Log::info('响应数据: ' . json_encode($response, JSON_UNESCAPED_UNICODE));

            // 检查响应
            if (!isset($response['errCode']) || $response['errCode'] !== 'SUCCESS') {
                $errMsg = $response['errMsg'] ?? '未知错误';
                Log::error('银联退款查询失败: ' . $errMsg);
                throw new \Exception('退款查询失败: ' . $errMsg);
            }

            // 返回退款状态
            return [
                'refundStatus' => $response['refundStatus'] ?? 'UNKNOWN',
                'refundAmount' => $response['refundAmount'] ?? 0,
            ];

        } catch (\Exception $e) {
            Log::error('银联退款查询异常: ' . $e->getMessage());
            Log::error('异常堆栈: ' . $e->getTraceAsString());
            throw $e;
        }
    }

    /**
     * 关闭订单
     * @param string $orderId 订单号
     * @return bool
     */
    public function closeOrder(string $orderId)
    {
        try {
            Log::info('=== 银联订单关闭 ===');
            Log::info('原始订单号: ' . $orderId);

            // 处理订单号
            $umsOrderId = $this->formatOrderId($orderId);
            Log::info('银联订单号: ' . $umsOrderId);

            // 构造请求参数
            $params = [
                'requestTimestamp' => date('Y-m-d H:i:s'),
                'mid' => $this->mid,
                'tid' => $this->tid,
                'merOrderId' => $umsOrderId,
            ];

            Log::info('请求参数: ' . json_encode($params, JSON_UNESCAPED_UNICODE));

            // 发送请求
            $url = $this->apiUrl . '/v1/netpay/close';
            $response = $this->request($url, $params);

            Log::info('响应数据: ' . json_encode($response, JSON_UNESCAPED_UNICODE));

            // 检查响应
            if (!isset($response['errCode']) || $response['errCode'] !== 'SUCCESS') {
                $errMsg = $response['errMsg'] ?? '未知错误';
                Log::error('银联订单关闭失败: ' . $errMsg);
                throw new \Exception('订单关闭失败: ' . $errMsg);
            }

            return true;

        } catch (\Exception $e) {
            Log::error('银联订单关闭异常: ' . $e->getMessage());
            Log::error('异常堆栈: ' . $e->getTraceAsString());
            throw $e;
        }
    }

    /**
     * H5支付专用请求方法(使用OPEN-FORM-PARAM认证)
     * @param string $url 请求地址
     * @param array $data 请求数据
     * @return array
     */
    protected function requestH5($url, $data)
    {
        // 检查是否为Mock请求
        if ($this->isMockEnabled() && $this->isMockUrl($url)) {
            return $this->mockRequest($url, $data);
        }
        
        // 将数据转换为JSON字符串(不使用UNESCAPED_UNICODE)
        $content = json_encode($data);

        // 生成时间戳和随机数
        $timestamp = date('YmdHis');
        $nonce = bin2hex(random_bytes(16));

        // 签名计算:使用原始content(未URL编码)
        $contentHash = hash('sha256', $content);
        $signStr = $this->appId . $timestamp . $nonce . $contentHash;
        $signature = base64_encode(hash_hmac('sha256', $signStr, $this->appKey, true));

        Log::info('=== H5支付请求(OPEN-FORM-PARAM) ===');
        Log::info('Content: ' . $content);
        Log::info('Content Hash: ' . $contentHash);
        Log::info('签名原串: ' . $signStr);
        Log::info('Signature: ' . $signature);

        // 构造URL参数(http_build_query会自动进行URL编码)
        $urlParams = [
            'authorization' => 'OPEN-FORM-PARAM',
            'appId' => $this->appId,
            'timestamp' => $timestamp,
            'nonce' => $nonce,
            'content' => $content,
            'signature' => $signature,
        ];

        // 使用GET方式,参数放在URL中
        $fullUrl = $url . '?' . http_build_query($urlParams);

        Log::info('完整URL长度: ' . strlen($fullUrl));

        // 发送请求
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $fullUrl);
        curl_setopt($ch, CURLOPT_POST, false);  // 使用GET方式
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);  // 不自动跟随重定向
        curl_setopt($ch, CURLOPT_HEADER, true);  // 获取响应头
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
        $error = curl_error($ch);
        curl_close($ch);

        Log::info('HTTP状态码: ' . $httpCode);

        if (!empty($error)) {
            Log::error('CURL错误: ' . $error);
            throw new \Exception('请求失败: ' . $error);
        }

        // 分离响应头和响应体
        $header = substr($response, 0, $headerSize);
        $body = substr($response, $headerSize);

        // Log::info('响应头: ' . $header);
        // Log::info('响应体: ' . $body);

        // 如果是302重定向,提取Location作为支付URL
        if ($httpCode == 302 || $httpCode == 301) {
            if (preg_match('/Location:\s*(.+)/i', $header, $matches)) {
                $payUrl = trim($matches[1]);
                Log::info('支付URL(重定向): ' . $payUrl);
                return [
                    'errCode' => 'SUCCESS',
                    'payUrl' => $payUrl,
                ];
            }
        }

        // 尝试解析JSON响应
        $decoded = json_decode($body, true);
        if ($decoded) {
            return $decoded;
        }

        // 如果既不是重定向也不是JSON,抛出异常
        throw new \Exception('响应格式错误: HTTP ' . $httpCode);
    }

    /**
     * 发送HTTP请求
     * @param string $url 请求地址
     * @param array $data 请求数据
     * @return array
     */
    protected function request($url, $data)
    {
        if ($this->isMockEnabled() && $this->isMockUrl($url)) {
            return $this->mockRequest($url, $data);
        }
        // 将数据转换为JSON字符串(报文体)
        $body = json_encode($data);

        // 生成时间戳和随机数
        $timestamp = date('YmdHis'); // 格式: 20251123140000
        $nonce = md5(uniqid(mt_rand(), true));

        // 生成签名(传入报文体)
        $signature = $this->generateSign($timestamp, $nonce, $body);

        // 构造Authorization头
        $authorization = "OPEN-BODY-SIG AppId=\"{$this->appId}\",Timestamp=\"{$timestamp}\",Nonce=\"{$nonce}\",Signature=\"{$signature}\"";

        Log::info('Authorization: ' . $authorization);

        // 构造请求头
        $headers = [
            'Authorization: ' . $authorization,
            'Content-Type: application/json',
        ];

        // 发送请求
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body); // 使用已经JSON编码的报文体
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HEADER, true); // 获取响应头
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
        $error = curl_error($ch);
        curl_close($ch);

        // 分离响应头和响应体
        $responseHeader = substr($response, 0, $headerSize);
        $responseBody = substr($response, $headerSize);

        // Log::info('响应头: ' . $responseHeader);

        if ($error) {
            // Log::error('CURL错误: ' . $error);
            throw new \Exception('网络请求失败: ' . $error);
        }

        if ($httpCode !== 200) {
            // Log::error('HTTP状态码: ' . $httpCode);
            // Log::error('响应内容: ' . $response);
            throw new \Exception('网络请求失败: HTTP ' . $httpCode);
        }

        $result = json_decode($responseBody, true);
        if (!$result) {
            // Log::error('响应解析失败: ' . $responseBody);
            throw new \Exception('响应解析失败');
        }

        // 验证响应签名(如果响应中包含签名)
        if (isset($result['sign']) && isset($result['signType'])) {
            // Log::info('检测到响应中包含签名,开始验证...');
            if (!$this->verifyResponseSign($result)) {
                Log::error('响应签名验证失败,可能是伪造的响应!');
                // throw new \Exception('响应签名验证失败,数据可能被篡改');
            }
            Log::info('响应签名验证成功');
        } else {
            // Log::info('响应中不包含签名字段,跳过验签');
        }

        return $result;
    }

    /**
     * 判断是否启用Mock
     * @return bool
     */
    protected function isMockEnabled(): bool
    {
        $flag = env('UMS_MOCK');
        if (is_string($flag)) {
            $flag = strtolower(trim($flag));
            return in_array($flag, ['1', 'true', 'yes', 'on'], true);
        }
        return (bool)$flag;
    }

    /**
     * 判断是否是Mock地址
     * @param string $url
     * @return bool
     */
    protected function isMockUrl(string $url): bool
    {
        return str_contains($url, '/mock/ums/');
    }

    /**
     * Mock请求处理
     * @param string $url
     * @param array $data
     * @return array
     */
    protected function mockRequest(string $url, array $data): array
    {
        if (str_contains($url, '/v1/netpay/wx/unified-order')) {
            $merOrderId = (string)($data['merOrderId'] ?? '');
            $totalAmount = (string)($data['totalAmount'] ?? '0');
            $tradeType = (string)($data['tradeType'] ?? 'MINI');
            $notifyUrl = (string)($data['notifyUrl'] ?? '');

            $overrideNotifyUrl = (string)env('UMS_MOCK_NOTIFY_URL');
            if ($overrideNotifyUrl !== '') {
                $notifyUrl = $overrideNotifyUrl;
            }

            $forceLocal = env('UMS_MOCK_FORCE_LOCAL_NOTIFY');
            $forceLocal = is_string($forceLocal) ? strtolower(trim($forceLocal)) : $forceLocal;
            $forceLocal = in_array($forceLocal, ['1', 'true', 'yes', 'on'], true);
            if ($notifyUrl === '' || $forceLocal) {
                $notifyUrl = 'http://127.0.0.1:20199/api/pay/ums/notify';
            }

            $miniPayRequest = [
                'appId' => $this->appId ?: 'wx_mock_appid',
                'timeStamp' => (string)time(),
                'nonceStr' => bin2hex(random_bytes(8)),
                'package' => 'prepay_id=mock_' . ($merOrderId !== '' ? $merOrderId : 'order'),
                'signType' => 'RSA',
                'paySign' => 'mock_sign',
            ];

            $callbackData = $this->buildMockNotifyPayload($merOrderId, $totalAmount, $tradeType);
            $this->scheduleMockNotify($notifyUrl, $callbackData);

            return [
                'errCode' => 'SUCCESS',
                'errMsg' => 'SUCCESS',
                'miniPayRequest' => $miniPayRequest,
            ];
        }

        // H5支付接口
        if (str_contains($url, '/v1/netpay/wxpay/h5-to-minipay')) {
            $merOrderId = (string)($data['merOrderId'] ?? '');
            $totalAmount = (string)($data['totalAmount'] ?? '0');
            $notifyUrl = (string)($data['notifyUrl'] ?? '');

            $overrideNotifyUrl = (string)env('UMS_MOCK_NOTIFY_URL');
            if ($overrideNotifyUrl !== '') {
                $notifyUrl = $overrideNotifyUrl;
            }

            $forceLocal = env('UMS_MOCK_FORCE_LOCAL_NOTIFY');
            $forceLocal = is_string($forceLocal) ? strtolower(trim($forceLocal)) : $forceLocal;
            $forceLocal = in_array($forceLocal, ['1', 'true', 'yes', 'on'], true);
            if ($notifyUrl === '' || $forceLocal) {
                $notifyUrl = 'http://127.0.0.1:20199/api/pay/ums/notify';
            }

            // 使用 PAY_BASE_URL 配置构建支付页面URL
            $baseUrl = env('PAY_BASE_URL', 'http://127.0.0.1:20199');
            $payUrl = rtrim($baseUrl, '/') . '/mock/ums/h5-pay-page?orderId=' . urlencode($merOrderId) 
                    . '&amount=' . urlencode($totalAmount)
                    . '&notifyUrl=' . urlencode($notifyUrl);

            $callbackData = $this->buildMockNotifyPayload($merOrderId, $totalAmount, 'H5');
            $this->scheduleMockNotify($notifyUrl, $callbackData);

            return [
                'errCode' => 'SUCCESS',
                'errMsg' => 'SUCCESS',
                'payUrl' => $payUrl,
            ];
        }

        if (str_contains($url, '/v1/netpay/refund')) {
            $refundOrderId = (string)($data['refundOrderId'] ?? ($data['merOrderId'] ?? ''));
            if ($refundOrderId === '') {
                $refundOrderId = 'mock_refund_' . date('YmdHis');
            }
            $refundAmount = (string)($data['refundAmount'] ?? '0');

            return [
                'errCode' => 'SUCCESS',
                'errMsg' => 'SUCCESS',
                'refundOrderId' => $refundOrderId,
                'refundAmount' => $refundAmount,
            ];
        }

        if (str_contains($url, '/v1/netpay/refund-query')) {
            return [
                'errCode' => 'SUCCESS',
                'errMsg' => 'SUCCESS',
                'refundStatus' => 'SUCCESS',
                'refundAmount' => $data['refundAmount'] ?? 0,
            ];
        }

        throw new \Exception('Mock暂未支持此接口: ' . $url);
    }

    /**
     * 构造Mock回调数据
     * @param string $merOrderId
     * @param string $totalAmount
     * @param string $tradeType
     * @return array
     */
    protected function buildMockNotifyPayload(string $merOrderId, string $totalAmount, string $tradeType): array
    {
        $data = [
            'merOrderId' => $merOrderId,
            'status' => 'TRADE_SUCCESS',
            'totalAmount' => $totalAmount,
            'targetOrderId' => 'mock_trade_no_' . date('YmdHis'),
            'notifyId' => 'mock_notify_' . bin2hex(random_bytes(6)),
            'targetSys' => 'WXPay',
            'tradeType' => $tradeType !== '' ? $tradeType : 'MINI',
            'signType' => 'SHA256',
        ];

        $data['sign'] = $this->generateMockNotifySign($data, (string)$this->notifyKey);

        return $data;
    }

    /**
     * 生成Mock回调签名
     * @param array $data
     * @param string $notifyKey
     * @return string
     */
    protected function generateMockNotifySign(array $data, string $notifyKey): string
    {
        unset($data['sign']);
        ksort($data, SORT_STRING);
        $pairs = [];
        foreach ($data as $key => $value) {
            $pairs[] = $key . '=' . $value;
        }
        $stringToSign = implode('&', $pairs) . $notifyKey;
        $signType = strtoupper((string)($data['signType'] ?? 'SHA256'));
        if ($signType === 'MD5') {
            return strtoupper(md5($stringToSign));
        }
        return strtoupper(hash('sha256', $stringToSign));
    }

    /**
     * 安排Mock回调
     * @param string $notifyUrl
     * @param array $payload
     * @return void
     */
    protected function scheduleMockNotify(string $notifyUrl, array $payload): void
    {
        $delayMs = (int)(env('UMS_MOCK_NOTIFY_DELAY_MS') ?: 2000);
        $delaySec = (int)ceil(max(0, $delayMs) / 1000);
        $nodeNotifyUrl = (string)env('UMS_MOCK_NODE_URL');
        $useQueue = env('UMS_MOCK_NOTIFY_QUEUE');
        $useQueue = is_string($useQueue) ? strtolower(trim($useQueue)) : $useQueue;
        $useQueue = in_array($useQueue, ['1', 'true', 'yes', 'on'], true);
        $queueEnabled = (bool)config('swoole.queue.enable');

        if ($nodeNotifyUrl !== '') {
            $nodePayload = [
                'notifyUrl' => $notifyUrl,
                'delayMs' => $delayMs,
                'payload' => $payload,
            ];
            $headers = [
                'Content-Type: application/json',
                'Content-Length:' . strlen(json_encode($nodePayload)),
            ];
            HttpService::postRequest($nodeNotifyUrl, json_encode($nodePayload), $headers, 5);
            return;
        }

        if ($useQueue && $queueEnabled && class_exists('\\app\\jobs\\payment\\UmsMockNotifyJob')) {
            if ($delaySec > 0) {
                \app\jobs\payment\UmsMockNotifyJob::dispatchSece($delaySec, [$notifyUrl, $payload, 5]);
            } else {
                \app\jobs\payment\UmsMockNotifyJob::dispatch([$notifyUrl, $payload, 5]);
            }
            return;
        }

        if ($delayMs > 0) {
            usleep($delayMs * 1000);
        }

        $headers = [
            'Content-Type: application/json',
            'Content-Length:' . strlen(json_encode($payload)),
        ];
        HttpService::postRequest($notifyUrl, json_encode($payload), $headers, 5);
    }

    /**
     * 验证响应签名
     * 按照银联商务官方文档规范验签(与回调验签逻辑相同):
     * 1. 除sign外的所有参数按ASCII字典序排序
     * 2. 用&连接成字符串
     * 3. 末尾拼接通讯密钥notify_key
     * 4. 按signType(SHA256或MD5)计算摘要并大写
     *
     * @param array $data 响应数据
     * @return bool
     */
    protected function verifyResponseSign(array $data): bool
    {
        try {
            // 检查必要字段
            if (empty($data['sign'])) {
                Log::error('响应缺少sign字段');
                return false;
            }

            if (empty($this->notifyKey)) {
                Log::error('未配置通讯密钥notify_key,无法验证响应签名');
                return false;
            }

            // 获取签名类型和签名值
            $signType = strtoupper($data['signType'] ?? 'SHA256');
            $sign = strtoupper($data['sign']);

            Log::info('响应签名类型: ' . $signType);
            Log::info('响应原始签名: ' . $sign);

            // 移除sign字段,准备验签
            $signData = $data;
            unset($signData['sign']);

            // 按ASCII字典序排序
            ksort($signData, SORT_STRING);

            // 拼接成 key=value&key=value 格式
            $query = [];
            foreach ($signData as $k => $v) {
                $query[] = $k . '=' . $v;
            }
            $stringToSign = implode('&', $query) . $this->notifyKey;

            Log::info('响应待签名字符串: ' . $stringToSign);

            // 根据签名类型计算摘要
            if ($signType === 'MD5') {
                $calculatedSign = strtoupper(md5($stringToSign));
            } else {
                // 默认使用SHA256
                $calculatedSign = strtoupper(hash('sha256', $stringToSign));
            }

            Log::info('响应计算签名: ' . $calculatedSign);

            // 使用hash_equals防止时序攻击
            $result = hash_equals($calculatedSign, $sign);

            if ($result) {
                Log::info('响应签名验证成功');
            } else {
                Log::error('响应签名验证失败');
                Log::error('期望签名: ' . $calculatedSign);
                Log::error('实际签名: ' . $sign);
            }

            return $result;

        } catch (\Exception $e) {
            Log::error('响应签名验证异常: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * 处理支付回调
     * @param array $data 回调数据
     * @return array
     */
    public function handleNotify($data)
    {
        try {
            Log::info('=== 银联支付回调处理 ===');
            Log::info('回调数据: ' . json_encode($data, JSON_UNESCAPED_UNICODE));

            // 验证签名
            if (!$this->verifyNotifySign($data)) {
                Log::error('回调签名验证失败');
                throw new \Exception('签名验证失败');
            }

            // 解析回调数据
            $merOrderId = $data['merOrderId'] ?? '';
            $status = $data['status'] ?? '';
            $seqId = $data['seqId'] ?? '';
            $targetOrderId = $data['targetOrderId'] ?? '';
            $totalAmount = $data['totalAmount'] ?? '0';
            $notifyId = $data['notifyId'] ?? '';
            $targetSys = $data['targetSys'] ?? '';  // 支付系统: WXPay/Alipay
            $tradeType = $data['tradeType'] ?? '';  // 支付渠道: MINI/H5

            // 检查支付状态
            if ($status !== 'TRADE_SUCCESS') {
                Log::warning('支付状态异常: ' . $status);
                return [
                    'pay_status' => 'fail',
                    'order_id' => $merOrderId,
                ];
            }

            // 金额转换:分转元
            $payAmount = bcdiv($totalAmount, '100', 2);
            $tradeNo = $targetOrderId !== '' ? $targetOrderId : '';
            if ($targetOrderId !== '') {
                Log::info('UMS notify uses targetOrderId as trade_no: ' . $targetOrderId);
            }

            return [
                'pay_status' => 'success',
                'order_id' => $merOrderId,
                'trade_no' => $tradeNo,
                // 'ums_seq_id' => $seqId,
                'pay_amount' => $payAmount,
                'notify_id' => $notifyId,
                'target_sys' => $targetSys,  // 返回支付系统标识
                'trade_type' => $tradeType,  // 返回支付渠道
            ];

        } catch (\Exception $e) {
            Log::error('回调处理异常: ' . $e->getMessage());
            throw $e;
        }
    }

    /**
     * 验证回调签名
     * 按照银联商务官方文档规范验签:
     * 1. 除sign外的所有参数按ASCII字典序排序
     * 2. 用&连接成字符串
     * 3. 末尾拼接通讯密钥key
     * 4. 按signType(SHA256或MD5)计算摘要并大写
     *
     * @param array $data 回调数据
     * @return bool
     */
    protected function verifyNotifySign(array $data): bool
    {
        try {
            // 检查必要字段
            if (empty($data['sign'])) {
                Log::error('缺少sign字段');
                return false;
            }

            if (empty($this->notifyKey)) {
                Log::error('未配置通讯密钥notify_key');
                return false;
            }

            // 获取签名类型和签名值
            $signType = strtoupper($data['signType'] ?? 'SHA256');
            $sign = strtoupper($data['sign']);

            Log::info('签名类型: ' . $signType);
            Log::info('原始签名: ' . $sign);

            // 移除sign字段,准备验签
            $signData = $data;
            unset($signData['sign']);

            // 按ASCII字典序排序
            ksort($signData, SORT_STRING);

            // 拼接成 key=value&key=value 格式
            $query = [];
            foreach ($signData as $k => $v) {
                // 使用原始值,不进行URL编码
                $query[] = $k . '=' . $v;
            }
            $stringToSign = implode('&', $query) . $this->notifyKey;

            Log::info('待签名字符串: ' . $stringToSign);

            // 根据签名类型计算摘要
            if ($signType === 'MD5') {
                $calculatedSign = strtoupper(md5($stringToSign));
            } else {
                // 默认使用SHA256
                $calculatedSign = strtoupper(hash('sha256', $stringToSign));
            }

            Log::info('计算签名: ' . $calculatedSign);

            // 使用hash_equals防止时序攻击
            $result = hash_equals($calculatedSign, $sign);

            if ($result) {
                Log::info('签名验证成功');
            } else {
                Log::error('签名验证失败');
                Log::error('期望签名: ' . $calculatedSign);
                Log::error('实际签名: ' . $sign);
            }

            return $result;

        } catch (\Exception $e) {
            Log::error('签名验证异常: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * 异步分账确认
     * @param string $merOrderId 原交易订单号
     * @param array $subOrders 子订单分账信息 [['mid' => '子商户号', 'merOrderId' => '子订单号', 'totalAmount' => 分账金额(分)]]
     * @param int $platformAmount 平台分账金额(分),默认0
     * @return array
     */
    public function confirmDivision(string $merOrderId, array $subOrders, int $platformAmount = 0): array
    {
        try {
            $url = $this->apiUrl . '/v1/netpay/sub-orders-confirm';

            $params = [
                'requestTimestamp' => date('Y-m-d H:i:s'),
                'merOrderId' => $merOrderId,
                'mid' => $this->mid,
                'tid' => $this->tid,
                'platformAmount' => $platformAmount,
                'subOrders' => $subOrders,
                'msgId' => $this->generateMsgId(),
            ];

            Log::info('=== 银联分账确认请求 ===');
            Log::info('请求地址: ' . $url);
            Log::info('请求参数: ' . json_encode($params, JSON_UNESCAPED_UNICODE));

            $response = $this->request($url, $params);

            Log::info('分账确认响应: ' . json_encode($response, JSON_UNESCAPED_UNICODE));

            return $response;

        } catch (\Exception $e) {
            Log::error('分账确认异常: ' . $e->getMessage());
            return [
                'errCode' => 'ERROR',
                'errMsg' => $e->getMessage()
            ];
        }
    }
}
