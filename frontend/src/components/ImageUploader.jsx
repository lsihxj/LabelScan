import React, { useState, useEffect, useRef } from 'react';
import { Upload, Button, Select, Space, Card, Spin, message } from 'antd';
import { UploadOutlined, FileImageOutlined } from '@ant-design/icons';
import { processSingleImage, processSingleImageStream } from '../api/client';
import ResultDisplay from './ResultDisplay';

const { Option } = Select;

const ImageUploader = () => {
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState([]);
  const [mode, setMode] = useState('balanced');
  const [recognitionMode, setRecognitionMode] = useState(() => {
    return localStorage.getItem('recognitionMode') || 'barcode_only';
  });
  const [sortOrder, setSortOrder] = useState('top_to_bottom');
  const [result, setResult] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const resultRef = useRef(null);
  const [aiStreamText, setAiStreamText] = useState(''); // AI流式输出文本
  const [aiStarted, setAiStarted] = useState(false); // AI是否开始输出

  // 保存识别模式设置
  useEffect(() => {
    localStorage.setItem('recognitionMode', recognitionMode);
    // 纯条码识别自动切换到极速模式
    if (recognitionMode === 'barcode_only' && mode !== 'fast') {
      setMode('fast');
    }
  }, [recognitionMode]);

  // 监听AI开始输出,立即滚动到底部
  useEffect(() => {
    if (aiStarted && resultRef.current) {
      resultRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end'
      });
    }
  }, [aiStarted]);

  // 监听AI流式输出,自动滚动到底部
  useEffect(() => {
    if (aiStreamText && recognitionMode === 'ai' && resultRef.current) {
      resultRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end'
      });
    }
  }, [aiStreamText, recognitionMode]);

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择图像文件');
      return;
    }

    setLoading(true);
    setResult(null);
    setAiStreamText('');
    setAiStarted(false);

    const formData = new FormData();
    formData.append('image', fileList[0].originFileObj);
    formData.append('mode', mode);
    formData.append('recognition_mode', recognitionMode);
    formData.append('sort_order', sortOrder);
    formData.append('ocr_mode', 'local');
    formData.append('return_image', 'false');

    try {
      // AI模式使用流式 API
      if (recognitionMode === 'ai') {
        // 立即滚动到结果区看到图像
        setTimeout(() => {
          if (resultRef.current) {
            resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 100);

        let isFirstChunk = true;
        await processSingleImageStream(formData, (chunk) => {
          if (isFirstChunk) {
            // 第一个数据块到达，标记AI开始输出
            setAiStarted(true);
            isFirstChunk = false;
          }
          setAiStreamText(prev => prev + chunk);
        });
        
        // 识别完成后再次确保滚动到底部
        setTimeout(() => {
          if (resultRef.current) {
            resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
          }
        }, 200);
        
        message.success('AI识别完成');
      } else {
        // 其他模式使用普通 API
        const response = await processSingleImage(formData);
        
        if (response.success) {
          setResult(response.data);
          message.success('识别完成');
        } else {
          message.error('识别失败: ' + response.message);
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      message.error('请求失败: ' + (error.response?.data?.detail || error.message));
      setAiStreamText('');
      setAiStarted(false);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = ({ fileList: newFileList }) => {
    setFileList(newFileList);
    setResult(null);
    
    // 生成预览URL
    if (newFileList.length > 0) {
      const file = newFileList[0].originFileObj;
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const uploadProps = {
    fileList,
    onChange: handleFileChange,
    beforeUpload: () => false, // 阻止自动上传
    accept: 'image/*',
    maxCount: 1
  };

  return (
    <div style={{ padding: '20px' }}>
      <Card title="图像上传与参数设置" style={{ marginBottom: '20px' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>选择图像文件</Button>
          </Upload>

          <Space wrap>
            <span>识别模式:</span>
            <Select
              value={recognitionMode}
              onChange={setRecognitionMode}
              style={{ width: 150 }}
            >
              <Option value="barcode_only">纯条码识别</Option>
              <Option value="ocr_only">OCR识别</Option>
              <Option value="barcode_and_ocr">OCR&条码</Option>
              <Option value="ai">AI识别</Option>
            </Select>
            {recognitionMode !== 'barcode_only' && recognitionMode !== 'ai' && (
              <span style={{ color: '#ff9800', fontSize: '13px' }}>
                ⚠️ OCR识别建议使用"均衡"或"完整"模式
              </span>
            )}

            {/* 非AI模式显示处理模式 */}
            {recognitionMode !== 'ai' && (
              <>
                <span>处理模式:</span>
                <Select
                  value={mode}
                  onChange={setMode}
                  style={{ width: 150 }}
                  disabled={recognitionMode === 'barcode_only'}
                >
                  <Option value="fast">极速模式</Option>
                  <Option value="balanced">均衡模式</Option>
                  <Option value="full">完整模式</Option>
                </Select>
              </>
            )}

            {/* 非AI模式显示排序方式 */}
            {recognitionMode !== 'ai' && (
              <>
                <span>排序方式:</span>
                <Select
                  value={sortOrder}
                  onChange={setSortOrder}
                  style={{ width: 150 }}
                >
                  <Option value="reading_order">阅读顺序</Option>
                  <Option value="top_to_bottom">从上到下</Option>
                  <Option value="left_to_right">从左到右</Option>
                </Select>
              </>
            )}
          </Space>

          <Button
            type="primary"
            onClick={handleUpload}
            loading={loading}
            disabled={fileList.length === 0}
            size="large"
          >
            {loading ? '识别中...' : '开始识别'}
          </Button>
        </Space>
      </Card>

      {loading && recognitionMode !== 'ai' && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" spinning={true}>
            <div style={{ padding: '50px' }}>正在识别,请稍候...</div>
          </Spin>
        </div>
      )}

      {/* AI模式的图像和结果区域 */}
      {recognitionMode === 'ai' && (previewUrl || aiStreamText) && (
        <div ref={resultRef}>
          {previewUrl && (
            <Card title="图像预览" style={{ marginBottom: '20px' }}>
              <img
                src={previewUrl}
                alt="Preview"
                style={{ maxWidth: '100%', maxHeight: '500px', display: 'block', margin: '0 auto' }}
              />
            </Card>
          )}

          {aiStreamText && (
            <Card 
              title="AI识别结果" 
              style={{ marginBottom: '20px' }}
              styles={{ body: { padding: '24px' } }}
            >
              <div style={{
                background: '#f5f5f5',
                padding: '16px',
                borderRadius: '4px',
                maxHeight: '600px',
                overflow: 'auto'
              }}>
                <pre style={{
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                  fontSize: '14px',
                  fontFamily: 'monospace',
                  lineHeight: '1.6'
                }}>
                  {aiStreamText}
                </pre>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* 非AI模式的图像预览 */}
      {recognitionMode !== 'ai' && previewUrl && (
        <Card title="图像预览" style={{ marginBottom: '20px' }}>
          <img
            src={previewUrl}
            alt="Preview"
            style={{ maxWidth: '100%', maxHeight: '500px', display: 'block', margin: '0 auto' }}
          />
        </Card>
      )}

      {/* 非AI模式的结果显示 */}
      {result && recognitionMode !== 'ai' && <div ref={resultRef}><ResultDisplay result={result} /></div>}
    </div>
  );
};

export default ImageUploader;
