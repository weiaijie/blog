/**
 * App组件测试
 */

import React from 'react';
import { render } from '@testing-library/react-native';
import App from '../src/App';

// Mock导航组件
jest.mock('../src/navigation/AppNavigator', () => {
  const React = require('react');
  const { View, Text } = require('react-native');
  
  return function MockAppNavigator() {
    return React.createElement(View, { testID: 'app-navigator' }, 
      React.createElement(Text, null, 'Mock App Navigator')
    );
  };
});

describe('App Component', () => {
  it('renders correctly', () => {
    const { getByTestId } = render(<App />);
    expect(getByTestId('app-navigator')).toBeTruthy();
  });

  it('should match snapshot', () => {
    const tree = render(<App />);
    expect(tree).toMatchSnapshot();
  });
});
