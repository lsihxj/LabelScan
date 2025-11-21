import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Switch, 
  Select, 
  Space, 
  Divider, 
  message,
  Modal,
  InputNumber,
  Collapse,
  Tag
} from 'antd';
import { 
  PlusOutlined, 
  DeleteOutlined, 
  EditOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { TextArea } = Input;

const AIConfigManager = () => {
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState(null);
  const [editingProvider, setEditingProvider] = useState(null);
  const [editingModel, setEditingModel] = useState(null);
  const [providerModalVisible, setProviderModalVisible] = useState(false);
  const [modelModalVisible, setModelModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [modelForm] = Form.useForm();

  const API_BASE = 'http://localhost:8000';

  // 加载配置
  const loadConfig = async (skipLoading = false) => {
    try {
      if (!skipLoading) setLoading(true);
      console.log('开始加载配置...');
      const response = await axios.get(`${API_BASE}/api/v1/ai/config`);
      console.log('加载配置响应:', response.data);
      if (response.data.success) {
        setConfig(response.data.data);
        console.log('配置已更新到state:', response.data.data);
      }
    } catch (error) {
      console.error('加载配置错误:', error);
      message.error('加载配置失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      if (!skipLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  // 调试: 监听config变化
  useEffect(() => {
    console.log('config state 已更新:', config);
  }, [config]);

  // 保存配置
  const saveConfig = async (updatedConfig) => {
    try {
      setLoading(true);
      console.log('保存配置:', updatedConfig);
      const response = await axios.put(`${API_BASE}/api/v1/ai/config`, updatedConfig);
      console.log('保存响应:', response.data);
      if (response.data.success) {
        message.success('配置保存成功');
        // 重新加载配置,但不显示loading
        await loadConfig(true);
      } else {
        message.error('保存失败: ' + (response.data.message || '未知错误'));
      }
    } catch (error) {
      console.error('保存配置失败:', error);
      message.error('保存配置失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 启用/禁用AI
  const toggleAI = (enabled) => {
    saveConfig({
      ...config,
      enabled
    });
  };

  // 编辑提供商
  const editProvider = (provider) => {
    setEditingProvider(provider);
    form.setFieldsValue(provider);
    setProviderModalVisible(true);
  };

  // 添加/更新提供商
  const handleProviderOk = async () => {
    try {
      const values = await form.validateFields();
      const providers = [...(config.providers || [])];
      
      if (editingProvider) {
        // 更新
        const index = providers.findIndex(p => p.id === editingProvider.id);
        providers[index] = { ...editingProvider, ...values };
      } else {
        // 添加 - 确保enabled字段有默认值
        providers.push({
          id: values.id,
          name: values.name,
          api_base: values.api_base,
          api_key: values.api_key,
          enabled: values.enabled !== undefined ? values.enabled : false
        });
      }
      
      await saveConfig({
        ...config,
        providers
      });
      
      setProviderModalVisible(false);
      setEditingProvider(null);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // 删除提供商
  const deleteProvider = (providerId) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个提供商吗?',
      onOk: async () => {
        const providers = [...(config.providers || [])].filter(p => p.id !== providerId);
        await saveConfig({
          ...config,
          providers
        });
      }
    });
  };

  // 编辑模型
  const editModel = (model) => {
    setEditingModel(model);
    modelForm.setFieldsValue(model);
    setModelModalVisible(true);
  };

  // 添加新模型
  const addModel = () => {
    setEditingModel(null);
    modelForm.resetFields();
    setModelModalVisible(true);
  };

  // 添加/更新模型
  const handleModelOk = async () => {
    try {
      const values = await modelForm.validateFields();
      const models = [...(config.models || [])];
      
      if (editingModel) {
        // 更新
        const index = models.findIndex(m => m.id === editingModel.id);
        models[index] = { ...editingModel, ...values, active: editingModel.active };
      } else {
        // 添加
        models.push({
          id: values.id,
          name: values.name,
          provider_id: values.provider_id,
          model_name: values.model_name,
          temperature: values.temperature,
          max_tokens: values.max_tokens,
          system_prompt: values.system_prompt,
          user_prompt: values.user_prompt,
          active: false
        });
      }
      
      await saveConfig({
        ...config,
        models
      });
      
      setModelModalVisible(false);
      setEditingModel(null);
      modelForm.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // 删除模型
  const deleteModel = (modelId) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个模型吗?',
      onOk: async () => {
        const models = [...(config.models || [])].filter(m => m.id !== modelId);
        await saveConfig({
          ...config,
          models,
          active_model_id: config.active_model_id === modelId ? null : config.active_model_id
        });
      }
    });
  };

  // 激活模型
  const activateModel = async (modelId) => {
    await saveConfig({
      ...config,
      active_model_id: modelId
    });
  };

  if (!config) {
    return <Card loading={true}>加载中...</Card>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <Card title="AI识别配置" extra={
        <Switch 
          checked={config.enabled} 
          onChange={toggleAI}
          checkedChildren="已启用"
          unCheckedChildren="已禁用"
        />
      }>
        <Collapse 
          defaultActiveKey={['1', '2']} 
          style={{ marginBottom: '20px' }}
          items={[
            {
              key: '1',
              label: 'AI提供商配置',
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  {console.log('渲染提供商列表, providers:', config.providers)}
                  {config.providers && config.providers.length > 0 ? (
                    config.providers.map(provider => (
                      <Card 
                        key={provider.id}
                        size="small"
                        title={
                          <Space>
                            {provider.name}
                            {provider.enabled && <Tag color="green">已启用</Tag>}
                          </Space>
                        }
                        extra={
                          <Space>
                            <Button size="small" icon={<EditOutlined />} onClick={() => editProvider(provider)}>
                              编辑
                            </Button>
                            <Button 
                              size="small" 
                              danger 
                              icon={<DeleteOutlined />} 
                              onClick={() => deleteProvider(provider.id)}
                            >
                              删除
                            </Button>
                          </Space>
                        }
                      >
                        <p><strong>ID:</strong> {provider.id}</p>
                        <p><strong>API地址:</strong> {provider.api_base}</p>
                        <p><strong>API Key:</strong> {provider.api_key ? '●●●●●●●●' : '未设置'}</p>
                      </Card>
                    ))
                  ) : (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
                      暂无提供商,请点击下方按钮添加
                    </div>
                  )}
                  <Button type="dashed" block icon={<PlusOutlined />} onClick={() => {
                    setEditingProvider(null);
                    form.resetFields();
                    // 设置默认值
                    form.setFieldsValue({
                      enabled: false
                    });
                    setProviderModalVisible(true);
                  }}>
                    添加提供商
                  </Button>
                </Space>
              )
            },
            {
              key: '2',
              label: '模型配置',
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  {config.models && config.models.map(model => (
                    <Card 
                      key={model.id}
                      size="small"
                      title={
                        <Space>
                          {model.name}
                          {config.active_model_id === model.id && (
                            <Tag color="blue" icon={<CheckCircleOutlined />}>已激活</Tag>
                          )}
                        </Space>
                      }
                      extra={
                        <Space>
                          {config.active_model_id !== model.id && (
                            <Button 
                              size="small" 
                              type="primary"
                              onClick={() => activateModel(model.id)}
                            >
                              激活
                            </Button>
                          )}
                          <Button size="small" icon={<EditOutlined />} onClick={() => editModel(model)}>
                            编辑
                          </Button>
                          <Button 
                            size="small" 
                            danger 
                            icon={<DeleteOutlined />} 
                            onClick={() => deleteModel(model.id)}
                          >
                            删除
                          </Button>
                        </Space>
                      }
                    >
                      <p><strong>模型名称:</strong> {model.model_name}</p>
                      <p><strong>提供商:</strong> {model.provider_id}</p>
                      <p><strong>温度:</strong> {model.temperature}</p>
                      <p><strong>Max Tokens:</strong> {model.max_tokens}</p>
                    </Card>
                  ))}
                  <Button type="dashed" block icon={<PlusOutlined />} onClick={addModel}>
                    添加模型
                  </Button>
                </Space>
              )
            }
          ]}
        />

        {!config.enabled && (
          <div style={{ padding: '20px', background: '#fff3cd', borderRadius: '4px', marginTop: '20px' }}>
            <ExclamationCircleOutlined style={{ color: '#856404', marginRight: '8px' }} />
            <span style={{ color: '#856404' }}>
              AI识别功能当前已禁用,请启用后才能使用AI识别模式
            </span>
          </div>
        )}
      </Card>

      {/* 提供商编辑模态框 */}
      <Modal
        title={editingProvider ? "编辑提供商" : "添加提供商"}
        open={providerModalVisible}
        onOk={handleProviderOk}
        onCancel={() => {
          setProviderModalVisible(false);
          setEditingProvider(null);
          form.resetFields();
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="id" label="ID" rules={[{ required: true }]}>
            <Input disabled={!!editingProvider} />
          </Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="api_base" label="API地址" rules={[{ required: true }]}>
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" rules={[{ required: true }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 模型编辑模态框 */}
      <Modal
        title={editingModel ? "编辑模型" : "添加模型"}
        open={modelModalVisible}
        onOk={handleModelOk}
        onCancel={() => {
          setModelModalVisible(false);
          setEditingModel(null);
          modelForm.resetFields();
        }}
        width={700}
      >
        <Form form={modelForm} layout="vertical">
          <Form.Item name="id" label="ID" rules={[{ required: true }]}>
            <Input disabled={!!editingModel} />
          </Form.Item>
          <Form.Item name="name" label="显示名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="provider_id" label="提供商" rules={[{ required: true }]}>
            <Select>
              {config.providers && config.providers.map(p => (
                <Option key={p.id} value={p.id}>{p.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="model_name" label="模型名称" rules={[{ required: true }]}>
            <Input placeholder="gpt-4-vision-preview" />
          </Form.Item>
          <Form.Item name="temperature" label="温度参数" rules={[{ required: true }]}>
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="max_tokens" label="Max Tokens" rules={[{ required: true }]}>
            <InputNumber min={1} max={32000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="system_prompt" label="系统提示词" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="你是一个专业的图像识别助手..." />
          </Form.Item>
          <Form.Item name="user_prompt" label="用户提示词" rules={[{ required: true }]}>
            <TextArea rows={5} placeholder="请识别图片中的所有条形码和文字..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AIConfigManager;
