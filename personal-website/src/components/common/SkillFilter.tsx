/**
 * SkillFilter.tsx
 *
 * 描述：技能筛选组件，用于筛选和过滤技能展示
 *
 * 功能：
 * - 按技能分类筛选
 * - 按熟练度等级筛选
 * - 按技能名称搜索
 * - 支持多条件组合筛选
 *
 * 主要组件/接口：
 * - SkillFilter：技能筛选组件
 * - SkillFilterProps：组件属性接口
 * - FilterOptions：筛选选项接口
 *
 * 导出：
 * - SkillFilter 组件（默认导出）
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { SkillCategory, SkillLevel } from '@/config/skills';
import styles from '@/styles/SkillFilter.module.css';

// 筛选选项接口
export interface FilterOptions {
  category: string;
  level: SkillLevel | 'all';
  search: string;
}

// 组件属性接口
interface SkillFilterProps {
  categories: SkillCategory[];
  onFilterChange: (filters: FilterOptions) => void;
  className?: string;
}

const SkillFilter: React.FC<SkillFilterProps> = ({ 
  categories, 
  onFilterChange, 
  className = '' 
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    category: 'all',
    level: 'all',
    search: ''
  });

  const [isExpanded, setIsExpanded] = useState(false);

  // 更新筛选条件
  const updateFilter = (key: keyof FilterOptions, value: string | SkillLevel) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  // 重置筛选条件
  const resetFilters = () => {
    const defaultFilters: FilterOptions = {
      category: 'all',
      level: 'all',
      search: ''
    };
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  };

  // 获取活跃筛选条件数量
  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.category !== 'all') count++;
    if (filters.level !== 'all') count++;
    if (filters.search.trim() !== '') count++;
    return count;
  };

  const activeFiltersCount = getActiveFiltersCount();

  return (
    <motion.div 
      className={`${styles.skillFilter} ${className}`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* 筛选器头部 */}
      <div className={styles.filterHeader}>
        <motion.button
          className={styles.toggleButton}
          onClick={() => setIsExpanded(!isExpanded)}
          whileTap={{ scale: 0.95 }}
        >
          <span className={styles.toggleIcon}>🔍</span>
          <span className={styles.toggleText}>技能筛选</span>
          {activeFiltersCount > 0 && (
            <span className={styles.filterBadge}>{activeFiltersCount}</span>
          )}
          <motion.span
            className={styles.expandIcon}
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            ▼
          </motion.span>
        </motion.button>
      </div>

      {/* 筛选器内容 */}
      <motion.div
        className={styles.filterContent}
        initial={false}
        animate={{ 
          height: isExpanded ? 'auto' : 0,
          opacity: isExpanded ? 1 : 0
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        style={{ overflow: 'hidden' }}
      >
        <div className={styles.filterControls}>
          {/* 搜索框 */}
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>搜索技能</label>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="输入技能名称..."
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
            />
          </div>

          {/* 分类筛选 */}
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>技能分类</label>
            <select
              className={styles.filterSelect}
              value={filters.category}
              onChange={(e) => updateFilter('category', e.target.value)}
            >
              <option value="all">全部分类</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.icon} {category.name}
                </option>
              ))}
            </select>
          </div>

          {/* 熟练度筛选 */}
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>熟练度等级</label>
            <select
              className={styles.filterSelect}
              value={filters.level}
              onChange={(e) => updateFilter('level', e.target.value as SkillLevel | 'all')}
            >
              <option value="all">全部等级</option>
              <option value={5}>⭐⭐⭐⭐⭐ 专家级</option>
              <option value={4}>⭐⭐⭐⭐ 精通</option>
              <option value={3}>⭐⭐⭐ 熟练</option>
              <option value={2}>⭐⭐ 基础</option>
              <option value={1}>⭐ 入门</option>
            </select>
          </div>

          {/* 重置按钮 */}
          {activeFiltersCount > 0 && (
            <motion.button
              className={styles.resetButton}
              onClick={resetFilters}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              重置筛选
            </motion.button>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SkillFilter;
