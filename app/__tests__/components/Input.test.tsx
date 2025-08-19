/**
 * Input组件测试
 */

import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import Input from '../../src/components/common/Input';

describe('Input Component', () => {
  const mockOnChangeText = jest.fn();

  beforeEach(() => {
    mockOnChangeText.mockClear();
  });

  it('renders correctly with placeholder', () => {
    const { getByPlaceholderText } = render(
      <Input placeholder="Test Input" onChangeText={mockOnChangeText} />
    );
    expect(getByPlaceholderText('Test Input')).toBeTruthy();
  });

  it('renders label when provided', () => {
    const { getByText } = render(
      <Input label="Test Label" onChangeText={mockOnChangeText} />
    );
    expect(getByText('Test Label')).toBeTruthy();
  });

  it('shows required indicator when required', () => {
    const { getByText } = render(
      <Input label="Required Field" required onChangeText={mockOnChangeText} />
    );
    expect(getByText(/Required Field/)).toBeTruthy();
    expect(getByText('*')).toBeTruthy();
  });

  it('shows error message when error is provided', () => {
    const { getByText } = render(
      <Input error="This field is required" onChangeText={mockOnChangeText} />
    );
    expect(getByText('This field is required')).toBeTruthy();
  });

  it('shows helper text when provided', () => {
    const { getByText } = render(
      <Input helperText="This is helper text" onChangeText={mockOnChangeText} />
    );
    expect(getByText('This is helper text')).toBeTruthy();
  });

  it('calls onChangeText when text changes', () => {
    const { getByDisplayValue } = render(
      <Input value="" onChangeText={mockOnChangeText} />
    );
    
    fireEvent.changeText(getByDisplayValue(''), 'new text');
    expect(mockOnChangeText).toHaveBeenCalledWith('new text');
  });

  it('toggles password visibility when showPasswordToggle is true', () => {
    const { getByText } = render(
      <Input 
        secureTextEntry 
        showPasswordToggle 
        onChangeText={mockOnChangeText} 
      />
    );
    
    const toggleButton = getByText('👁️');
    fireEvent.press(toggleButton);
    
    // After toggle, icon should change
    expect(getByText('🙈')).toBeTruthy();
  });

  it('should match snapshot', () => {
    const tree = render(
      <Input 
        label="Snapshot Input"
        placeholder="Enter text"
        onChangeText={mockOnChangeText}
      />
    );
    expect(tree).toMatchSnapshot();
  });
});
