/**
 * 工具函数测试
 */

import {
  validateEmail,
  validatePassword,
  validateUsername,
  validatePhone,
  formatDate,
  delay,
  generateRandomString,
  isEmpty,
  capitalize,
  truncateText,
} from '../../src/utils/helpers';

describe('Helper Functions', () => {
  describe('validateEmail', () => {
    it('should validate correct email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user.name@domain.co.uk')).toBe(true);
      expect(validateEmail('user+tag@example.org')).toBe(true);
    });

    it('should reject invalid email addresses', () => {
      expect(validateEmail('invalid-email')).toBe(false);
      expect(validateEmail('test@')).toBe(false);
      expect(validateEmail('@example.com')).toBe(false);
      expect(validateEmail('')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('should validate passwords with correct length', () => {
      expect(validatePassword('12345678')).toBe(true);
      expect(validatePassword('password123')).toBe(true);
    });

    it('should reject passwords that are too short', () => {
      expect(validatePassword('123')).toBe(false);
      expect(validatePassword('1234567')).toBe(false);
      expect(validatePassword('')).toBe(false);
    });
  });

  describe('validateUsername', () => {
    it('should validate usernames with correct length', () => {
      expect(validateUsername('user')).toBe(true);
      expect(validateUsername('username123')).toBe(true);
      expect(validateUsername('a'.repeat(20))).toBe(true);
    });

    it('should reject usernames with incorrect length', () => {
      expect(validateUsername('ab')).toBe(false);
      expect(validateUsername('a'.repeat(21))).toBe(false);
      expect(validateUsername('')).toBe(false);
    });
  });

  describe('validatePhone', () => {
    it('should validate correct Chinese phone numbers', () => {
      expect(validatePhone('13812345678')).toBe(true);
      expect(validatePhone('15987654321')).toBe(true);
      expect(validatePhone('18888888888')).toBe(true);
    });

    it('should reject invalid phone numbers', () => {
      expect(validatePhone('12812345678')).toBe(false);
      expect(validatePhone('1381234567')).toBe(false);
      expect(validatePhone('138123456789')).toBe(false);
      expect(validatePhone('')).toBe(false);
    });
  });

  describe('formatDate', () => {
    it('should format date correctly', () => {
      const date = new Date('2023-12-25T10:30:45');
      expect(formatDate(date, 'YYYY-MM-DD')).toBe('2023-12-25');
      expect(formatDate(date, 'YYYY-MM-DD HH:mm:ss')).toBe('2023-12-25 10:30:45');
    });

    it('should handle string dates', () => {
      expect(formatDate('2023-12-25', 'YYYY-MM-DD')).toBe('2023-12-25');
    });
  });

  describe('delay', () => {
    it('should delay execution', async () => {
      const start = Date.now();
      await delay(100);
      const end = Date.now();
      expect(end - start).toBeGreaterThanOrEqual(90);
    });
  });

  describe('generateRandomString', () => {
    it('should generate string of correct length', () => {
      expect(generateRandomString(10)).toHaveLength(10);
      expect(generateRandomString(5)).toHaveLength(5);
    });

    it('should generate different strings', () => {
      const str1 = generateRandomString(10);
      const str2 = generateRandomString(10);
      expect(str1).not.toBe(str2);
    });
  });

  describe('isEmpty', () => {
    it('should detect empty values', () => {
      expect(isEmpty(null)).toBe(true);
      expect(isEmpty(undefined)).toBe(true);
      expect(isEmpty('')).toBe(true);
      expect(isEmpty([])).toBe(true);
      expect(isEmpty({})).toBe(true);
    });

    it('should detect non-empty values', () => {
      expect(isEmpty('text')).toBe(false);
      expect(isEmpty([1, 2, 3])).toBe(false);
      expect(isEmpty({ key: 'value' })).toBe(false);
      expect(isEmpty(0)).toBe(false);
    });
  });

  describe('capitalize', () => {
    it('should capitalize first letter', () => {
      expect(capitalize('hello')).toBe('Hello');
      expect(capitalize('WORLD')).toBe('World');
      expect(capitalize('tEST')).toBe('Test');
    });

    it('should handle empty string', () => {
      expect(capitalize('')).toBe('');
    });
  });

  describe('truncateText', () => {
    it('should truncate long text', () => {
      const longText = 'This is a very long text that should be truncated';
      expect(truncateText(longText, 10)).toBe('This is a ...');
    });

    it('should not truncate short text', () => {
      const shortText = 'Short';
      expect(truncateText(shortText, 10)).toBe('Short');
    });
  });
});
