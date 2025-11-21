import React, { useState, useRef, useEffect } from 'react';
import { Button, Select, Space, Card, Spin, message, Modal, Radio } from 'antd';
import { CameraOutlined, FileImageOutlined, CloseOutlined, RotateLeftOutlined, RotateRightOutlined } from '@ant-design/icons';
import { processSingleImage, processSingleImageStream } from '../api/client';
import ResultDisplay from './ResultDisplay';

const { Option } = Select;

const MobileUploader = () => {
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('balanced');
  const [recognitionMode, setRecognitionMode] = useState(() => {
    // 仏localStorage读取上次选择的识别模式
    return localStorage.getItem('recognitionMode') || 'barcode_only';
  });
  const [sortOrder, setSortOrder] = useState('top_to_bottom');
  const [result, setResult] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [stream, setStream] = useState(null);
  const [rotationAngle, setRotationAngle] = useState(() => {
    // 从 localStorage 读取上次选择的旋转角度
    return localStorage.getItem('cameraRotation') || '0';
  });
  
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const resultAreaRef = useRef(null); // 用于滚动到加载动画
  const resultDisplayRef = useRef(null); // 用于滚动到识别结果
  const [aiStreamText, setAiStreamText] = useState(''); // AI流式输出文本
  const [aiStarted, setAiStarted] = useState(false); // AI是否开始输出
  
  // 保存旋转角度设置
  useEffect(() => {
    localStorage.setItem('cameraRotation', rotationAngle);
  }, [rotationAngle]);

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
    if (aiStarted && resultDisplayRef.current) {
      resultDisplayRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end'
      });
    }
  }, [aiStarted]);

  // 监听AI流式输出,自动滚动到底部
  useEffect(() => {
    if (aiStreamText && recognitionMode === 'ai' && resultDisplayRef.current) {
      resultDisplayRef.current.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end'
      });
    }
  }, [aiStreamText, recognitionMode]);

  // 当结果更新时自动滚动到结果区域(非AI模式)
  useEffect(() => {
    if (result && recognitionMode !== 'ai' && resultDisplayRef.current) {
      // 延迟一下再滚动,确保结果已经渲染完成
      setTimeout(() => {
        resultDisplayRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 200);
    }
  }, [result]);

  // 旋转图像
  const rotateImage = (canvas, angle) => {
    if (angle === '0') return canvas;

    const rotatedCanvas = document.createElement('canvas');
    const ctx = rotatedCanvas.getContext('2d');
    
    // 根据旋转角度设置画布尺寸
    if (angle === '90' || angle === '-90') {
      rotatedCanvas.width = canvas.height;
      rotatedCanvas.height = canvas.width;
    } else {
      rotatedCanvas.width = canvas.width;
      rotatedCanvas.height = canvas.height;
    }

    // 移动到中心点
    ctx.translate(rotatedCanvas.width / 2, rotatedCanvas.height / 2);
    
    // 旋转
    ctx.rotate((angle * Math.PI) / 180);
    
    // 绘制图像
    ctx.drawImage(canvas, -canvas.width / 2, -canvas.height / 2);
    
    return rotatedCanvas;
  };

  // 处理图像上传和识别
  const processImage = async (file) => {
    setLoading(true);
    setResult(null);
    setAiStreamText('');
    setAiStarted(false);

    // AI模式立即滚动到结果区看到图像
    if (recognitionMode === 'ai') {
      setTimeout(() => {
        if (resultDisplayRef.current) {
          resultDisplayRef.current.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          });
        }
      }, 100);
    } else {
      // 非AI模式滚动到loading动画
      setTimeout(() => {
        if (resultAreaRef.current) {
          resultAreaRef.current.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          });
        }
      }, 100);
    }

    const formData = new FormData();
    formData.append('image', file);
    formData.append('mode', mode);
    formData.append('recognition_mode', recognitionMode);
    formData.append('sort_order', sortOrder);
    formData.append('ocr_mode', 'local');
    formData.append('return_image', 'false');

    try {
      // AI模式使用流式 API
      if (recognitionMode === 'ai') {
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
          if (resultDisplayRef.current) {
            resultDisplayRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
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

  // 从相册选择
  const handleAlbumSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setResult(null);
      processImage(file);
    }
  };

  // 打开相机
  const openCamera = async () => {
    // 检查浏览器兼容性
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      message.error('您的浏览器不支持摄像头访问,请使用相册选择功能');
      return;
    }

    // 检查是否为HTTPS或localhost
    const isSecureContext = window.isSecureContext;
    if (!isSecureContext && window.location.hostname !== 'localhost') {
      message.warning('摄像头功能需要HTTPS协议,建议使用相册选择功能');
      // 仍然尝试访问,某些浏览器可能允许
    }

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment', // 后置摄像头
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      setStream(mediaStream);
      setShowCamera(true);
      
      // 等待 modal 显示后再设置 video src
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      }, 100);
    } catch (error) {
      console.error('Camera error:', error);
      let errorMsg = '无法访问摄像头';
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMsg = '摄像头权限被拒绝,请在浏览器设置中允许访问摄像头';
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        errorMsg = '未检测到摄像头设备';
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        errorMsg = '摄像头正被其他应用占用';
      } else if (error.name === 'OverconstrainedError') {
        errorMsg = '无法满足摄像头参数要求';
      } else if (error.name === 'SecurityError') {
        errorMsg = '摄像头访问被安全策略阻止,请使用HTTPS访问或使用相册选择';
      }
      
      message.error(errorMsg);
    }
  };

  // 关闭相机
  const closeCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setShowCamera(false);
  };

  // 拍照
  const takePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    // 设置 canvas 尺寸与视频一致
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // 绘制当前帧
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // 如果不旋转,裁剪图片(只保留中间60%的高度)
    let finalCanvas = canvas;
    if (rotationAngle === '0') {
      const croppedCanvas = document.createElement('canvas');
      const croppedCtx = croppedCanvas.getContext('2d');
      
      // 计算裁剪区域 - 保留中间60%的高度
      const cropHeight = Math.floor(canvas.height * 0.6);
      const cropY = Math.floor((canvas.height - cropHeight) / 2);
      
      croppedCanvas.width = canvas.width;
      croppedCanvas.height = cropHeight;
      
      // 从原canvas中裁剪中间部分
      croppedCtx.drawImage(
        canvas,
        0, cropY, canvas.width, cropHeight,  // 源区域
        0, 0, canvas.width, cropHeight       // 目标区域
      );
      
      finalCanvas = croppedCanvas;
    } else {
      // 旋转图像
      finalCanvas = rotateImage(canvas, rotationAngle);
    }

    // 转换为 blob 并处理
    finalCanvas.toBlob((blob) => {
      const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      
      setPreviewUrl(url);
      setResult(null);
      closeCamera();
      processImage(file);
    }, 'image/jpeg', 0.95);
  };

  // 清除预览
  const clearPreview = () => {
    setPreviewUrl(null);
    setResult(null);
  };

  return (
    <div style={{ padding: '16px', maxWidth: '100%' }}>
      <Card 
        title="电子标签识别" 
        style={{ marginBottom: '16px' }}
        bodyStyle={{ padding: '16px' }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* 参数设置 */}
          <div>
            <div style={{ marginBottom: '8px', fontSize: '14px', color: '#666' }}>
              识别模式:
            </div>
            <Select
              value={recognitionMode}
              onChange={setRecognitionMode}
              style={{ width: '100%' }}
              size="large"
            >
              <Option value="barcode_only">纯条码识别</Option>
              <Option value="ocr_only">OCR识别</Option>
              <Option value="barcode_and_ocr">OCR&条码</Option>
              <Option value="ai">AI识别</Option>
            </Select>
            {recognitionMode !== 'barcode_only' && recognitionMode !== 'ai' && (
              <div style={{ 
                marginTop: '6px', 
                fontSize: '12px', 
                color: '#ff9800',
                padding: '4px 8px',
                background: '#fff3e0',
                borderRadius: '4px'
              }}>
                提示: OCR识别使用"均衡"或"完整"模式效果更佳
              </div>
            )}
          </div>

          {/* 非AI模式显示处理模式 */}
          {recognitionMode !== 'ai' && (
            <div>
              <div style={{ marginBottom: '8px', fontSize: '14px', color: '#666' }}>
                处理模式:
              </div>
              <Select
                value={mode}
                onChange={setMode}
                style={{ width: '100%' }}
                size="large"
                disabled={recognitionMode === 'barcode_only'}
              >
                <Option value="fast">极速模式</Option>
                <Option value="balanced">均衡模式</Option>
                <Option value="full">完整模式</Option>
              </Select>
            </div>
          )}

          {/* 非AI模式显示排序方式 */}
          {recognitionMode !== 'ai' && (
            <div>
              <div style={{ marginBottom: '8px', fontSize: '14px', color: '#666' }}>
                排序方式:
              </div>
              <Select
                value={sortOrder}
                onChange={setSortOrder}
                style={{ width: '100%' }}
                size="large"
              >
                <Option value="top_to_bottom">从上到下</Option>
                <Option value="reading_order">阅读顺序</Option>
                <Option value="left_to_right">从左到右</Option>
              </Select>
            </div>
          )}

          {/* 拍照旋转角度 */}
          <div>
            <div style={{ marginBottom: '8px', fontSize: '14px', color: '#666' }}>
              拍照后旋转:
            </div>
            <Radio.Group 
              value={rotationAngle} 
              onChange={(e) => setRotationAngle(e.target.value)}
              style={{ width: '100%' }}
              size="large"
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Radio value="0" style={{ fontSize: '15px' }}>
                  不旋转
                </Radio>
                <Radio value="-90" style={{ fontSize: '15px' }}>
                  <RotateLeftOutlined /> 向左旋转90°
                </Radio>
                <Radio value="90" style={{ fontSize: '15px' }}>
                  <RotateRightOutlined /> 向右旋转90°
                </Radio>
              </Space>
            </Radio.Group>
          </div>

          {/* 拍照和相册按钮 - 移动到参数下方 */}
          <div style={{ 
            borderTop: '1px solid #f0f0f0',
            paddingTop: '16px',
            marginTop: '8px'
          }}>
            <Space style={{ width: '100%', justifyContent: 'center' }} size="middle">
              <Button
                type="primary"
                icon={<CameraOutlined />}
                size="large"
                onClick={openCamera}
                style={{ flex: 1, height: '48px', fontSize: '16px' }}
              >
                拍照识别
              </Button>
              <Button
                type="default"
                icon={<FileImageOutlined />}
                size="large"
                onClick={() => fileInputRef.current?.click()}
                style={{ flex: 1, height: '48px', fontSize: '16px' }}
              >
                相册选择
              </Button>
            </Space>
          </div>

          {/* 隐藏的文件选择input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleAlbumSelect}
          />
        </Space>
      </Card>

      {/* 加载状态 - 添加ref用于滚动定位,AI模式不显示 */}
      <div ref={resultAreaRef}>
        {loading && recognitionMode !== 'ai' && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="正在识别,请稍候..." />
          </div>
        )}
      </div>

      {/* AI模式的图像和结果区域 */}
      {recognitionMode === 'ai' && (previewUrl || aiStreamText) && (
        <div ref={resultDisplayRef}>
          {previewUrl && (
            <Card 
              title="图像预览" 
              style={{ marginBottom: '16px' }}
              extra={
                <Button 
                  type="text" 
                  icon={<CloseOutlined />} 
                  onClick={clearPreview}
                />
              }
            >
              <img
                src={previewUrl}
                alt="Preview"
                style={{ 
                  width: '100%', 
                  height: 'auto',
                  display: 'block',
                  borderRadius: '4px'
                }}
              />
            </Card>
          )}

          {aiStreamText && (
            <Card 
              title="AI识别结果" 
              style={{ marginBottom: '16px' }}
              styles={{ body: { padding: '12px' } }}
            >
              <div style={{
                background: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                maxHeight: '500px',
                overflow: 'auto'
              }}>
                <pre style={{
                  margin: 0,
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                  fontSize: '13px',
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
      {recognitionMode !== 'ai' && previewUrl && !loading && (
        <Card 
          title="图像预览" 
          style={{ marginBottom: '16px' }}
          extra={
            <Button 
              type="text" 
              icon={<CloseOutlined />} 
              onClick={clearPreview}
            />
          }
        >
          <img
            src={previewUrl}
            alt="Preview"
            style={{ 
              width: '100%', 
              height: 'auto',
              display: 'block',
              borderRadius: '4px'
            }}
          />
        </Card>
      )}

      {/* 非AI模式的结果显示 */}
      {result && recognitionMode !== 'ai' && (
        <div ref={resultDisplayRef}>
          <ResultDisplay result={result} />
        </div>
      )}

      {/* 相机模态框 */}
      <Modal
        open={showCamera}
        onCancel={closeCamera}
        footer={null}
        width="100%"
        style={{ 
          top: 0, 
          maxWidth: '100vw',
          padding: 0,
          margin: 0
        }}
        bodyStyle={{ 
          padding: 0,
          height: rotationAngle === '0' ? '48vh' : '80vh',
          display: 'flex',
          flexDirection: 'column',
          maxHeight: '90vh'
        }}
        destroyOnClose
      >
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column',
          background: '#000',
          height: '100%'
        }}>
          <div style={{
            flex: 1,
            overflow: 'hidden',
            position: 'relative'
          }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ 
                width: '100%',
                height: '100%',
                objectFit: rotationAngle === '0' ? 'cover' : 'contain',
                objectPosition: 'center'
              }}
            />
          </div>
          <div style={{ 
            padding: '12px',
            background: '#000',
            display: 'flex',
            justifyContent: 'center',
            gap: '12px'
          }}>
            <Button
              type="primary"
              size="large"
              onClick={takePhoto}
              style={{ 
                width: '100px',
                height: '44px',
                fontSize: '16px'
              }}
            >
              拍照
            </Button>
            <Button
              size="large"
              onClick={closeCamera}
              style={{ 
                width: '100px',
                height: '44px',
                fontSize: '16px'
              }}
            >
              取消
            </Button>
          </div>
        </div>
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </Modal>
    </div>
  );
};

export default MobileUploader;
