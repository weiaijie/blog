/**
 * ProjectFilter.tsx
 *
 * 描述：项目筛选组件，用于筛选和排序项目展示
 *
 * 功能：
 * - 按项目分类筛选
 * - 按技术栈筛选
 * - 按项目状态筛选
 * - 按时间排序
 * - 支持多条件组合筛选
 *
 * 主要组件/接口：
 * - ProjectFilter：项目筛选组件
 * - ProjectFilterProps：组件属性接口
 * - FilterOptions：筛选选项接口
 *
 * 导出：
 * - ProjectFilter 组件（默认导出）
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ProjectItem, ProjectStatus, ProjectType } from '@/config/projects';
import styles from '@/styles/ProjectFilter.module.css';

// 排序选项
export type SortOption = 'newest' | 'oldest' | 'name' | 'status';

// 筛选选项接口
export interface FilterOptions {
  category: string;
  technology: string;
  status: ProjectStatus | 'all';
  type: ProjectType | 'all';
  sort: SortOption;
  search: string;
}

// 组件属性接口
interface ProjectFilterProps {
  projects: ProjectItem[];
  onFilterChange: (filters: FilterOptions) => void;
  className?: string;
}

const ProjectFilter: React.FC<ProjectFilterProps> = ({ 
  projects, 
  onFilterChange, 
  className = '' 
}) => {
  const [filters, setFilters] = useState<FilterOptions>({
    category: 'all',
    technology: 'all',
    status: 'all',
    type: 'all',
    sort: 'newest',
    search: ''
  });

  const [isExpanded, setIsExpanded] = useState(false);

  // 获取所有技术栈选项
  const getAllTechnologies = () => {
    const techSet = new Set<string>();
    projects.forEach(project => {
      project.technologies.forEach(tech => techSet.add(tech));
    });
    return Array.from(techSet).sort();
  };

  // 更新筛选条件
  const updateFilter = (key: keyof FilterOptions, value: string | SortOption | ProjectStatus | ProjectType) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  // 重置筛选条件
  const resetFilters = () => {
    const defaultFilters: FilterOptions = {
      category: 'all',
      technology: 'all',
      status: 'all',
      type: 'all',
      sort: 'newest',
      search: ''
    };
    setFilters(defaultFilters);
    onFilterChange(defaultFilters);
  };

  // 获取活跃筛选条件数量
  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.category !== 'all') count++;
    if (filters.technology !== 'all') count++;
    if (filters.status !== 'all') count++;
    if (filters.type !== 'all') count++;
    if (filters.search.trim() !== '') count++;
    return count;
  };

  const activeFiltersCount = getActiveFiltersCount();
  const technologies = getAllTechnologies();

  return (
    <motion.div 
      className={`${styles.projectFilter} ${className}`}
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
          aria-expanded={isExpanded}
          aria-controls="filter-content"
          aria-label={`${isExpanded ? '收起' : '展开'}项目筛选选项`}
        >
          <span className={styles.toggleIcon}>🔍</span>
          <span className={styles.toggleText}>项目筛选</span>
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
        id="filter-content"
        className={styles.filterContent}
        initial={false}
        animate={{
          height: isExpanded ? 'auto' : 0,
          opacity: isExpanded ? 1 : 0
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        style={{ overflow: 'hidden' }}
        role="region"
        aria-label="项目筛选选项"
      >
        <div className={styles.filterControls}>
          {/* 搜索框 */}
          <div className={styles.filterGroup}>
            <label htmlFor="project-search" className={styles.filterLabel}>搜索项目</label>
            <input
              id="project-search"
              type="text"
              className={styles.searchInput}
              placeholder="输入项目名称或描述..."
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
              aria-describedby="search-help"
            />
            <div id="search-help" className="sr-only">
              搜索项目名称、描述或技术栈
            </div>
          </div>

          {/* 分类筛选 */}
          <div className={styles.filterGroup}>
            <label htmlFor="category-select" className={styles.filterLabel}>项目分类</label>
            <select
              id="category-select"
              className={styles.filterSelect}
              value={filters.category}
              onChange={(e) => updateFilter('category', e.target.value)}
              aria-label="选择项目分类"
            >
              <option value="all">全部分类</option>
              <option value="enterprise">🏢 企业级应用</option>
              <option value="business-systems">💼 业务系统</option>
              <option value="web-development">🌐 Web开发</option>
            </select>
          </div>

          {/* 技术栈筛选 */}
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>技术栈</label>
            <select
              className={styles.filterSelect}
              value={filters.technology}
              onChange={(e) => updateFilter('technology', e.target.value)}
            >
              <option value="all">全部技术</option>
              {technologies.map((tech) => (
                <option key={tech} value={tech}>{tech}</option>
              ))}
            </select>
          </div>

          {/* 项目状态筛选 */}
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>项目状态</label>
            <select
              className={styles.filterSelect}
              value={filters.status}
              onChange={(e) => updateFilter('status', e.target.value as ProjectStatus | 'all')}
            >
              <option value="all">全部状态</option>
              <option value="completed">✅ 已完成</option>
              <option value="in-progress">🔄 进行中</option>
              <option value="archived">📦 已归档</option>
            </select>
          </div>

          {/* 项目类型筛选 */}
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>项目类型</label>
            <select
              className={styles.filterSelect}
              value={filters.type}
              onChange={(e) => updateFilter('type', e.target.value as ProjectType | 'all')}
            >
              <option value="all">全部类型</option>
              <option value="web-app">🌐 Web应用</option>
              <option value="mobile-app">📱 移动应用</option>
              <option value="desktop-app">💻 桌面应用</option>
              <option value="library">📚 库/框架</option>
              <option value="tool">🔧 工具</option>
            </select>
          </div>

          {/* 排序选项 */}
          <div className={styles.filterGroup}>
            <label className={styles.filterLabel}>排序方式</label>
            <select
              className={styles.filterSelect}
              value={filters.sort}
              onChange={(e) => updateFilter('sort', e.target.value as SortOption)}
            >
              <option value="newest">⏰ 最新项目</option>
              <option value="oldest">📅 最早项目</option>
              <option value="name">🔤 项目名称</option>
              <option value="status">📊 项目状态</option>
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

export default ProjectFilter;
