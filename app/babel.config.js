module.exports = {
  presets: [
    ['@babel/preset-env', {
      targets: {
        browsers: ['last 2 versions', 'ie >= 11']
      }
    }],
    '@babel/preset-react',
    '@babel/preset-typescript'
  ],
  plugins: [
    '@babel/plugin-proposal-class-properties',
  ],
  env: {
    // React Native环境配置
    development: {
      presets: ['module:metro-react-native-babel-preset'],
    }
  }
};
