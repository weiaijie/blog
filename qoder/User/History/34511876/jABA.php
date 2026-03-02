<?php
/**
 * 银联商务支付统一测试脚本（按官方文档的原始请求流程实现）
 *
 * 使用方法：
 * docker exec -it crmeb_pro 
 *   php test_ums.php mini                        # 测试小程序下单
 *   php test_ums.php h5                          # 测试H5下单
 *   php test_ums.php query <订单号>               # 测试订单查询
 *   php test_ums.php refund <订单号> [金额]        # 测试普通退款（可指定金额，单位：元）
 *   php test_ums.php refund-multi <订单号>         # 测试多次退款（交互式输入多次退款金额）
 *   php test_ums.php refund-division <订单号>      # 测试分账退款
 *   php test_ums.php refund-query <退款单号>      # 测试退款查询
 *   php test_ums.php close <订单号>               # 测试订单关闭
 *   php test_ums.php test-notify                 # 测试回调验签
 *   php test_ums.php all                         # 依次执行全部测试
 */

date_default_timezone_set('Asia/Shanghai');
require __DIR__ . '/vendor/autoload.php';

$action = $argv[1] ?? 'help';
$param = $argv[2] ?? '';

try {
    // 根据操作类型加载对应的账号配置
    $paymentType = ($action === 'h5') ? 'h5' : 'mini';
    $account = loadAccountConfig($paymentType);
    $testOptions = loadTestOptions();

    echo "========================================\n";
    echo "银联商务支付测试脚本（官方原始请求版）\n";
    echo "========================================\n";
    echo "当前账号: {$account['name']} ({$account['mid']}/{$account['tid']})\n";
    echo "API地址: {$account['api_url']}\n\n";

    switch ($action) {
        case 'mini':
            runMiniPay($account, $testOptions);
            break;
        case 'h5':
            runH5Pay($account, $testOptions);
            break;
        case 'close':
            close($account, $testOptions);
            break;
        case 'query':
            requireParam($param, '订单号', 'php test_ums.php query <订单号>');
            runQuery($account, $param);
            break;
        case 'refund':
            requireParam($param, '订单号', 'php test_ums.php refund <订单号> [金额]');
            $refundAmount = $argv[3] ?? ''; // 可选的退款金额参数
            runRefund($account, $param, $testOptions, $refundAmount);
            break;
        case 'refund-multi':
            requireParam($param, '订单号', 'php test_ums.php refund-multi <订单号>');
            runMultiRefund($account, $param, $testOptions);
            break;
        case 'refund-division':
            requireParam($param, '订单号', 'php test_ums.php refund-division <订单号>');
            runRefundWithDivision($account, $param, $testOptions);
            break;
        case 'refund-query':
            requireParam($param, '退款单号', 'php test_ums.php refund-query <退款单号>');
            runRefundQuery($account, $param);
            break;
        case 'close':
            requireParam($param, '订单号', 'php test_ums.php close <订单号>');
            runCloseOrder($account, $param);
            break;
        case 'test-notify':
            runTestNotify($account);
            break;
        case 'all':
            runAll($account, $testOptions);
            break;
        default:
            showHelp();
    }
} catch (\Throwable $e) {
    echo "❌ 测试异常: {$e->getMessage()}\n";
    exit(1);
}

// ========== CLI Actions ==========

function runMiniPay(array $account, array $opts): void
{
    $orderId = 'wx' . date('YmdHis') . rand(1000, 9999);
    $payload = [
        'requestTimestamp' => date('Y-m-d H:i:s'),
        // 'merOrderId' => formatOrderId($orderId, $account),
        'merOrderId' => '3HD3wx733318125222625280_1',
        'mid' => $account['mid'],
        'tid' => $account['tid'],
        'instMid' => 'MINIDEFAULT',
        'tradeType' => 'MINI',
        'totalAmount' => amountToFen($opts['amount']),
        'orderDesc' => '测试订单',
        'notifyUrl' => $opts['notify_url'],
        'subAppId' => $opts['sub_app_id'],
        'subOpenId' => $opts['openid'],
    ];

    echo "原始订单号: {$orderId}\n";
    echo "银联订单号: {$payload['merOrderId']}\n\n";

    $response = executeUmsCall('MINI 下单', $account, '/v1/netpay/wx/unified-order', $payload);
    persistLastOrderId($orderId);
    displayResultTips($response);
}

function close(array $account, array $opts): void
{
    $orderId = 'wx' . date('YmdHis') . rand(1000, 9999);
    $payload = [
        'requestTimestamp' => date('Y-m-d H:i:s'),
        // 'merOrderId' => formatOrderId($orderId, $account),
        'merOrderId' => '3HD3wx733318125222625280',
        'mid' => $account['mid'],
        'tid' => $account['tid'],
        'instMid' => 'MINIDEFAULT',
        'tradeType' => 'MINI',
        'totalAmount' => amountToFen($opts['amount']),
        'orderDesc' => '测试订单',
        'notifyUrl' => $opts['notify_url'],
        'subAppId' => $opts['sub_app_id'],
        'subOpenId' => $opts['openid'],
    ];

    echo "原始订单号: {$orderId}\n";
    echo "银联订单号: {$payload['merOrderId']}\n\n";

    $response = executeUmsCall('MINI 下单', $account, '/v1/netpay/close', $payload);
    persistLastOrderId($orderId);
    displayResultTips($response);
}

function runH5Pay(array $account, array $opts): void
{
    echo "请选择H5支付方式:\n";
    echo "1. H5微信支付 (/v1/netpay/wxpay/h5-pay)\n";
    echo "2. H5跳转微信小程序支付 (/v1/netpay/wxpay/h5-to-minipay)\n";
    echo "请输入选择 (1 或 2, 默认2): ";

    $choice = trim(fgets(STDIN));
    if (empty($choice)) {
        $choice = '2';
    }

    $orderId = 'wx' . date('YmdHis') . rand(1000, 9999);

    if ($choice === '1') {
        // H5微信支付 - 需要 sceneType, merAppName, merAppId
        $payload = [
            'requestTimestamp' => date('Y-m-d H:i:s'),
            'merOrderId' => formatOrderId($orderId, $account),
            'mid' => $account['mid'],
            'tid' => $account['tid'],
            'instMid' => 'H5DEFAULT',
            'totalAmount' => amountToFen($opts['amount']),
            'orderDesc' => '测试订单(H5)',
            'notifyUrl' => $opts['notify_url'],
            'returnUrl' => $opts['return_url'],
            'sceneType' => 'IOS_WAP',
            'merAppName' => '香溢乐享优选',
            'merAppId' => 'https://m.chinaums.com',
        ];

        echo "\n使用: H5微信支付\n";
        echo "原始订单号: {$orderId}\n";
        echo "银联订单号: {$payload['merOrderId']}\n\n";

        $response = executeUmsH5Call('H5微信支付', $account, '/v1/netpay/wxpay/h5-pay', $payload);
    } else {
        // H5跳转微信小程序支付 - 不需要 sceneType, merAppName, merAppId
        $payload = [
            'requestTimestamp' => date('Y-m-d H:i:s'),
            'merOrderId' => formatOrderId($orderId, $account),
            'mid' => $account['mid'],
            'tid' => $account['tid'],
            'instMid' => 'H5DEFAULT',
            'totalAmount' => amountToFen($opts['amount']),
        ];

        echo "\n使用: H5跳转微信小程序支付\n";
        echo "原始订单号: {$orderId}\n";
        echo "银联订单号: {$payload['merOrderId']}\n\n";

        $response = executeUmsH5Call('H5跳转小程序支付', $account, '/v1/netpay/wxpay/h5-to-minipay', $payload);
    }

    persistLastOrderId($orderId);
    displayResultTips($response);

}

function runQuery(array $account, string $orderId): void
{
    $payload = [
        'requestTimestamp' => date('Y-m-d H:i:s'),
        'merOrderId' => formatOrderId($orderId, $account),
        // 'instMid' => 'H5DEFAULT',
        'mid' => $account['mid'],
        'tid' => $account['tid'],
    ];

    executeUmsCall('订单查询', $account, '/v1/netpay/query', $payload);
}

function runRefund(array $account, string $orderId, array $opts): void
{
    $refundOrderId = 'RF' . date('YmdHis') . rand(1000, 9999);
    $payload = [
        'requestTimestamp' => date('Y-m-d H:i:s'),
        'mid' => $account['mid'],
        'tid' => $account['tid'],
        'merOrderId' => formatOrderId($orderId, $account),
        // 'refundOrderId' => '3HD3wx733318576710090752',//formatOrderId($refundOrderId, $account),
        'refundAmount' => 10, //amountToFen($opts['amount']),
        'totalAmount' => 10, //amountToFen($opts['amount']),
        'orderDesc' => '测试退款',
    ];

    echo "原订单号: {$orderId}\n";
    echo "退款订单号: {$refundOrderId}\n\n";

    $response = executeUmsCall('发起退款', $account, '/v1/netpay/refund', $payload);
    displayResultTips($response);
}

function runRefundWithDivision(array $account, string $orderId, array $opts): void
{
    echo "========================================\n";
    echo "分账退款测试\n";
    echo "========================================\n";

    // 从配置文件读取平台分账配置
    $configFile = __DIR__ . '/config/UmsPayConfig.json';
    $config = json_decode(file_get_contents($configFile), true);
    $platformDivision = $config['platform_division'] ?? null;

    if (!$platformDivision || empty($platformDivision['mid'])) {
        echo "❌ 未配置平台分账信息\n";
        return;
    }

    echo "请输入以下信息:\n";

    // 输入退款金额
    echo "退款总金额(元,默认0.04): ";
    $refundAmount = trim(fgets(STDIN));
    if (empty($refundAmount)) {
        $refundAmount = '0.04';
    }

    // 输入供应商退款金额
    echo "供应商退款金额(元,默认0.03): ";
    $supplierRefundAmount = trim(fgets(STDIN));
    if (empty($supplierRefundAmount)) {
        $supplierRefundAmount = '0.03';
    }

    // 计算平台退款金额
    $platformRefundAmount = bcsub($refundAmount, $supplierRefundAmount, 2);

    echo "\n退款金额分配:\n";
    echo "  总退款金额: {$refundAmount}元\n";
    echo "  供应商退款: {$supplierRefundAmount}元\n";
    echo "  平台退款: {$platformRefundAmount}元\n\n";

    // 去掉支付单号的时间戳后缀
    // 例如: 3HD3wx740228190735171584_1_0561 -> 3HD3wx740228190735171584_1
    $subOrderBase = $orderId;
    $lastUnderscorePos = strrpos($subOrderBase, '_');
    if ($lastUnderscorePos !== false) {
        $subOrderBase = substr($subOrderBase, 0, $lastUnderscorePos);
    }

    // 生成默认子订单号
    $defaultSupplierSubOrderId = 'SUB_' . $subOrderBase;
    $defaultPlatformSubOrderId = 'PLAT_' . $subOrderBase;

    // 输入供应商子订单号
    echo "供应商子订单号(默认 {$defaultSupplierSubOrderId}): ";
    $supplierSubOrderId = trim(fgets(STDIN));
    if (empty($supplierSubOrderId)) {
        $supplierSubOrderId = $defaultSupplierSubOrderId;
    }

    // 输入平台子订单号
    echo "平台子订单号(默认 {$defaultPlatformSubOrderId}): ";
    $platformSubOrderId = trim(fgets(STDIN));
    if (empty($platformSubOrderId)) {
        $platformSubOrderId = $defaultPlatformSubOrderId;
    }

    echo "\n子订单号:\n";
    echo "  供应商子订单号: {$supplierSubOrderId}\n";
    echo "  平台子订单号: {$platformSubOrderId}\n\n";

    // 构造分账退款参数
    $subOrders = [
        [
            'mid' => $platformDivision['mid'],
            'merOrderId' => $supplierSubOrderId,
            'totalAmount' => bcmul($supplierRefundAmount, '100', 0),
        ],
        [
            'mid' => $platformDivision['mid'],
            'merOrderId' => $platformSubOrderId,
            'totalAmount' => bcmul($platformRefundAmount, '100', 0),
        ],
    ];

    $refundOrderId = 'RF' . date('YmdHis') . rand(1000, 9999);
    $payload = [
        'requestTimestamp' => date('Y-m-d H:i:s'),
        'mid' => $account['mid'],
        'tid' => $account['tid'],
        'merOrderId' => formatOrderId($orderId, $account),
        'refundOrderId' => formatOrderId($refundOrderId, $account),
        'refundAmount' => bcmul($refundAmount, '100', 0),
        'totalAmount' => bcmul($refundAmount, '100', 0),
        'orderDesc' => '测试分账退款',
        'platformAmount' => 0,
        'subOrders' => $subOrders,
    ];

    echo "原订单号: {$orderId}\n";
    echo "退款订单号: {$refundOrderId}\n\n";

    $response = executeUmsCall('发起分账退款', $account, '/v1/netpay/refund', $payload);
    displayResultTips($response);
}

function runRefundQuery(array $account, string $refundOrderId): void
{
    $payload = [
        'requestTimestamp' => date('Y-m-d H:i:s'),
        'mid' => $account['mid'],
        'tid' => $account['tid'],
        'refundOrderId' => formatOrderId($refundOrderId, $account),
    ];

    executeUmsCall('退款查询', $account, '/v1/netpay/refund-query', $payload);
}

function runCloseOrder(array $account, string $orderId): void
{
    $payload = [
        'requestTimestamp' => date('Y-m-d H:i:s'),
        'mid' => $account['mid'],
        'tid' => $account['tid'],
        'merOrderId' => formatOrderId($orderId, $account),
    ];

    executeUmsCall('关闭订单', $account, '/v1/netpay/close', $payload);
}

function runTestNotify(array $account): void
{
    echo "========================================\n";
    echo "测试回调验签\n";
    echo "========================================\n";

    // 检查是否配置了通讯密钥
    if (empty($account['notify_key'])) {
        echo "❌ 未配置通讯密钥 notify_key\n";
        echo "请在 config/UmsPayConfig.json 中配置 notify_key 字段\n";
        return;
    }

    // 使用真实的银联回调数据作为模板
    // 这是从银联实际返回的回调数据
    $mockNotifyData = [
        'msgType' => 'wx.notify',
        'payTime' => date('Y-m-d H:i:s'),
        'buyerCashPayAmt' => '10',
        'connectSys' => 'UNIONPAY',
        'merName' => '香溢乐享优选',
        'mid' => $account['mid'],
        'tid' => $account['tid'],
        'invoiceAmount' => '10',
        'settleDate' => date('Y-m-d'),
        'billFunds' => '现金:10',
        'buyerId' => 'otdJ_uNR6GRFVnlDOVtnk9nZF5yg',
        'mchntUuid' => '92041d5a554c4ea09ff03b9204db78fb',
        'DQ' => 'LLnI',  // 银联会随机生成这个字段
        'instMid' => 'MINIDEFAULT',
        'receiptAmount' => '10',
        'couponAmount' => '0',
        'cardAttr' => 'BALANCE',
        'targetOrderId' => '4200003009202512132758763781',
        'signType' => 'SHA256',
        'billFundsDesc' => '现金支付0.10元。',
        'subBuyerId' => 'ofxai7SpEkwo7L9Ugo0JTEterfZA',
        'orderDesc' => '支付测试商品',
        'seqId' => '55522683958N',
        'merOrderId' => '3HD3wx' . time() . rand(100000, 999999),
        'targetSys' => 'WXPay',
        'bankInfo' => 'OTHERS',
        'totalAmount' => '10',
        'createTime' => date('Y-m-d H:i:s', time() - 60),
        'buyerPayAmount' => '10',
        'notifyId' => '929caf4e-42db-4ed7-8507-13b0521cb380',
        'subInst' => '104200',
        'status' => 'TRADE_SUCCESS',
    ];

//     $mockNotifyData = [
// 'msgType' => 'wx.notify',
// 'payTime' => '2025-12-13 23:55:17',
// 'buyerCashPayAmt' => '10',
// 'connectSys' => 'UNIONPAY',
// // 'sign' => '8D49DF76607F456BF7ACCF3FFC6F5B446E8440E6FE653D095A65359D38E6E29D',
// 'merName' => '香溢乐享优选',
// 'mid' => '898310100010854',
// 'invoiceAmount' => '10',
// 'settleDate' => '2025-12-13',
// 'billFunds' => '现金:10',
// 'buyerId' => 'otdJ_uNR6GRFVnlDOVtnk9nZF5yg',
// 'mchntUuid' => '92041d5a554c4ea09ff03b9204db78fb',
// 'DQ' => 'LLnI', // 银联会随机生成这个字段
// 'tid' => '41AUZ7C6',
// 'instMid' => 'MINIDEFAULT',
// 'receiptAmount' => '10',
// 'couponAmount' => '0',
// 'cardAttr' => 'BALANCE',
// 'targetOrderId' => '4200003009202512132758763781',
// 'signType' => 'SHA256',
// 'billFundsDesc' => '现金支付0.10元。',
// 'subBuyerId' => 'ofxai7SpEkwo7L9Ugo0JTEterfZA',
// 'orderDesc' => '支付测试商品',
// 'seqId' => '55522683958N',
// 'merOrderId' => '3HD3wx731297238646521856',
// 'targetSys' => 'WXPay',
// 'bankInfo' => 'OTHERS',
// 'totalAmount' => '10',
// 'createTime' => '2025-12-13 23:54:12',
// 'buyerPayAmount' => '10',
// 'notifyId' => '929caf4e-42db-4ed7-8507-13b0521cb380',
// 'subInst' => '104200',
// 'status' => 'TRADE_SUCCESS',
// ];

    echo "模拟回调数据:\n";
    echo json_encode($mockNotifyData, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n\n";

    // 计算签名
    $signData = $mockNotifyData;
    ksort($signData, SORT_STRING);

    $query = [];
    foreach ($signData as $k => $v) {
        $query[] = $k . '=' . $v;
    }
    $stringToSign = implode('&', $query) . $account['notify_key'];


    echo "待签名字符串:\n{$stringToSign}\n\n";

    $signType = $mockNotifyData['signType'];
    if ($signType === 'MD5') {
        $sign = strtoupper(md5($stringToSign));
    } else {
        $sign = strtoupper(hash('sha256', $stringToSign));
    }

    echo "签名类型: {$signType}\n";
    echo "计算签名: {$sign}\n\n";

    // 添加签名到数据中
    $mockNotifyData['sign'] = $sign;

    echo "完整回调数据(含签名):\n";
    echo json_encode($mockNotifyData, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n\n";

    // 验证签名
    echo "========================================\n";
    echo "验证签名\n";
    echo "========================================\n";

    $receivedSign = strtoupper($mockNotifyData['sign']);
    $verifyData = $mockNotifyData;
    unset($verifyData['sign']);

    ksort($verifyData, SORT_STRING);
    $verifyQuery = [];
    foreach ($verifyData as $k => $v) {
        $verifyQuery[] = $k . '=' . $v;
    }
    $verifyString = implode('&', $verifyQuery) . $account['notify_key'];

    if ($signType === 'MD5') {
        $calculatedSign = strtoupper(md5($verifyString));
    } else {
        $calculatedSign = strtoupper(hash('sha256', $verifyString));
    }

    echo "接收签名: {$receivedSign}\n";
    echo "计算签名: {$calculatedSign}\n";

    if (hash_equals($calculatedSign, $receivedSign)) {
        echo "✅ 签名验证成功\n\n";
    } else {
        echo "❌ 签名验证失败\n\n";
    }

    echo "========================================\n";
    echo "测试说明\n";
    echo "========================================\n";
    echo "1. 此测试模拟银联回调数据并验证签名\n";
    echo "2. 实际回调数据由银联服务器发送\n";
    echo "3. 验签成功说明 notify_key 配置正确\n";
    echo "4. 验签失败请检查 notify_key 是否与银联商户后台一致\n\n";
}

function runAll(array $account, array $opts): void
{
    runMiniPay($account, $opts);
    runH5Pay($account, $opts);

    $recentOrder = trim(@file_get_contents(__DIR__ . '/last_order_id.txt')) ?: ('wx' . (time() - 60) . '0000');
    runQuery($account, $recentOrder);
    runRefund($account, $recentOrder, $opts);

    $recentRefund = 'RF' . (time() - 30) . rand(1000, 9999);
    runRefundQuery($account, $recentRefund);
    runCloseOrder($account, $recentOrder);

    echo "\n";
    runTestNotify($account);
}

// ========== Utility Functions ==========

function loadAccountConfig(string $paymentType = 'mini'): array
{
    $file = __DIR__ . '/config/UmsPayConfig.json';
    if (!is_file($file)) {
        throw new RuntimeException("找不到配置文件: {$file}");
    }
    $config = json_decode(file_get_contents($file), true);
    if (!$config || empty($config['accounts'])) {
        throw new RuntimeException('配置文件格式错误');
    }

    $selected = getenv('UMS_ACCOUNT') ?: ($config['current_account'] ?? 'test');

    // 如果是H5支付且存在productionH5配置,则使用productionH5
    if ($paymentType === 'h5' && isset($config['accounts']['productionH5'])) {
        $selected = 'productionH5';
        echo "✅ H5支付使用专用配置: productionH5\n";
    }

    if (!isset($config['accounts'][$selected])) {
        throw new RuntimeException("未找到账号配置: {$selected}");
    }

    $account = $config['accounts'][$selected];
    $account['name'] = $selected;
    $account['api_url'] = rtrim($account['api_url'] ?? '', '/');
    $account['is_production'] = (strpos($selected, 'production') !== false);

    foreach (['app_id', 'app_key', 'mid', 'tid', 'api_url'] as $field) {
        if (empty($account[$field])) {
            throw new RuntimeException("配置项 {$field} 不能为空 ({$selected})");
        }
    }

    // notify_key 是可选的,仅在测试回调时需要
    $account['notify_key'] = $account['notify_key'] ?? '';

    return $account;
}

function loadTestOptions(): array
{
    return [
        'amount' => getenv('UMS_TEST_AMOUNT') ?: '0.1',
        'openid' => getenv('UMS_TEST_OPENID') ?: 'ofxai7SpEkwo7L9Ugo0JTEterfZA',
        'sub_app_id' => getenv('UMS_TEST_SUB_APPID') ?: 'wxb5fc16b55f439205',
        'notify_url' => getenv('UMS_TEST_NOTIFY_URL') ?: 'http://localhost:20199/api/pay/ums/notify',
        'return_url' => getenv('UMS_TEST_RETURN_URL') ?: 'http://localhost:20199/pages/order/list',
    ];
}

function executeUmsCall(string $title, array $account, string $endpoint, array $payload): array
{
    echo "========================================\n";
    echo "{$title}\n";
    echo "========================================\n";

    $url = $account['api_url'] . $endpoint;
    $body = json_encode($payload, JSON_UNESCAPED_UNICODE);
    $auth = buildAuthorization($account['app_id'], $account['app_key'], $body);

    echo "请求URL: {$url}\n";
    echo "Authorization: {$auth['header']}\n";
    echo "请求参数:\n" . json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n\n";

    $headers = [
        'Authorization: ' . $auth['header'],
        'Content-Type: application/json',
    ];

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    echo "HTTP状态码: {$httpCode}\n";
    if (!empty($error)) {
        throw new RuntimeException("CURL错误: {$error}");
    }

    echo "原始响应:\n{$response}\n\n";

    $decoded = json_decode($response, true);
    if (!$decoded) {
        throw new RuntimeException('响应解析失败');
    }

    echo "解析后的响应:\n" . json_encode($decoded, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n\n";

    return $decoded;
}

function executeUmsH5Call(string $title, array $account, string $endpoint, array $payload): array
{
    echo "========================================\n";
    echo "{$title}\n";
    echo "========================================\n";

    $url = $account['api_url'] . $endpoint;

    // 注意:JSON不使用UNESCAPED_UNICODE,保持标准JSON格式
    $content = json_encode($payload);

    // H5支付使用URL参数方式(OPEN-FORM-PARAM)
    $timestamp = date('YmdHis');
    $nonce = bin2hex(random_bytes(16));

    // 签名计算:使用原始content(未URL编码)
    $contentHash = hash('sha256', $content);
    $signStr = $account['app_id'] . $timestamp . $nonce . $contentHash;
    $signature = base64_encode(hash_hmac('sha256', $signStr, $account['app_key'], true));

    // 构造URL参数(http_build_query会自动进行URL编码)
    $urlParams = [
        'authorization' => 'OPEN-FORM-PARAM',
        'appId' => $account['app_id'],
        'timestamp' => $timestamp,
        'nonce' => $nonce,
        'content' => $content,  // http_build_query会自动URL编码
        'signature' => $signature,
    ];

    // 使用GET方式,参数放在URL中
    $fullUrl = $url . '?' . http_build_query($urlParams);

    echo "请求URL: {$url}\n";
    echo "认证方式: OPEN-FORM-PARAM\n";
    echo "AppId: {$account['app_id']}\n";
    echo "Timestamp: {$timestamp}\n";
    echo "Nonce: {$nonce}\n";
    echo "Content(原始): {$content}\n";
    echo "Content Hash: {$contentHash}\n";
    echo "签名原串: {$signStr}\n";
    echo "Signature: {$signature}\n\n";

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

    echo "HTTP状态码: {$httpCode}\n";
    if (!empty($error)) {
        throw new RuntimeException("CURL错误: {$error}");
    }

    // 分离响应头和响应体
    $header = substr($response, 0, $headerSize);
    $body = substr($response, $headerSize);

    echo "响应头:\n{$header}\n";
    echo "响应体:\n{$body}\n\n";

    // 如果是302重定向,提取Location
    if ($httpCode == 302 || $httpCode == 301) {
        if (preg_match('/Location:\s*(.+)/i', $header, $matches)) {
            $payUrl = trim($matches[1]);
            echo "支付URL: {$payUrl}\n\n";
            return [
                'errCode' => 'SUCCESS',
                'payUrl' => $payUrl,
            ];
        }
    }

    // 尝试解析JSON响应
    $decoded = json_decode($body, true);
    if (!$decoded) {
        throw new RuntimeException('响应解析失败');
    }

    echo "解析后的响应:\n" . json_encode($decoded, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n\n";

    return $decoded;
}

function buildAuthorization(string $appId, string $appKey, string $body): array
{
    $timestamp = date('YmdHis');
    $nonce = bin2hex(random_bytes(16));
    $bodyHash = hash('sha256', $body);
    $signStr = $appId . $timestamp . $nonce . $bodyHash;
    $signature = base64_encode(hash_hmac('sha256', $signStr, $appKey, true));
    $header = "OPEN-BODY-SIG AppId=\"{$appId}\",Timestamp=\"{$timestamp}\",Nonce=\"{$nonce}\",Signature=\"{$signature}\"";

    return [
        'header' => $header,
        'timestamp' => $timestamp,
        'nonce' => $nonce,
        'signature' => $signature,
    ];
}

function formatOrderId(string $orderId, array $account): string
{
    if (!empty($account['is_production']) && strpos($orderId, '3HD3') !== 0) {
        return '3HD3' . substr($orderId, 0, 24);
    }
    return $orderId;
}

function amountToFen(string $amount): string
{
    if (function_exists('bcmul')) {
        return bcmul($amount, '100', 0);
    }
    return (string) (int) round(floatval($amount) * 100);
}

function persistLastOrderId(string $orderId): void
{
    @file_put_contents(__DIR__ . '/last_order_id.txt', $orderId);
}

function requireParam(?string $value, string $label, string $usage): void
{
    if (!empty($value)) {
        return;
    }
    echo "❌ 请输入{$label}\n";
    echo "用法: {$usage}\n";
    exit(1);
}

function displayResultTips(array $response): void
{
    if (!isset($response['errCode'])) {
        echo "⚠️ 响应中缺少 errCode 字段\n";
        return;
    }

    if ($response['errCode'] === 'SUCCESS') {
        echo "✅ 接口调用成功\n\n";
    } else {
        $msg = $response['errMsg'] ?? $response['errInfo'] ?? '未知错误';
        echo "❌ 接口返回错误: {$response['errCode']} - {$msg}\n\n";
    }
}

function showHelp(): void
{
    echo "用法:\n";
    echo "  php test_ums.php mini                        # 测试小程序下单\n";
    echo "  php test_ums.php h5                          # 测试H5下单\n";
    echo "  php test_ums.php query <订单号>               # 测试订单查询\n";
    echo "  php test_ums.php refund <订单号>              # 测试普通退款\n";
    echo "  php test_ums.php refund-division <订单号>     # 测试分账退款\n";
    echo "  php test_ums.php refund-query <退款单号>      # 测试退款查询\n";
    echo "  php test_ums.php close <订单号>               # 测试订单关闭\n";
    echo "  php test_ums.php test-notify                 # 测试回调验签\n";
    echo "  php test_ums.php all                         # 依次执行全部测试\n";
    echo "环境变量:\n";
    echo "  UMS_ACCOUNT             切换使用的账号（test / production）\n";
    echo "  UMS_TEST_AMOUNT         测试金额（元，默认0.01）\n";
    echo "  UMS_TEST_OPENID         用户OpenId\n";
    echo "  UMS_TEST_SUB_APPID      小程序AppId\n";
    echo "  UMS_TEST_NOTIFY_URL     异步通知地址\n";
    echo "  UMS_TEST_RETURN_URL     同步跳转地址（H5）\n";
}
