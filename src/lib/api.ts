/**
 * API utility functions for communicating with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
  errorDetails?: unknown;
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
          ...(options.headers || {}),
        },
        ...options,
      });

      // Try to parse JSON for both success and error responses
      const contentType = response.headers.get("content-type") || "";
      const isJson = contentType.includes("application/json");

      if (!response.ok) {
        let parsed: any = undefined;
        let text: string | undefined = undefined;
        try {
          parsed = isJson ? await response.json() : undefined;
        } catch {
          try {
            text = await response.text();
          } catch {
            // ignore
          }
        }

        const detail = parsed?.detail || parsed?.message || parsed?.error || text;
        const errorMessage = `HTTP ${response.status}${detail ? `: ${detail}` : ""}`;

        return {
          error: errorMessage,
          status: response.status,
          errorDetails: parsed ?? text,
        };
      }

      if (isJson) {
        const data = await response.json();
        return {
          data,
          status: response.status,
        };
      }

      // Fallback for non-JSON success
      const text = await response.text();
      return {
        data: text as unknown as T,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Unknown error occurred",
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

  // Versions (formerly artifacts)
  async listVersions(planId: string): Promise<ApiResponse<any[]>> {
    return this.request(`/api/plans/${planId}/versions`);
  }

  // Keep old method for backwards compatibility
  async listArtifacts(planId: string): Promise<ApiResponse<any[]>> {
    return this.listVersions(planId);
  }

  async updatePlanVersion(
    planId: string,
    version: number,
    payload: { content?: any }
  ): Promise<ApiResponse<any>> {
    return this.request(`/api/plans/${planId}/versions/${version}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
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

  // Business logic - plan generation with streaming
  generatePlan(
    planId: string,
    payload: {
      user_message: string;
      plan_artifact?: any;
      chat_messages?: any[];
    },
    onMessage: (data: any) => void,
    onError: (error: any) => void,
    onComplete: () => void
  ): () => void {
    const url = `${this.baseUrl}/api/business/plans/${planId}/generate`;

    // Make the POST request and handle the streaming response
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Hint server that we expect an event stream
        "Accept": "text/event-stream",
      },
      body: JSON.stringify(payload),
    })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = ""; // Buffer to hold partial SSE frames across reads

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            // Flush any trailing buffered event if present
            if (buffer.trim().length > 0) {
              const events = buffer.split('\n\n');
              for (const evt of events) {
                const dataLine = evt.split('\n').find((l) => l.startsWith('data:'));
                if (!dataLine) continue;
                const jsonStr = dataLine.slice(5).trim().replace(/^:\s*/, '');
                if (!jsonStr) continue;
                try {
                  const data = JSON.parse(jsonStr);
                  if (data.type === 'complete') {
                    onComplete();
                    return;
                  } else if (data.type === 'error') {
                    onError(new Error(data.message));
                    return;
                  } else {
                    onMessage(data);
                  }
                } catch (parseError) {
                  // Ignore final partial parse errors
                }
              }
            }
            break;
          }

          // Append decoded content to buffer (use streaming decode to avoid breaking multi-byte chars)
          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE events separated by two newlines
          let sepIndex: number;
          while ((sepIndex = buffer.indexOf('\n\n')) !== -1) {
            const eventBlock = buffer.slice(0, sepIndex);
            buffer = buffer.slice(sepIndex + 2);

            // Join all data lines (support multi-line data per SSE spec)
            const dataLines = eventBlock
              .split('\n')
              .filter((l) => l.startsWith('data:'))
              .map((l) => l.slice(5).trimStart());

            if (dataLines.length === 0) continue;
            const jsonPayload = dataLines.join('\n').trim();
            if (!jsonPayload) continue;

            try {
              const data = JSON.parse(jsonPayload);
              if (data.type === 'complete') {
                onComplete();
                return;
              } else if (data.type === 'error') {
                onError(new Error(data.message));
                return;
              } else {
                onMessage(data);
              }
            } catch (err) {
              console.warn('Failed to parse SSE event:', jsonPayload, err);
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    })
    .catch(onError);

    // Return a cleanup function
    return () => {
      // In a real implementation, you might want to track and cancel the fetch
      console.log('Cleanup called for plan generation');
    };
  }
}

// Export a default instance
export const apiClient = new ApiClient();

export const { healthCheck } = apiClient;
