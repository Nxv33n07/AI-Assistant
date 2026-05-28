export type Denomination =
  | "catholic"
  | "protestant_reformed"
  | "protestant_evangelical"
  | "protestant_lutheran"
  | "orthodox_eastern"
  | "pentecostal"
  | "nondenominational";

export interface ScriptureRef {
  reference: string;
  text: string;
  translation: string;
  relevance: "direct" | "semantic";
}

export interface SafetyFlag {
  category: string;
  severity: "blocked" | "warned" | "redirected";
  message: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  scripture_references?: ScriptureRef[];
  corrections?: string[];
  safety_flag?: SafetyFlag | null;
  timestamp: Date;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  denomination: Denomination;
}

export interface ChatResponse {
  response: string;
  thinking?: string;
  scripture_references: ScriptureRef[];
  corrections: string[];
  safety_flag: SafetyFlag | null;
  session_id: string;
  denomination: string;
}

export interface ImageRequest {
  session_id: string;
  prompt: string;
  denomination: Denomination;
}

export interface ImageResponse {
  image_url: string | null;
  enhanced_prompt: string | null;
  safety_flag: SafetyFlag | null;
  session_id: string;
}

export const DENOMINATION_LABELS: Record<Denomination, string> = {
  nondenominational: "Non-denominational",
  catholic: "Catholic",
  protestant_reformed: "Reformed / Presbyterian",
  protestant_evangelical: "Evangelical Protestant",
  protestant_lutheran: "Lutheran",
  orthodox_eastern: "Eastern Orthodox",
  pentecostal: "Pentecostal / Charismatic",
};
