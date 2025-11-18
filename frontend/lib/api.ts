import axios, { AxiosInstance } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add token to requests
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Error handling and retry logic
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Retry logic for network errors
        if (!error.response && !originalRequest._retry) {
          originalRequest._retry = true;
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

          // Max 3 retries
          if (originalRequest._retryCount <= 3) {
            // Exponential backoff: 1s, 2s, 4s
            const delay = Math.pow(2, originalRequest._retryCount - 1) * 1000;
            await new Promise((resolve) => setTimeout(resolve, delay));
            return this.client(originalRequest);
          }
        }

        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          this.clearToken();
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
        }

        // Handle 429 Rate Limiting
        if (error.response?.status === 429 && !originalRequest._retry) {
          originalRequest._retry = true;
          const retryAfter = error.response.headers["retry-after"] || 5;
          await new Promise((resolve) => setTimeout(resolve, retryAfter * 1000));
          return this.client(originalRequest);
        }

        return Promise.reject(error);
      }
    );

    // Load token from localStorage
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("auth_token");
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }

  getToken() {
    return this.token;
  }

  // Auth endpoints
  async authenticateTelegram(initData: string) {
    const response = await this.client.post("/api/auth/telegram", {
      init_data: initData,
    });
    this.setToken(response.data.access_token);
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get("/api/auth/me");
    return response.data;
  }

  async logout() {
    const response = await this.client.post("/api/auth/logout");
    this.clearToken();
    return response.data;
  }

  // Projects endpoints
  async getProjects() {
    const response = await this.client.get("/api/projects");
    return response.data;
  }

  async getProject(id: string) {
    const response = await this.client.get(`/api/projects/${id}`);
    return response.data;
  }

  async createProject(data: {
    description: string;
    organization_id?: string;
  }) {
    const response = await this.client.post("/api/projects", data);
    return response.data;
  }

  async executeProject(id: string) {
    const response = await this.client.post(`/api/projects/${id}/execute`);
    return response.data;
  }

  async getProjectStatus(id: string) {
    const response = await this.client.get(`/api/projects/${id}/status`);
    return response.data;
  }

  async getProjectProgress(id: string) {
    const response = await this.client.get(`/api/projects/${id}/progress`);
    return response.data;
  }

  // Tasks endpoints
  async getProjectTasks(projectId: string) {
    const response = await this.client.get(`/api/tasks/project/${projectId}`);
    return response.data;
  }

  async getTask(id: string) {
    const response = await this.client.get(`/api/tasks/${id}`);
    return response.data;
  }

  async executeTask(id: string) {
    const response = await this.client.post(`/api/tasks/${id}/execute`);
    return response.data;
  }

  // Agents endpoints
  async getAgents() {
    const response = await this.client.get("/api/agents");
    return response.data;
  }

  async getAgent(type: string) {
    const response = await this.client.get(`/api/agents/${type}`);
    return response.data;
  }

  // HR Agent endpoints
  async getAgentPerformance(agentType?: string) {
    const url = agentType
      ? `/api/hr/agents/${agentType}/performance`
      : "/api/hr/agents/performance";
    const response = await this.client.get(url);
    return response.data;
  }

  async analyzeAgent(agentType: string) {
    const response = await this.client.post(`/api/hr/agents/${agentType}/analyze`);
    return response.data;
  }

  async suggestImprovements(agentType: string) {
    const response = await this.client.post(
      `/api/hr/agents/${agentType}/suggest-improvements`
    );
    return response.data;
  }

  async getImprovements() {
    const response = await this.client.get("/api/hr/improvements");
    return response.data;
  }

  async analyzeSkillGaps(data: { project_requirements: string[] }) {
    const response = await this.client.post("/api/hr/analyze-skill-gaps", data);
    return response.data;
  }

  async recruitAgent(data: {
    agent_type: string;
    name: string;
    skills: string[];
    description: string;
  }) {
    const response = await this.client.post("/api/hr/recruit-agent", data);
    return response.data;
  }

  async getDynamicAgents() {
    const response = await this.client.get("/api/hr/dynamic-agents");
    return response.data;
  }

  // Knowledge Base endpoints
  async searchKnowledge(data: {
    query: string;
    top_k?: number;
    content_type?: string;
    agent_type?: string;
    tags?: string[];
  }) {
    const response = await this.client.post("/api/knowledge/search", data);
    return response.data;
  }

  async storeKnowledge(data: {
    title: string;
    content: string;
    content_type: string;
    source_type?: string;
    source_id?: string;
    agent_type?: string;
    tags?: string[];
    metadata?: Record<string, any>;
  }) {
    const response = await this.client.post("/api/knowledge/store", data);
    return response.data;
  }

  async findSimilar(entryId: string, top_k?: number) {
    const response = await this.client.get(
      `/api/knowledge/similar/${entryId}`,
      { params: { top_k } }
    );
    return response.data;
  }

  async getAgentContext(data: {
    agent_type: string;
    query: string;
    top_k?: number;
  }) {
    const response = await this.client.post("/api/knowledge/context", data);
    return response.data;
  }

  async suggestSimilarProjects(data: {
    project_description: string;
    top_k?: number;
  }) {
    const response = await this.client.post(
      "/api/knowledge/suggest-projects",
      data
    );
    return response.data;
  }

  async getKnowledgeStats() {
    const response = await this.client.get("/api/knowledge/stats");
    return response.data;
  }
}

export const api = new ApiClient();
