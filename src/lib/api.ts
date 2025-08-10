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

  // Users API
  async getUsers(): Promise<ApiResponse<any[]>> {
    return this.request("/api/users");
  }

  async createUser(userData: {
    username: string;
    email: string;
  }): Promise<ApiResponse> {
    return this.request("/api/users", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async getUser(userId: number): Promise<ApiResponse> {
    return this.request(`/api/users/${userId}`);
  }

  // Messages API
  async getMessages(): Promise<ApiResponse<any[]>> {
    return this.request("/api/messages");
  }

  async createMessage(message: string): Promise<ApiResponse> {
    return this.request("/api/messages", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  }

  // Stats API
  async getStats(): Promise<ApiResponse> {
    return this.request("/api/stats");
  }
}

// Export a default instance
export const apiClient = new ApiClient();

// Export individual functions for convenience
export const {
  healthCheck,
  getUsers,
  createUser,
  getUser,
  getMessages,
  createMessage,
  getStats,
} = apiClient;
