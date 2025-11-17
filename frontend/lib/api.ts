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
}

export const api = new ApiClient();
