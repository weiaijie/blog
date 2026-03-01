// Jest setup file

// Mock React Native modules
jest.mock('react-native/Libraries/Animated/NativeAnimatedHelper');

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock react-native modules
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  
  // Mock useColorScheme
  RN.useColorScheme = jest.fn(() => 'light');
  
  return RN;
});

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Setup test environment
beforeEach(() => {
  jest.clearAllMocks();
});
