import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Descriptions, Typography } from 'antd';
import { RobotOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const ResultDisplay = ({ result }) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (!result) return null;

  // 检查是否为AI识别模式
  const isAIMode = result.recognition_mode === 'ai';
  const hasAIResponse = result.ai_raw_response;

  const columns = [
    {
      title: '序号',
      dataIndex: 'order',
      key: 'order',
      width: isMobile ? 60 : 80,
      render: (order) => <Tag color="blue">#{order}</Tag>
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: isMobile ? 80 : 120,
      render: (type) => {
        const colorMap = {
          'barcode_group': 'green',
          'barcode': 'green',
          'text': 'orange'
        };
        const nameMap = {
          'barcode_group': '条码组',
          'barcode': '条码',
          'text': '独立文字'
        };
        return <Tag color={colorMap[type]}>{nameMap[type] || type}</Tag>;
      }
    },
    {
      title: '内容',
      dataIndex: 'data',
      key: 'data',
      render: (data, record) => {
        if (record.type === 'barcode_group' || record.type === 'barcode') {
          return (
            <div style={{ fontSize: isMobile ? '12px' : '14px' }}>
              <div><strong>条码:</strong> {data.barcode_data}</div>
              <div><strong>类型:</strong> {data.barcode_type}</div>
              {data.related_text && (
                <div><strong>关联文字:</strong> {data.related_text}</div>
              )}
            </div>
          );
        } else if (record.type === 'text') {
          return <div style={{ fontSize: isMobile ? '12px' : '14px' }}>{data.text}</div>;
        }
        return null;
      }
    },
    ...(!isMobile ? [{
      title: '位置',
      dataIndex: 'position',
      key: 'position',
      width: 200,
      render: (pos) => (
        <div style={{ fontSize: '12px' }}>
          <div>X: {pos.x}, Y: {pos.y}</div>
          <div>W: {pos.width}, H: {pos.height}</div>
        </div>
      )
    }] : [])
  ];

  const dataSource = result.results.map((item, index) => ({
    ...item,
    key: index
  }));

  return (
    <div>
      <Card 
        title="识别结果" 
        style={{ marginBottom: isMobile ? '16px' : '20px' }}
        styles={{ body: { padding: isMobile ? '12px' : '24px' } }}
      >
        <Descriptions bordered column={isMobile ? 1 : 2} size="small">
          <Descriptions.Item label="处理模式">
            <Tag color="purple">{result.mode_used}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="识别模式">
            <Tag color={isAIMode ? 'blue' : 'green'}>
              {result.recognition_mode === 'ai' ? 'AI识别' :
               result.recognition_mode === 'barcode_only' ? '纯条码识别' :
               result.recognition_mode === 'ocr_only' ? 'OCR识别' : 'OCR&条码'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="排序方式">
            <Tag color="cyan">{result.sort_order}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="处理耗时">
            {result.process_time} ms
          </Descriptions.Item>
          <Descriptions.Item label="识别数量">
            {result.results.length} 项
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {result.structured_fields && Object.keys(result.structured_fields).length > 0 && (
        <Card 
          title="结构化字段" 
          style={{ marginBottom: isMobile ? '16px' : '20px' }} 
          size="small"
          styles={{ body: { padding: isMobile ? '12px' : '24px' } }}
        >
          <Descriptions bordered column={1} size="small">
            {Object.entries(result.structured_fields).map(([key, value]) => (
              <Descriptions.Item label={key} key={key}>
                {value}
              </Descriptions.Item>
            ))}
          </Descriptions>
        </Card>
      )}

      {/* AI识别模式下显示单个Tab */}
      {isAIMode && hasAIResponse ? (
        <Card styles={{ body: { padding: isMobile ? '12px' : '24px' } }}>
          <div style={{ marginBottom: '16px' }}>
            <Tag color="blue" icon={<RobotOutlined />}>AI识别结果</Tag>
          </div>
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
              fontSize: isMobile ? '12px' : '14px',
              fontFamily: 'monospace',
              lineHeight: '1.6'
            }}>
              {typeof result.ai_raw_response === 'string' 
                ? result.ai_raw_response 
                : JSON.stringify(result.ai_raw_response, null, 2)}
            </pre>
          </div>
        </Card>
      ) : isAIMode ? (
        /* AI模式但没有响应数据 */
        <Card>
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            等待AI响应...
          </div>
        </Card>
      ) : (
        /* 非AI识别模式下直接显示表格 */
        <Card 
          title="详细结果列表"
          styles={{ body: { padding: isMobile ? '0' : '24px' } }}
        >
          <Table
            columns={columns}
            dataSource={dataSource}
            pagination={{ pageSize: isMobile ? 5 : 10 }}
            size={isMobile ? 'small' : 'middle'}
            scroll={isMobile ? { x: 'max-content' } : undefined}
          />
        </Card>
      )}

      {result.full_text && (
        <Card 
          title="全文识别结果" 
          style={{ marginTop: isMobile ? '16px' : '20px' }}
          styles={{ body: { padding: isMobile ? '12px' : '24px' } }}
        >
          <Paragraph style={{ whiteSpace: 'pre-wrap', fontSize: isMobile ? '12px' : '14px' }}>
            {result.full_text}
          </Paragraph>
        </Card>
      )}
    </div>
  );
};

export default ResultDisplay;