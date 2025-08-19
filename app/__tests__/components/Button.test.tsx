/**
 * Button组件测试
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import Button from '../../src/components/common/Button';

describe('Button Component', () => {
  const mockOnPress = jest.fn();

  beforeEach(() => {
    mockOnPress.mockClear();
  });

  it('renders correctly with title', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={mockOnPress} />
    );
    expect(getByText('Test Button')).toBeTruthy();
  });

  it('calls onPress when pressed', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={mockOnPress} />
    );
    
    fireEvent.press(getByText('Test Button'));
    expect(mockOnPress).toHaveBeenCalledTimes(1);
  });

  it('does not call onPress when disabled', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={mockOnPress} disabled />
    );
    
    fireEvent.press(getByText('Test Button'));
    expect(mockOnPress).not.toHaveBeenCalled();
  });

  it('shows loading state correctly', () => {
    const { getByText } = render(
      <Button title="Test Button" onPress={mockOnPress} loading />
    );
    
    expect(getByText('加载中...')).toBeTruthy();
  });

  it('renders different variants correctly', () => {
    const variants = ['primary', 'secondary', 'outline', 'ghost', 'danger'] as const;
    
    variants.forEach(variant => {
      const { getByText } = render(
        <Button title={`${variant} Button`} onPress={mockOnPress} variant={variant} />
      );
      expect(getByText(`${variant} Button`)).toBeTruthy();
    });
  });

  it('renders different sizes correctly', () => {
    const sizes = ['small', 'medium', 'large'] as const;
    
    sizes.forEach(size => {
      const { getByText } = render(
        <Button title={`${size} Button`} onPress={mockOnPress} size={size} />
      );
      expect(getByText(`${size} Button`)).toBeTruthy();
    });
  });

  it('should match snapshot', () => {
    const tree = render(
      <Button title="Snapshot Button" onPress={mockOnPress} />
    );
    expect(tree).toMatchSnapshot();
  });
});
