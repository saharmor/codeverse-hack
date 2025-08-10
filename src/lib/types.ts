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
