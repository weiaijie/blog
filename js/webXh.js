// 重复字符串
String.prototype.repeat = function(n) {
  return new Array(n+1).join(this);
}
  
// 替换全部
String.prototype.replaceAll = function(str1, str2) {
  return this.replace(new RegExp(str1, "gm"), str2);
}
  
// 清除空格
String.prototype.trim = function() {
  return this.replace(/^\s*(.*?)\s+$/, "$1");
}
  
// 计算数组中的最大值
Array.prototype.max = function() {
  return Math.max.apply({}, this);
}
  
// 计算数组中的最小值
Array.prototype.min = function() {
  return Math.min.apply({}, this);
}
  
// 复制数组
Array.prototype.copy = function() {
  return [].concat(this);
};
  
// 去除数组中指定元素，只能去除一个，如果想多个，之前先用unique处理
Array.prototype.remove = function(value){
  for (var i = 0, len = this.length; i < len; i++) {
    if (this[i] == value) {
      this.splice(i, 1);
      break;
    }
  }
  return this;
}
  
// 判断数组中是否存在指定元素，返回索引值
Array.prototype.inArray = function(value) {
  var index = -1, key;
  for (key in this) {
    if (this[key] == value) {
      index = key;
      break;
    }
  }
  return index;
}
  
// 去除数组中的重复元素
Array.prototype.unique = function() {
  var key, ret = [];
  for (key in this) {
    if (ret.inArray(this[key]) < 0) {
      ret.push(this[key]);
    }
  }
  return ret;
}
  
// 检测是否已经安装flash，检测flash的版本
var flashVersion = (function() {
  var version;
  try {
    version = navigator.plugins['Shockwave Flash'];
    version = version.description;
  } catch (ex) {
    try {
      version = new ActiveXObject('ShockwaveFlash.ShockwaveFlash')
        .GetVariable('$version');
    } catch (ex2) {
      version = '0.0';
    }
  }
  version = version.match(/\d+/g);
  return parseFloat(version[0] + '.' + version[1], 10);
})();
  
// 检测是否支持transition
var supportTransition = (function() {
  var s = document.createElement('p').style,
    r = 'transition' in s ||
    'WebkitTransition' in s ||
    'MozTransition' in s ||
    'msTransition' in s ||
    'OTransition' in s;
  s = null;
  return r;
})();
  
// 判断浏览器是否支持图片的base64
var isSupportBase64 = (function() {
  var data = new Image();
  var support = true;
  data.onload = data.onerror = function() {
    if (this.width != 1 || this.height != 1) {
      support = false;
    }
    return support;
  };
  data.src = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";
})();
  
// 首字母大写
function ucfirst(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
  
// 清除左空格
function ltrim(str) {
  return str.replace(/^(\s*|　*)/, "");
}
  
// 清除右空格
function rtrim(str) {
  return str.replace(/(\s*|　*)$/, "");
}
  
// 设置Cookie值
function setCookie(name, value, hours, path, domain) {
  var d = new Date();
  var offset = 8;
  var utc = d.getTime() + (d.getTimezoneOffset() * 60000);
  var nd = utc + (3600000 * offset);
  var expire = new Date(nd);
  expire.setTime(expire.getTime() + hours * 60 * 60 * 1000);
  var path = path || "";
  var domain = domain || "";
  document.cookie = name + "=" + escape(value) + ";path="+ path +";expires=" + expire.toGMTString() + ";domain="+ domain +";"
}
  
// 获取Cookie值
function getCookie(name) {
  var arr = document.cookie.match(new RegExp("(^| )" + name + "=([^;]*)(;|$)"));
  if (arr != null) {
    return unescape(arr[2]);
  }
  return null;
}
  
// 删除Cookie值
function removeCookie(name) {
  setCookie(name, "", -1);
}
  
// 生成范围随机数
function rand(n, m) {
  return Math.random() * (m - n) + n;
}
  
// 加入收藏夹
function addFavorite(url, title) {
  try {
    window.external.addFavorite(url, title);
  } catch(e) {
    try {
      window.sidebar.addPanel(title, url, "");
    } catch(e) {
      alert("加入收藏失败，请使用Ctrl+D进行添加");
    }
  }
}
  
// 设为首页
function setHomepage(url) {
  if (document.all) {
    document.body.style.behavior = 'url(#default#homepage)';
    document.body.setHomePage(url);
  } else if (window.sidebar) {
    if (window.netscape) {
      try {
        netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
      } catch(e) {
        alert("该操作被浏览器拒绝，如果想启用该功能，请在地址栏内输入 about:config,然后将项 signed.applets.codebase_principal_support 值该为true");
      }
    }
    var prefs = Components.classes['@mozilla.org/preferences-service;1'].getService(Components.interfaces.nsIPrefBranch);
    prefs.setCharPref('browser.startup.homepage', url);
  }
}
  
// 加载样式文件
function loadStyle(url) {
  try {
    document.createStyleSheet(url);
  } catch(e) {
    var cssLink = document.createElement('link');
    cssLink.rel = 'stylesheet';
    cssLink.type = 'text/css';
    cssLink.href = url;
    var head = document.getElementsByTagName('head')[0];
    head.appendChild(cssLink)
  }
}
  
// 清除脚本内容
function stripscript(str) {
  return str.replace(/<script.*?>.*?<\/script>/ig, '');
}
  
// 检验URL链接是否有效
function getUrlState(url) {
  var xmlhttp = new ActiveXObject("microsoft.xmlhttp");
  xmlhttp.open("GET", url, false);
  try {
    xmlhttp.send();
  } catch(e) {
      
  } finally {
    var result = xmlhttp.responseText;
    if (result) {
      if (xmlhttp.status == 200) {
        return true;
      } else {
        return false;
      }
    } else {
      return false;
    }
  }
}
  
// 格式化CSS代码
function formatCss(str){
  str = str.replace(/\s*([\{\}\:\;\,])\s*/g, "$1");
  str = str.replace(/;\s*;/g, ";"); //清除连续分号
  str = str.replace(/\,[\s\.\#\d]*{/g, "{");
  str = str.replace(/([^\s])\{([^\s])/g, "$1 {\n\t$2");
  str = str.replace(/([^\s])\}([^\n]*)/g, "$1\n}\n$2");
  str = str.replace(/([^\s]);([^\s\}])/g, "$1;\n\t$2");
  return str;
}
  
// 压缩CSS代码
function compressCss (str) {
  str = str.replace(/\/\*(.|\n)*?\*\//g, "");    //删除注释
  str = str.replace(/\s*([\{\}\:\;\,])\s*/g, "$1");
  str = str.replace(/\,[\s\.\#\d]*\{/g, "{");    //容错处理
  str = str.replace(/;\s*;/g, ";");         //清除连续分号
  str = str.match(/^\s*(\S+(\s+\S+)*)\s*$/);    //去掉首尾空白
  return (str == null) ? "" : s[1];
}
  
// getElementsByClassName
function getElementsByClassName(name, context) {
  var context = context || document;
  if (context.getElementsByClassName) {
    return context.getElementsByClassName(name);
  }
    
  var nodes = context.getElementsByTagName("*"), nodesLength = nodes.length, ret = [];
  for (var i = 0; i < nodesLength; i++) {
    var className = nodes[i].className;
    if (nodes[i].nodeType == 1 && className) {
      var classes = className.split(' ');
      for (var j = 0; j < classes.length; j++) {
        if (name == classes[j]) {
          ret.push(nodes[i]);
          break
        }
      }
    }
  }
  return ret;
}
  
// 获取页面高度
function getPageHeight() {
  var doc = document;
  var rot = doc.compatMode == "BackCompat" ? doc.body : doc.documentElement;
  return Math.max(doc.documentElement.scrollHeight, doc.body.scrollHeight, rot.clientHeight);
}
  
// 获取页面scrollLeft
function getPageScrollLeft() {
  var doc = document;
  return doc.documentElement.scrollLeft || doc.body.scrollLeft;
}
  
// 获取页面可视宽度
function getPageViewWidth() {
  var doc = document;
  var rot = doc.compatMode == "BackCompat" ? doc.body : doc.documentElement;
  return rot.clientWidth;
}
  
// 获取页面宽度
function getPageWidth(){
  var doc = document;
  var rot = doc.compatMode == "BackCompat" ? doc.body : doc.documentElement;
  return Math.max(doc.documentElement.scrollWidth, doc.body.scrollWidth, rot.clientWidth);
}
  
// 获取页面scrollTop
function getPageScrollTop(){
  var doc = document;
  return doc.documentElement.scrollTop || doc.body.scrollTop;
}
  
// 获取页面可视高度
function getPageViewHeight() {
  var doc = document;
  var rot = doc.compatMode == "BackCompat" ? doc.body : doc.documentElement;
  return rot.clientHeight;
}
  
// 获取网页被卷去的位置
function getScrollXY() {
  return document.body.scrollTop ? {
    x : document.body.scrollLeft,
    y : document.body.scrollTop
  } : {
    x : document.documentElement.scrollLeft,
    y : document.documentElement.scrollTop
  }
}
// 获取元素的样式值
function getStyle(elem, name) {
  if (elem.style[name]) {
    return elem.style[name];
  } else if (elem.currentStyle) {
    return elem.currentStyle[name];
  } else if (document.defaultView && document.defaultView.getComputedStyle) {
    var s = document.defaultView.getComputedStyle(elem, "");
    return s && s.getPropertyValue(name);
  } else {
    return null;
  }
}
  
// 获取元素相对于这个页面的X坐标
function pageX(elem) {
  return elem.offsetParent ? (elem.offsetLeft + pageX(elem.offsetParent)) : elem.offsetLeft;
}
  
// 获取元素相对于这个页面的Y坐标
function pageY(elem) {
  return elem.offsetParent ? (elem.offsetTop + pageY(elem.offsetParent)) : elem.offsetTop;
}
  
// 获取元素相对于父元素的X坐标
function parentX(elem) {
  return elem.parentNode == elem.offsetParent ? elem.offsetLeft : pageX(elem) - pageX(elem.parentNode);
}
  
// 获取元素相对于父元素的Y坐标
function parentY(elem) {
  return elem.parentNode == elem.offsetParent ? elem.offsetTop : pageY(elem)-pageY(elem.parentNode);
}
  
// 获取使用CSS定位的元素的X坐标
function posX(elem) {
  return parseInt(getStyle(elem, "left"));
}
  
// 获取使用CSS定位的元素的Y坐标
function posY(elem) {
  return parseInt(getStyle(elem, "top"));
}
  
// 设置元素X位置
function setX(elem, pos) {
  elem.style.left = pos + "px";
}
  
// 设置元素Y位置
function setY(elem, pos) {
  elem.style.top = pos + "px";
}
  
// 增加元素X坐标
function addX(elem, pos) {
  set(elem, (posX(elem) + pos));
}
  
// 增加元素Y坐标
function addY(elem, pos) {
  set(elem, (posY(elem) + pos));
}
  
// 获取元素使用CSS控制大小的高度
function getHeight(elem) {
  return parseInt(getStyle(elem, "height"));
}
  
// 获取元素使用CSS控制大小的宽度
function getWidth(elem) {
  return parseInt(getStyle(elem, "width"));
}
  
// 设置透明度
function setOpacity(elem, num) {
  if (elem.filters) {
    elem.style.filter="alpha(opacity="+ num +")";
  } else {
    elem.style.opacity = num/100;
  }
}
  
// 获取鼠标光标相对于整个页面的X位置
function getX(e) {
  e = e || window.event;
  return e.pageX || e.clientX + document.body.scrollLeft;
}
  
// 获取鼠标光标相对于整个页面的Y位置
function getY(e) {
  e = e || window.event;
  return e.pageY || e.clientY + document.body.scrollTop;
}
  
// 获取鼠标光标相对于当前元素的X位置
function getElementX(e) {
  return (e && e.layerX) || window.event.offsetX;
}
  
// 获取鼠标光标相对于当前元素的Y位置
function getElementY(e) {
  return (e && e.layerY) || window.event.offsetY;
}
  
// 获取滚动条的X位置
function scrollX() {
  var de = document.documentElement;
  return self.pageXOffset || (de && de.scrollLeft) || document.body.scrollLeft;
}
  
// 获取滚动条的Y位置
function scrollY() {
  var de = document.documentElement;
  return self.pageYOffset || (de && de.scrollTop) || document.body.scrollTop;
}
  
// 确认是否键盘有效输入值
function checkKey(iKey) {
  if (iKey == 32 || iKey == 229) {return true;} /*空格和异常*/
  if (iKey>47 && iKey < 58)   {return true;} /*数字*/
  if (iKey>64 && iKey < 91)   {return true;} /*字母*/
  if (iKey>95 && iKey < 108)  {return true;} /*数字键盘1*/
  if (iKey>108 && iKey < 112)  {return true;} /*数字键盘2*/
  if (iKey>185 && iKey < 193)  {return true;} /*符号1*/
  if (iKey>218 && iKey < 223)  {return true;} /*符号2*/
  return false;
}
  
// 获得URL中GET参数值
function getParams() {
  var queryStr = window.location.href.split("?");
  var params = [];
  if (queryStr[1]) {
    var gets = queryStr[1].split("&");
    for (var i = 0; i < gets.length; i++) {
      temp = gets.split("=");
      params[temp[0]] = temp[1];
    }
  }
  return params;
}
  
// 字符串反序
function strReverse(text) {
  return text.split('').reverse().join('');
}
  
// HTML实体
function htmlEncode(str) {
  var s = "";
  if (str.length == 0) return "";
  s = str.replace(/\&/g, "&");
  s = s.replace(/</g, "<");
  s = s.replace(/>/g, ">");
  s = s.replace(/\'/g, "'");
  s = s.replace(/\"/g, "&qout;");
  return s;
}
  
// HTML还原
function htmlDecode(str) {
  var s = "";
  if (str.length == 0) return "";
  s = str.replace(/&/g, "&");
  s = s.replace(/</g, "<");
  s = s.replace(/>/g, ">");
  s = s.replace(/'/g, "\'");
  s = s.replace(/&qout;/g, "\"");
  return s;
}
  
// 克隆
function clone(obj) {
  var ret;
  switch (typeof obj) {
    case 'undefined':
      break;
    case 'string':
      ret = obj + '';
      break;
    case 'number':
      ret = obj - 0;
      break;
    case 'boolean':
      ret = obj;
      break;
    case 'object':
      if (obj === null) {
        ret = null;
      } else {
        if (obj instanceof Array) {
          ret = [];
          for (var i = 0, len = obj.length; i < len; i++) {
            ret.push(clone(obj[i]));
          }
        } else {
          ret = {};
          for (var k in obj) {
            ret[k] = clone(obj[k]);
          }
        }
      }
      break;
    default:
      ret = obj;
      break;
  }
  return ret;
}
  
// 检测变量是否为email格式
function isEmail(mail) {
  if (/^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$/.test(mail)) {
    return true;
  }
  return false;
}
  
// 验证身份证号码
function isIdenCode(code){
  var city={11:"北京",12:"天津",13:"河北",14:"山西",15:"内蒙古",21:"辽宁",22:"吉林",23:"黑龙江 ",31:"上海",32:"江苏",33:"浙江",34:"安徽",35:"福建",36:"江西",37:"山东",41:"河南",42:"湖北 ",43:"湖南",44:"广东",45:"广西",46:"海南",50:"重庆",51:"四川",52:"贵州",53:"云南",54:"西藏 ",61:"陕西",62:"甘肃",63:"青海",64:"宁夏",65:"新疆",71:"台湾",81:"香港",82:"澳门",91:"国外"};
  var tip = "";
  var pass = true;
  if (!code || !/^\d{6}(18|19|20)?\d{2}(0[1-9]|1[012])(0[1-9]|[12]\d|3[01])\d{3}(\d|X)$/i.test(code)) {
    tip = "身份证号格式错误";
    pass = false;
  } else if (!city[code.substr(0,2)]) {
    tip = "地址编码错误";
    pass = false;
  } else {
    //18位身份证需要验证最后一位校验位
    if(code.length == 18){
      code = code.split('');
      //∑(ai×Wi)(mod 11)
      //加权因子
      var factor = [ 7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2 ];
      //校验位
      var parity = [ 1, 0, 'X', 9, 8, 7, 6, 5, 4, 3, 2 ];
      var sum = 0;
      var ai = 0;
      var wi = 0;
      for (var i = 0; i < 17; i++) {
        ai = code[i];
        wi = factor[i];
        sum += ai * wi;
      }
        
      var last = parity[sum % 11];
      if (parity[sum % 11] != code[17]) {
        tip = "校验位错误";
        pass = false;
      }
    }
  }
  return pass;
}
  
// 检测变量是否为小数
function isDecimal(dec){
  if (dec.match(/^-?\d+(\.\d+)?$/g) == null) {
    return false;
  }
  return true;
}
  
// 检测变量是否为整型
function isInteger(num){
  if (num.match(/^[-+]?\d*$/) == null) {
    return false;
  }
  return true;
}
  
// 检测变量是否为时间格式
function checkTime(str) {
  var time = str.match(/^(\d{1,2})(:)?(\d{1,2})\2(\d{1,2})$/);
  if (time == null) {
    return false;
  }
    
  if (time[1] > 24 || time[3] > 60 || time[4] > 60) {
    return false
  }
  return true;
}
  
// 检测变量类型是否为日期格式
function checkDate(str) {
  var date = str.match(/^(\d{1,4})(-|\/)(\d{1,2})\2(\d{1,2})$/);
  if (date == null) {
    return false;
  }
    
  var d = new Date(r[1], r[3]-1, r[4]);
  return (d.getFullYear() == r[1] && (d.getMonth()+1) == r[3] && d.getDate() == r[4]);
}
  
// 检测变量是否为长日期格式
function checkDateTime(str) {
  var reg = /^(\d{1,4})(-|\/)(\d{1,2})\2(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2})$/;
  var dt = str.match(reg);
  if (dt == null) {
    return false;
  }
    
  var d = new Date(dt[1], dt[3]-1, dt[4], dt[5], dt[6], dt[7]);
  return (d.getFullYear() == dt[1] && (d.getMonth()+1) == dt[3] && d.getDate() == dt[4] && d.getHours() == dt[5] && d.getMinutes() == dt[6] && d.getSeconds() == dt[7]);
}
  
// 检测变量是否为未定义
function isUndefined(val) {
  return typeof val === 'undefined';
}
  
// 检测变量是否为定义
function isDefined(val) {
  return typeof val !== 'undefined';
}
  
// 检测变量类型是否为对象
function isObject(val) {
 return val !== null && typeof val === 'object';
}
  
// 检测变量类型是否为空对象
function isBlankObject(val) {
 return val !== null && typeof val === 'object' && !Object.getPrototypeOf(val);
}
  
// 检测变量类型是否为字符串
function isString(val) {
  return typeof val === 'string';
}
  
// 检测变量类型是否为数字
function isNumber(val) {
  return typeof val === 'number';
}
  
// 检测变量类型是否为日期
function isDate(val) {
  return toString.call(val) === '[object Date]';
}
  
// 检测变量类型是否为函数
function isFunction(val) {
  return typeof val === 'function';
}
  
// 检测变量类型是否为正则表达式
function isRegExp(val) {
  return toString.call(val) === '[object RegExp]';
}
  
// 检测变量是否window窗体对象
function isWindow(obj) {
  return obj && obj.window === obj;
}
  
// 检测变量类型是否为布尔
function isBoolean(val) {
  return typeof val === 'boolean';
}
  
// 检测变量类型是否为文件对象
function isFile(obj) {
  return toString.call(obj) === '[object File]';
}
  
// 检测变量类型是否为表单对象
function isFormData(obj) {
  return toString.call(obj) === '[object FormData]';
}
  
// 检测变量类型是否为二进制对象
function isBlob(obj) {
  return toString.call(obj) === '[object Blob]';
}
  
// 转全角字符
function toDBC(str) {
  var result = "";
  var len = str.length;
  for (var i = 0; i < len; i++) {
    var code = str.charCodeAt(i);
    //全角与半角相差（除空格外）：65248(十进制)
    code = (code >= 0x0021 && code <= 0x007E) ? (code + 65248) : code;
    //处理空格
    code = (code == 0x0020) ? 0x03000 : code;
    result += String.fromCharCode(code);
  }
  return result;
}
  
// 转半角字符
function toSBC(str) {
  var result = "";
  var len = str.length;
  for (var i = 0; i < len; i++) {
    var code = str.charCodeAt(i);
    //全角与半角相差（除空格外）：65248（十进制）
    code = (code >= 0xFF01 && code <= 0xFF5E) ? (code - 65248) : code;
    //处理空格
    code = (code == 0x03000) ? 0x0020 : code;
    result += String.fromCharCode(code);
  }
  return result;
}
  
// 全角半角转换
// angle: 0全到半，1半到全，其他不转化
function chgAngle(str, angle) {
  if (typeof str != "string" || str.length <= 0 || !(angle === 0 || angle == 1)) {
    return str;
  }
    
  var i, len, ret = [], code;
  if (angle) {
    /*半->全*/
    for (i = 0, len = str.length; i < len; i++) {
      code = str.charCodeAt(i);
      if (code == 32) {
        code = 12288;
      } else if (code < 127) {
        code += 65248;
      }
      ret.push(String.fromCharCode(code));
    }
  } else {
    /*全->半*/
    for (i = 0, len = str.length; i < len; i++) {
      code = str.charCodeAt(i);
      if (code == 12288) {
        code = 32;
      } else if (code > 65280 && code < 65375) {
        code -= 65248;
      }
      ret.push(String.fromCharCode(code));
    }
  }
  return ret.join("");
}
  
// 数据的本地化存储
function makeWebStorage() {
  //IE用userdata实现，w3c浏览器本身支持
  if (("localStorage" in window)) {
    var store = {
      set  : function(key, value) {localStorage.setItem(key, value)},
      get  : function(key)    {return localStorage.getItem(key)},
      remove : function(key)    {return localStorage.removeItem(key)}
    }
  } else {
    var store = {
      userData : null,
      name   : location.hostname,
      init   : function () {
        if (!store.userData) {
          try {
            store.userData = document.createElement('INPUT');
            store.userData.type = "hidden";
            store.userData.style.display = "none";
            store.userData.addBehavior("#default#userData");
            document.body.appendChild(store.userData);
            var expires = new Date();
            expires.setDate(expires.getDate() + 365);
            store.userData.expires = expires.toUTCString();
          } catch (e) {
            return false;
          }
        }
        return true;
      },
      setItem : function(key, value) {
        if (store.init()) {
          store.userData.load(store.name);
          store.userData.setAttribute(key, value);
          store.userData.save(store.name);
        }
      },
      getItem : function(key) {
        if (store.init()) {
          store.userData.load(store.name);
          return store.userData.getAttribute(key);
        }
      },
      remove : function(key) {
        if (store.init()) {
          store.userData.load(store.name);
          store.userData.removeAttribute(key);
          store.userData.save(store.name);
        }
      }
    };
  }
  window.webStorage = store;
}
  
function makeSessionStorage() {
  if (("sessionStorage" in window)) {
    var store = {
      set  : function(key, value) {window.sessionStorage.setItem(key, value)},
      get  : function(key)    {return window.sessionStorage.getItem(key)},
      remove : function(key)    {return window.sessionStorage.removeItem(key)}
    }
  } else {
    var store = {
      set  : function(key, value) {},
      get  : function(key)    {},
      remove : function(key)    {}
    }
  }
  window.sessStorage = store;
}