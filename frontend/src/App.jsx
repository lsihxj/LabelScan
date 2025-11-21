import React, { useState, useEffect } from 'react';
import { Layout, Typography, Space, Tabs } from 'antd';
import { BarcodeOutlined, MobileOutlined, DesktopOutlined, SettingOutlined, RobotOutlined } from '@ant-design/icons';
import ImageUploader from './components/ImageUploader';
import MobileUploader from './components/MobileUploader';
import AIConfigManager from './components/AIConfigManager';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

function App() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // 检测是否为移动设备
    const checkMobile = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const mobileKeywords = ['android', 'iphone', 'ipad', 'ipod', 'mobile'];
      const isMobileDevice = mobileKeywords.some(keyword => userAgent.includes(keyword));
      const isSmallScreen = window.innerWidth <= 768;
      
      setIsMobile(isMobileDevice || isSmallScreen);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 移动版布局
  if (isMobile) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <Header style={{ 
          background: '#1890ff',
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          height: '56px'
        }}>
          <Space size="small">
            <BarcodeOutlined style={{ fontSize: '24px', color: '#fff' }} />
            <Title level={4} style={{ margin: 0, color: '#fff' }}>
              标签识别
            </Title>
          </Space>
        </Header>
        
        <Content style={{ 
          padding: '0',
          background: '#f5f5f5',
          overflow: 'auto'
        }}>
          <MobileUploader />
        </Content>
      </Layout>
    );
  }

  // 桌面版布局
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 50px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        display: 'flex',
        alignItems: 'center'
      }}>
        <Space size="middle">
          <BarcodeOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            电子标签多条码识别系统
          </Title>
        </Space>
      </Header>
      
      <Content style={{ 
        padding: '24px 50px',
        background: '#f0f2f5'
      }}>
        <div style={{ 
          background: '#fff', 
          padding: '24px',
          borderRadius: '8px',
          minHeight: '500px'
        }}>
          <Tabs defaultActiveKey="1" items={[
            {
              key: '1',
              label: (
                <span>
                  <BarcodeOutlined />
                  图像识别
                </span>
              ),
              children: <ImageUploader />
            },
            {
              key: '2',
              label: (
                <span>
                  <RobotOutlined />
                  AI配置
                </span>
              ),
              children: <AIConfigManager />
            }
          ]} />
        </div>
      </Content>
      
      <Footer style={{ textAlign: 'center' }}>
        电子标签多条码识别系统 ©2025 | 支持多条码识别、文字提取、智能排序
      </Footer>
    </Layout>
  );
}

export default App;
