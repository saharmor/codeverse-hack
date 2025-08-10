export type Project = {
  id: string;
  name: string;
  path?: string;
  lastUpdated?: string;
  icon?: "folder" | "dashboard";
};

export type MessageRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
};

export type Repository = {
  id: string;
  name: string;
  path: string;
  gitUrl?: string | null;
  defaultBranch: string;
  createdAt?: string;
  updatedAt?: string;
};

export type PlanStatus = "draft" | "active" | "completed" | "archived";

export type Plan = {
  id: string;
  repositoryId: string;
  name: string;
  description?: string | null;
  targetBranch: string;
  version: number;
  status: PlanStatus;
  createdAt?: string;
  updatedAt?: string;
};

export type ArtifactType =
  | "feature_plan"
  | "implementation_steps"
  | "code_changes";

export type PlanArtifact = {
  id: string;
  planId: string;
  content: Record<string, any>;
  artifactType: ArtifactType;
  createdAt: string;
};

export type ChatStatus = "active" | "completed";

export type ChatSession = {
  id: string;
  planId: string;
  messages: Array<{
    role: MessageRole | string;
    content: string;
    timestamp?: string | number | null;
  }>;
  status: ChatStatus;
  createdAt?: string;
  updatedAt?: string;
};
