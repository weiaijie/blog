/**
 * 待办事项管理页面
 *
 * 这是一个功能完整的任务管理页面，提供以下功能：
 *
 * 核心功能：
 * 1. 任务列表展示 - 显示所有待办事项
 * 2. 任务添加 - 通过模态框添加新任务
 * 3. 任务状态切换 - 标记任务为完成/未完成
 * 4. 任务删除 - 删除不需要的任务
 * 5. 任务过滤 - 按状态筛选任务（全部/待完成/已完成）
 * 6. 优先级管理 - 为任务设置优先级（高/中/低）
 * 7. 统计信息 - 显示任务总数、完成数等统计
 *
 * 用户体验特性：
 * - 直观的UI设计
 * - 流畅的交互动画
 * - 清晰的视觉反馈
 * - 响应式布局
 */

import React, { useState, useEffect } from 'react';
import {
  View,           // 基础容器组件
  Text,           // 文本显示组件
  ScrollView,     // 可滚动容器组件
  StyleSheet,     // 样式表
  TouchableOpacity, // 可点击容器组件
  Alert,          // 系统弹窗组件
  TextInput,      // 文本输入组件
  Modal,          // 模态框组件
} from 'react-native';

import { Button } from '../../components/common'; // 自定义按钮组件

/**
 * 待办事项数据结构
 * 定义了每个任务的完整信息
 */
interface TodoItem {
  id: string;                                    // 唯一标识符
  title: string;                                 // 任务标题（必填）
  description?: string;                          // 任务描述（可选）
  completed: boolean;                            // 完成状态
  createdAt: Date;                              // 创建时间
  priority: 'low' | 'medium' | 'high';          // 优先级（低/中/高）
}

/**
 * 待办事项页面主组件
 */
const TodoScreen: React.FC = () => {
  // ==================== 状态管理 ====================

  // 待办事项列表状态
  const [todos, setTodos] = useState<TodoItem[]>([]);

  // 添加任务模态框显示状态
  const [showAddModal, setShowAddModal] = useState(false);

  // 新任务表单数据状态
  const [newTodo, setNewTodo] = useState({
    title: '',                                    // 任务标题
    description: '',                              // 任务描述
    priority: 'medium' as TodoItem['priority'],   // 默认优先级为中等
  });

  // 任务过滤状态（全部/待完成/已完成）
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');

  // ==================== 初始化数据 ====================

  /**
   * 组件挂载时初始化示例数据
   *
   * 这里创建了一些示例任务来演示功能
   * 在实际应用中，这些数据应该从API或本地存储加载
   */
  useEffect(() => {
    const sampleTodos: TodoItem[] = [
      {
        id: '1',
        title: '学习React Native',
        description: '完成基础教程和实践项目',
        completed: false,
        createdAt: new Date(),
        priority: 'high',
      },
      {
        id: '2',
        title: '完善应用功能',
        description: '添加更多实用功能模块',
        completed: false,
        createdAt: new Date(),
        priority: 'medium',
      },
      {
        id: '3',
        title: '优化用户界面',
        description: '改进UI设计和用户体验',
        completed: true,
        createdAt: new Date(),
        priority: 'low',
      },
    ];
    setTodos(sampleTodos);
  }, []); // 空依赖数组，只在组件挂载时执行一次

  // ==================== 核心业务逻辑函数 ====================

  /**
   * 添加新的待办事项
   *
   * 功能：
   * 1. 验证输入数据的有效性
   * 2. 创建新的待办事项对象
   * 3. 更新待办事项列表
   * 4. 重置表单并关闭模态框
   */
  const addTodo = () => {
    // 验证标题是否为空
    if (!newTodo.title.trim()) {
      Alert.alert('提示', '请输入待办事项标题');
      return;
    }

    // 创建新的待办事项对象
    const todo: TodoItem = {
      id: Date.now().toString(),              // 使用时间戳作为唯一ID
      title: newTodo.title.trim(),            // 去除首尾空格
      description: newTodo.description.trim(), // 去除首尾空格
      completed: false,                       // 新任务默认未完成
      createdAt: new Date(),                  // 设置创建时间
      priority: newTodo.priority,             // 使用用户选择的优先级
    };

    // 将新任务添加到列表开头（最新的任务显示在最上面）
    setTodos([todo, ...todos]);

    // 重置表单数据
    setNewTodo({ title: '', description: '', priority: 'medium' });

    // 关闭添加模态框
    setShowAddModal(false);
  };

  /**
   * 切换待办事项的完成状态
   *
   * @param id - 要切换状态的待办事项ID
   */
  const toggleTodo = (id: string) => {
    setTodos(todos.map(todo =>
      // 如果是目标任务，切换其完成状态；否则保持不变
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  /**
   * 删除待办事项
   *
   * @param id - 要删除的待办事项ID
   *
   * 功能：
   * 1. 显示确认对话框
   * 2. 用户确认后从列表中移除对应的任务
   */
  const deleteTodo = (id: string) => {
    Alert.alert(
      '确认删除',
      '确定要删除这个待办事项吗？',
      [
        { text: '取消', style: 'cancel' },  // 取消按钮
        {
          text: '删除',
          style: 'destructive',              // 危险操作样式
          onPress: () => setTodos(todos.filter(todo => todo.id !== id)) // 从列表中移除
        },
      ]
    );
  };

  // ==================== 工具函数 ====================

  /**
   * 根据当前过滤条件获取过滤后的待办事项列表
   *
   * @returns 过滤后的待办事项数组
   */
  const getFilteredTodos = () => {
    switch (filter) {
      case 'active':
        return todos.filter(todo => !todo.completed);  // 只返回未完成的任务
      case 'completed':
        return todos.filter(todo => todo.completed);   // 只返回已完成的任务
      default:
        return todos;                                   // 返回所有任务
    }
  };

  /**
   * 根据优先级获取对应的颜色
   *
   * @param priority - 任务优先级
   * @returns 对应的颜色值（十六进制）
   */
  const getPriorityColor = (priority: TodoItem['priority']) => {
    switch (priority) {
      case 'high': return '#EF4444';    // 红色 - 高优先级
      case 'medium': return '#F59E0B';  // 橙色 - 中优先级
      case 'low': return '#10B981';     // 绿色 - 低优先级
      default: return '#6B7280';        // 灰色 - 默认颜色
    }
  };

  /**
   * 根据优先级获取对应的中文文本
   *
   * @param priority - 任务优先级
   * @returns 对应的中文描述
   */
  const getPriorityText = (priority: TodoItem['priority']) => {
    switch (priority) {
      case 'high': return '高';     // 高优先级
      case 'medium': return '中';   // 中优先级
      case 'low': return '低';      // 低优先级
      default: return '中';         // 默认为中优先级
    }
  };

  // ==================== 计算派生状态 ====================

  // 根据当前过滤条件获取要显示的待办事项列表
  const filteredTodos = getFilteredTodos();

  // 计算已完成任务的数量
  const completedCount = todos.filter(todo => todo.completed).length;

  // 计算任务总数
  const totalCount = todos.length;

  // ==================== 渲染UI ====================

  return (
    <View style={styles.container}>
      {/* 统计信息卡片 - 显示任务的统计数据 */}
      <View style={styles.statsContainer}>
        {/* 总任务数 */}
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{totalCount}</Text>
          <Text style={styles.statLabel}>总计</Text>
        </View>

        {/* 待完成任务数 */}
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{totalCount - completedCount}</Text>
          <Text style={styles.statLabel}>待完成</Text>
        </View>

        {/* 已完成任务数 */}
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{completedCount}</Text>
          <Text style={styles.statLabel}>已完成</Text>
        </View>
      </View>

      {/* 过滤器 */}
      <View style={styles.filterContainer}>
        {(['all', 'active', 'completed'] as const).map((filterType) => (
          <TouchableOpacity
            key={filterType}
            style={[
              styles.filterButton,
              filter === filterType && styles.activeFilterButton,
            ]}
            onPress={() => setFilter(filterType)}
          >
            <Text
              style={[
                styles.filterText,
                filter === filterType && styles.activeFilterText,
              ]}
            >
              {filterType === 'all' ? '全部' : 
               filterType === 'active' ? '待完成' : '已完成'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 待办事项列表 */}
      <ScrollView style={styles.todoList} showsVerticalScrollIndicator={false}>
        {filteredTodos.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              {filter === 'all' ? '暂无待办事项' :
               filter === 'active' ? '暂无待完成事项' : '暂无已完成事项'}
            </Text>
          </View>
        ) : (
          filteredTodos.map((todo) => (
            <View key={todo.id} style={styles.todoItem}>
              <TouchableOpacity
                style={styles.todoContent}
                onPress={() => toggleTodo(todo.id)}
              >
                <View style={styles.todoHeader}>
                  <View style={styles.todoTitleRow}>
                    <Text
                      style={[
                        styles.todoTitle,
                        todo.completed && styles.completedTitle,
                      ]}
                    >
                      {todo.title}
                    </Text>
                    <View
                      style={[
                        styles.priorityBadge,
                        { backgroundColor: getPriorityColor(todo.priority) },
                      ]}
                    >
                      <Text style={styles.priorityText}>
                        {getPriorityText(todo.priority)}
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.checkbox}>
                    {todo.completed ? '✅' : '⭕'}
                  </Text>
                </View>
                {todo.description ? (
                  <Text
                    style={[
                      styles.todoDescription,
                      todo.completed && styles.completedDescription,
                    ]}
                  >
                    {todo.description}
                  </Text>
                ) : null}
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.deleteButton}
                onPress={() => deleteTodo(todo.id)}
              >
                <Text style={styles.deleteText}>🗑️</Text>
              </TouchableOpacity>
            </View>
          ))
        )}
      </ScrollView>

      {/* 添加按钮 */}
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => setShowAddModal(true)}
      >
        <Text style={styles.addButtonText}>+</Text>
      </TouchableOpacity>

      {/* 添加待办事项模态框 */}
      <Modal
        visible={showAddModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowAddModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>添加待办事项</Text>
            <TouchableOpacity onPress={() => setShowAddModal(false)}>
              <Text style={styles.closeButton}>✕</Text>
            </TouchableOpacity>
          </View>
          
          <View style={styles.modalContent}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>标题 *</Text>
              <TextInput
                style={styles.textInput}
                value={newTodo.title}
                onChangeText={(text) => setNewTodo({ ...newTodo, title: text })}
                placeholder="输入待办事项标题"
                maxLength={50}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>描述</Text>
              <TextInput
                style={[styles.textInput, styles.textArea]}
                value={newTodo.description}
                onChangeText={(text) => setNewTodo({ ...newTodo, description: text })}
                placeholder="输入详细描述（可选）"
                multiline
                numberOfLines={3}
                maxLength={200}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>优先级</Text>
              <View style={styles.prioritySelector}>
                {(['low', 'medium', 'high'] as const).map((priority) => (
                  <TouchableOpacity
                    key={priority}
                    style={[
                      styles.priorityOption,
                      newTodo.priority === priority && styles.selectedPriority,
                      { borderColor: getPriorityColor(priority) },
                    ]}
                    onPress={() => setNewTodo({ ...newTodo, priority })}
                  >
                    <Text
                      style={[
                        styles.priorityOptionText,
                        newTodo.priority === priority && { color: getPriorityColor(priority) },
                      ]}
                    >
                      {getPriorityText(priority)}优先级
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.modalActions}>
              <Button
                title="取消"
                onPress={() => setShowAddModal(false)}
                variant="outline"
                style={styles.modalButton}
              />
              <Button
                title="添加"
                onPress={addTodo}
                variant="primary"
                style={styles.modalButton}
              />
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    margin: 16,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
  },
  statLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
  filterContainer: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 4,
  },
  filterButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeFilterButton: {
    backgroundColor: '#007AFF',
  },
  filterText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  activeFilterText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  todoList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#6B7280',
  },
  todoItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
    flexDirection: 'row',
    alignItems: 'center',
  },
  todoContent: {
    flex: 1,
    padding: 16,
  },
  todoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  todoTitleRow: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  todoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
  },
  completedTitle: {
    textDecorationLine: 'line-through',
    color: '#6B7280',
  },
  priorityBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  priorityText: {
    fontSize: 10,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  checkbox: {
    fontSize: 20,
  },
  todoDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    lineHeight: 20,
  },
  completedDescription: {
    textDecorationLine: 'line-through',
  },
  deleteButton: {
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteText: {
    fontSize: 18,
  },
  addButton: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4.65,
    elevation: 8,
  },
  addButtonText: {
    fontSize: 24,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  closeButton: {
    fontSize: 18,
    color: '#6B7280',
    padding: 4,
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#FFFFFF',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  prioritySelector: {
    flexDirection: 'row',
    gap: 8,
  },
  priorityOption: {
    flex: 1,
    borderWidth: 2,
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  selectedPriority: {
    backgroundColor: '#F9FAFB',
  },
  priorityOptionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  modalButton: {
    flex: 1,
  },
});

export default TodoScreen;
