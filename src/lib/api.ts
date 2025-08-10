/**
 * API utility functions for communicating with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        return {
          error: `HTTP error! status: ${response.status}`,
          status: response.status,
        };
      }

      const data = await response.json();
      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error:
          error instanceof Error ? error.message : "Unknown error occurred",
        status: 0,
      };
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse> {
    return this.request("/health");
  }

  // Repositories
  async listRepositories(): Promise<ApiResponse<any[]>> {
    return this.request("/api/repositories");
  }

  async createRepository(payload: {
    name: string;
    path: string;
    git_url?: string | null;
    default_branch?: string;
  }): Promise<ApiResponse<any>> {
    return this.request("/api/repositories", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async deleteRepository(repoId: string): Promise<ApiResponse> {
    return this.request(`/api/repositories/${repoId}`, { method: "DELETE" });
  }

  // Plans
  async listPlans(repoId: string): Promise<ApiResponse<any[]>> {
    return this.request(`/api/repositories/${repoId}/plans`);
  }

  async createPlan(
    repoId: string,
    payload: {
      name: string;
      description?: string | null;
      target_branch: string;
      version?: number;
      status?: string;
    }
  ): Promise<ApiResponse<any>> {
    return this.request(`/api/repositories/${repoId}/plans`, {
      method: "POST",
      body: JSON.stringify({ ...payload, repository_id: repoId }),
    });
  }

  async deletePlan(planId: string): Promise<ApiResponse> {
    return this.request(`/api/plans/${planId}`, { method: "DELETE" });
  }

  async getPlan(planId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/plans/${planId}`);
  }

  // Artifacts
  async listArtifacts(planId: string): Promise<ApiResponse<any[]>> {
    return this.request(`/api/plans/${planId}/artifacts`);
  }

  // Chat
  async getPlanChat(planId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/plans/${planId}/chat`);
  }

  async createPlanChat(
    planId: string,
    payload?: { messages?: any[]; status?: string }
  ): Promise<ApiResponse<any>> {
    return this.request(`/api/plans/${planId}/chat`, {
      method: "POST",
      body: JSON.stringify({ plan_id: planId, ...(payload || {}) }),
    });
  }

  async updateChat(
    chatId: string,
    payload: { messages?: any[]; status?: string }
  ): Promise<ApiResponse<any>> {
    return this.request(`/api/chat/${chatId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }
}

// Export a default instance
export const apiClient = new ApiClient();

export const { healthCheck } = apiClient;
