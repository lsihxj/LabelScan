/**
 * API客户端
 */
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

/**
 * 处理单张图像
 */
export const processSingleImage = async (formData) => {
  return await apiClient.post('/process/single', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

/**
 * 流式处理单张图像(AI识别)
 * @param {FormData} formData - 表单数据
 * @param {Function} onChunk - 每个数据块的回调函数
 */
export const processSingleImageStream = async (formData, onChunk) => {
  const response = await fetch('/api/v1/process/single/stream', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              onChunk(parsed.content);
            } else if (parsed.error) {
              throw new Error(parsed.error);
            }
          } catch (e) {
            console.warn('Failed to parse chunk:', data, e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};

/**
 * 批量处理图像
 */
export const processBatchImages = async (formData) => {
  return await apiClient.post('/process/batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
};

/**
 * 获取健康状态
 */
export const getHealth = async () => {
  return await apiClient.get('/health');
};

/**
 * 获取配置
 */
export const getConfig = async () => {
  return await apiClient.get('/config');
};

/**
 * 更新配置
 */
export const updateConfig = async (config) => {
  return await apiClient.put('/config', config);
};

export default apiClient;
