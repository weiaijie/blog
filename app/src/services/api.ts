// API配置文件
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// API基础配置
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:3000/api' 
  : 'https://your-production-api.com/api';

const API_TIMEOUT = 10000; // 10秒超时

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // 在这里可以添加认证token等
    // const token = getAuthToken();
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    if (__DEV__) {
      console.log('API Request:', config);
    }
    
    return config;
  },
  (error) => {
    if (__DEV__) {
      console.error('API Request Error:', error);
    }
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    if (__DEV__) {
      console.log('API Response:', response);
    }
    return response;
  },
  (error) => {
    if (__DEV__) {
      console.error('API Response Error:', error);
    }
    
    // 处理常见错误
    if (error.response?.status === 401) {
      // 处理未授权错误
      // 可以在这里清除token并跳转到登录页
    }
    
    if (error.response?.status === 500) {
      // 处理服务器错误
      console.error('服务器内部错误');
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
export { API_BASE_URL, API_TIMEOUT };
