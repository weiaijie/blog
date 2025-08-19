/**
 * performance.ts
 *
 * 描述：性能监控和分析工具
 *
 * 功能：
 * - 监控页面加载性能
 * - 分析Core Web Vitals指标
 * - 监控资源加载时间
 * - 提供性能优化建议
 *
 * 主要功能：
 * - measurePageLoad：测量页面加载性能
 * - measureCoreWebVitals：测量核心Web指标
 * - analyzeBundle：分析bundle大小
 * - reportPerformance：上报性能数据
 */

// 性能指标接口
interface PerformanceMetrics {
  // Core Web Vitals
  LCP?: number; // Largest Contentful Paint
  FID?: number; // First Input Delay
  CLS?: number; // Cumulative Layout Shift
  
  // 其他重要指标
  FCP?: number; // First Contentful Paint
  TTFB?: number; // Time to First Byte
  TTI?: number; // Time to Interactive
  
  // 自定义指标
  pageLoadTime?: number;
  domContentLoaded?: number;
  resourceLoadTime?: number;
}

// 性能监控类
export class PerformanceMonitor {
  private metrics: PerformanceMetrics = {};
  private observer?: PerformanceObserver;

  constructor() {
    if (typeof window !== 'undefined') {
      this.initializeMonitoring();
    }
  }

  // 初始化性能监控
  private initializeMonitoring() {
    // 监控导航时间
    this.measureNavigationTiming();
    
    // 监控Core Web Vitals
    this.measureCoreWebVitals();
    
    // 监控资源加载
    this.measureResourceTiming();
  }

  // 测量导航时间
  private measureNavigationTiming() {
    window.addEventListener('load', () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      if (navigation) {
        this.metrics.pageLoadTime = navigation.loadEventEnd - navigation.fetchStart;
        this.metrics.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.fetchStart;
        this.metrics.TTFB = navigation.responseStart - navigation.fetchStart;
      }
    });
  }

  // 测量Core Web Vitals
  private measureCoreWebVitals() {
    // LCP (Largest Contentful Paint)
    this.observePerformanceEntry('largest-contentful-paint', (entries) => {
      const lastEntry = entries[entries.length - 1];
      this.metrics.LCP = lastEntry.startTime;
    });

    // FID (First Input Delay)
    this.observePerformanceEntry('first-input', (entries) => {
      const firstEntry = entries[0];
      this.metrics.FID = firstEntry.processingStart - firstEntry.startTime;
    });

    // CLS (Cumulative Layout Shift)
    this.observePerformanceEntry('layout-shift', (entries) => {
      let clsValue = 0;
      for (const entry of entries) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value;
        }
      }
      this.metrics.CLS = clsValue;
    });

    // FCP (First Contentful Paint)
    this.observePerformanceEntry('paint', (entries) => {
      const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        this.metrics.FCP = fcpEntry.startTime;
      }
    });
  }

  // 测量资源加载时间
  private measureResourceTiming() {
    window.addEventListener('load', () => {
      const resources = performance.getEntriesByType('resource');
      const totalResourceTime = resources.reduce((total, resource) => {
        return total + (resource.responseEnd - resource.startTime);
      }, 0);
      
      this.metrics.resourceLoadTime = totalResourceTime;
    });
  }

  // 观察性能条目
  private observePerformanceEntry(entryType: string, callback: (entries: PerformanceEntry[]) => void) {
    try {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries());
      });
      
      observer.observe({ entryTypes: [entryType] });
    } catch (error) {
      console.warn(`Performance observer for ${entryType} not supported:`, error);
    }
  }

  // 获取性能指标
  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  // 分析性能并提供建议
  public analyzePerformance(): string[] {
    const suggestions: string[] = [];
    
    // LCP建议
    if (this.metrics.LCP && this.metrics.LCP > 2500) {
      suggestions.push('LCP过高，建议优化图片加载和关键资源');
    }
    
    // FID建议
    if (this.metrics.FID && this.metrics.FID > 100) {
      suggestions.push('FID过高，建议减少JavaScript执行时间');
    }
    
    // CLS建议
    if (this.metrics.CLS && this.metrics.CLS > 0.1) {
      suggestions.push('CLS过高，建议为图片和广告设置尺寸');
    }
    
    // 页面加载时间建议
    if (this.metrics.pageLoadTime && this.metrics.pageLoadTime > 3000) {
      suggestions.push('页面加载时间过长，建议优化资源加载');
    }
    
    return suggestions;
  }

  // 上报性能数据
  public reportPerformance() {
    const metrics = this.getMetrics();
    const suggestions = this.analyzePerformance();
    
    // 在开发环境下输出到控制台
    if (process.env.NODE_ENV === 'development') {
      console.group('🚀 Performance Metrics');
      console.table(metrics);
      if (suggestions.length > 0) {
        console.group('💡 Performance Suggestions');
        suggestions.forEach(suggestion => console.log(`• ${suggestion}`));
        console.groupEnd();
      }
      console.groupEnd();
    }
    
    // 在生产环境下可以发送到分析服务
    if (process.env.NODE_ENV === 'production') {
      // 这里可以集成Google Analytics、Sentry等服务
      // gtag('event', 'performance_metrics', metrics);
    }
  }

  // 清理监控
  public cleanup() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

// 创建全局性能监控实例
export const performanceMonitor = new PerformanceMonitor();

// 便捷函数
export const measurePagePerformance = () => {
  return performanceMonitor.getMetrics();
};

export const getPerformanceSuggestions = () => {
  return performanceMonitor.analyzePerformance();
};

// 分析bundle大小的工具函数
export const analyzeBundleSize = () => {
  if (typeof window === 'undefined') return;
  
  const scripts = Array.from(document.querySelectorAll('script[src]'));
  const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
  
  console.group('📦 Bundle Analysis');
  
  scripts.forEach((script: HTMLScriptElement) => {
    if (script.src.includes('_next/static')) {
      console.log(`JS: ${script.src.split('/').pop()}`);
    }
  });
  
  styles.forEach((style: HTMLLinkElement) => {
    if (style.href.includes('_next/static')) {
      console.log(`CSS: ${style.href.split('/').pop()}`);
    }
  });
  
  console.groupEnd();
};

// 在页面加载完成后自动上报性能数据
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    setTimeout(() => {
      performanceMonitor.reportPerformance();
      analyzeBundleSize();
    }, 1000);
  });
}
