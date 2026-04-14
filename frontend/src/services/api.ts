import axios from 'axios';
import type { ConversationFlow, FlowBlock, FlowConnection, FlowTemplate } from '@/types/flow';

const API_BASE_URL = '/api/flows';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const flowApi = {
  // Flow operations
  async getAllFlows(): Promise<ConversationFlow[]> {
    const response = await api.get('');
    return response.data;
  },

  async getFlow(id: number): Promise<ConversationFlow> {
    const response = await api.get(`/${id}`);
    return response.data;
  },

  async createFlow(flow: Partial<ConversationFlow>): Promise<ConversationFlow> {
    const response = await api.post('', flow);
    return response.data;
  },

  async updateFlow(id: number, flow: Partial<ConversationFlow>): Promise<ConversationFlow> {
    const response = await api.put(`/${id}`, flow);
    return response.data;
  },

  async deleteFlow(id: number): Promise<void> {
    await api.delete(`/${id}`);
  },

  async activateFlow(id: number): Promise<ConversationFlow> {
    const response = await api.patch(`/${id}/activate`);
    return response.data;
  },

  // Block operations
  async createBlock(flowId: number, block: Partial<FlowBlock>): Promise<FlowBlock> {
    const response = await api.post(`/${flowId}/blocks`, block);
    return response.data;
  },

  async updateBlock(blockId: number, block: Partial<FlowBlock>): Promise<FlowBlock> {
    const response = await api.put(`/blocks/${blockId}`, block);
    return response.data;
  },

  async deleteBlock(blockId: number): Promise<void> {
    await api.delete(`/blocks/${blockId}`);
  },

  // Connection operations
  async getConnections(flowId: number): Promise<FlowConnection[]> {
    const response = await api.get(`/${flowId}/connections`);
    return response.data;
  },

  async createConnection(
    flowId: number,
    connection: Partial<FlowConnection>
  ): Promise<FlowConnection> {
    const response = await api.post(`/${flowId}/connections`, connection);
    return response.data;
  },

  async deleteConnection(connectionId: number): Promise<void> {
    await api.delete(`/connections/${connectionId}`);
  },
};

// Templates API
export const templatesApi = {
  async getAllTemplates(): Promise<FlowTemplate[]> {
    const response = await axios.get('/api/templates/');
    return response.data;
  },

  async createTemplate(
    template: Omit<FlowTemplate, 'id' | 'created_at'>
  ): Promise<FlowTemplate> {
    const response = await axios.post('/api/templates/', template);
    return response.data;
  },

  async deleteTemplate(templateId: number): Promise<void> {
    await axios.delete(`/api/templates/${templateId}`);
  },
};

export default api;
