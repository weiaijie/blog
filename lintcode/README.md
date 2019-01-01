## lintcode刷题

1.反转一个只有3位数的整数。
``` javaScript
return parseInt(number.toString().split("").reverse().join(""))
```
2.将一个字符由小写字母转换为大写字母
``` javaScript
return String.fromCharCode(parseInt(character.charCodeAt()) - 32)
```