export interface ConversationSummary {
  id: string;
  title: string;
  updatedAt: number;
}

export interface UserContext {
  id: string;
  username: string;
  role: "USER" | "MERCHANT" | "ADMIN";
  merchantId: string | null;
}

export interface RecommendationCard {
  id: string;
  name: string;
  location?: string;
  address?: string;
  type?: string;
  featured?: boolean;
  rating?: string;
  reviewCount?: number | null;
  priceLabel?: string;
  summary?: string;
  highlights?: string[];
  imageUrl?: string;
  detailUrl?: string;
  bookingUrl?: string;
  mapUrl?: string;
  followUpPrompt?: string;
}

export interface RecommendationsPayload {
  title?: string;
  subtitle?: string;
  count?: number;
  cards: RecommendationCard[];
}

export interface PendingActionSummary {
  action?: string;
  target_type?: string;
  target_id?: string | number;
  target_label?: string;
  current_status?: string;
  impact?: string;
  reason?: string;
  property_name?: string;
  booking_number?: string;
  confirmation_text?: string;
}

export interface PendingActionPayload {
  token: string;
  tool: string;
  arguments: Record<string, unknown>;
  expires_at: string;
  confirmation_text: string;
  summary?: PendingActionSummary;
}

export type ChatRole = "assistant" | "user";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
  recommendations?: RecommendationsPayload | null;
  pendingAction?: PendingActionPayload | null;
  error?: boolean;
}

export type AgentStepStatus = "pending" | "running" | "done" | "error";

export interface AgentStep {
  key: string;
  label: string;
  detail: string;
  status: AgentStepStatus;
}

export interface ToolLogItem {
  tool: string;
  label: string;
  status: "running" | "done" | "error";
  summary?: string;
}

export interface StreamRoute {
  skills: string[];
  tools: string[];
  systemPrompt: string | null;
}

export interface StreamMeta {
  conversationId?: string;
  route?: StreamRoute;
  requestId?: string;
}
