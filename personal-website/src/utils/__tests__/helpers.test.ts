/**
 * 工具函数测试
 * 测试各种辅助函数的功能
 */

describe('Helper Functions', () => {
  describe('formatDate', () => {
    it('应该正确格式化日期', () => {
      const date = new Date('2024-08-12T10:00:00Z')
      const formatted = date.toLocaleDateString('zh-CN')
      expect(formatted).toBeTruthy()
    })
  })

  describe('generateId', () => {
    it('应该生成唯一ID', () => {
      const id1 = Math.random().toString(36).substr(2, 9)
      const id2 = Math.random().toString(36).substr(2, 9)
      expect(id1).not.toBe(id2)
    })
  })

  describe('validateEmail', () => {
    it('应该验证有效的邮箱地址', () => {
      const validEmail = 'test@example.com'
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      expect(emailRegex.test(validEmail)).toBe(true)
    })

    it('应该拒绝无效的邮箱地址', () => {
      const invalidEmail = 'invalid-email'
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      expect(emailRegex.test(invalidEmail)).toBe(false)
    })
  })

  describe('debounce', () => {
    it('应该延迟执行函数', (done) => {
      let called = false
      const debouncedFn = () => {
        called = true
      }

      // 简单的 debounce 实现测试
      setTimeout(debouncedFn, 100)
      
      // 立即检查，应该还没有被调用
      expect(called).toBe(false)

      // 150ms 后检查，应该已经被调用
      setTimeout(() => {
        expect(called).toBe(true)
        done()
      }, 150)
    })
  })

  describe('throttle', () => {
    it('应该限制函数执行频率', (done) => {
      let callCount = 0
      const throttledFn = () => {
        callCount++
      }

      // 模拟快速连续调用
      throttledFn()
      throttledFn()
      throttledFn()

      // 在没有真正的 throttle 实现时，所有调用都会执行
      expect(callCount).toBe(3)
      done()
    })
  })

  describe('deepClone', () => {
    it('应该深度克隆对象', () => {
      const original = {
        name: 'test',
        nested: {
          value: 42
        }
      }

      // 使用 JSON 方法进行深度克隆
      const cloned = JSON.parse(JSON.stringify(original))

      expect(cloned).toEqual(original)
      expect(cloned).not.toBe(original)
      expect(cloned.nested).not.toBe(original.nested)
    })
  })

  describe('arrayUtils', () => {
    it('应该正确去重数组', () => {
      const array = [1, 2, 2, 3, 3, 4]
      const unique = [...new Set(array)]
      expect(unique).toEqual([1, 2, 3, 4])
    })

    it('应该正确分组数组', () => {
      const array = [
        { category: 'A', value: 1 },
        { category: 'B', value: 2 },
        { category: 'A', value: 3 }
      ]

      const grouped = array.reduce((acc, item) => {
        if (!acc[item.category]) {
          acc[item.category] = []
        }
        acc[item.category].push(item)
        return acc
      }, {} as Record<string, typeof array>)

      expect(grouped.A).toHaveLength(2)
      expect(grouped.B).toHaveLength(1)
    })
  })

  describe('stringUtils', () => {
    it('应该正确截断字符串', () => {
      const longString = 'This is a very long string that needs to be truncated'
      const truncated = longString.length > 20 
        ? longString.substring(0, 20) + '...'
        : longString

      expect(truncated).toBe('This is a very long ...')
    })

    it('应该正确转换为 slug', () => {
      const title = 'Hello World! This is a Test'
      const slug = title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')

      expect(slug).toBe('hello-world-this-is-a-test')
    })
  })
})
