const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const sid = localStorage.getItem("session_id");
  return sid ? { Authorization: `Bearer ${sid}` } : {};
}

export interface User {
  id: string;
  handle: string;
  display_name: string;
  bio: string;
  topics: string[];
  following_ids: string[];
  followers_count: number;
  following_count: number;
}

export interface Post {
  id: string;
  author_id: string;
  text: string;
  post_type: string;
  topics: string[];
  created_at: number;
  like_count: number;
  repost_count: number;
  reply_count: number;
  quote_count: number;
  view_count: number;
}

export interface PostWithAuthor extends Post {
  author: User | null;
}

export interface ActionScore {
  action: string;
  weight: number;
  probability: number;
  contribution: number;
}

export interface RankingExplanation {
  post_id: string;
  final_score: number;
  rank: number;
  source: string;
  action_scores: ActionScore[];
  diversity_penalty: number;
  recency_boost: number;
  topic_boost: number;
}

export interface FeedItem {
  post: PostWithAuthor;
  ranking_explanation: RankingExplanation | null;
  parent_post?: PostWithAuthor | null;
  quoted_post?: PostWithAuthor | null;
}

export interface FeedResponse {
  items: FeedItem[];
  next_cursor: string | null;
}

export interface AlgorithmPreferences {
  recency_vs_popularity: number;
  friends_vs_global: number;
  niche_vs_viral: number;
  tech_weight: number;
  politics_weight: number;
  culture_weight: number;
  memes_weight: number;
  finance_weight: number;
  diversity_strength: number;
  exploration: number;
  negative_signal_strength: number;
}

async function apiError(res: Response): Promise<never> {
  let msg: string;
  try {
    const data = await res.json();
    msg = typeof data.detail === "string" ? data.detail : res.statusText || "Request failed";
  } catch {
    msg = await res.text() || res.statusText || "Request failed";
  }
  throw new Error(msg);
}

export async function login(handle: string): Promise<{ user: User; session_id: string }> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ handle: handle.trim() }),
  });
  if (!res.ok) await apiError(res);
  return res.json();
}

export async function getMe(): Promise<User> {
  const res = await fetch(`${API_URL}/api/auth/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getFeed(userId: string, includeExplanations = true, followingOnly = false): Promise<FeedResponse> {
  const params = new URLSearchParams({ limit: "50", include_explanations: String(includeExplanations) });
  if (followingOnly) params.set("following_only", "true");
  const res = await fetch(`${API_URL}/api/feed/${userId}?${params}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUserPosts(userId: string, limit = 50): Promise<FeedResponse> {
  const res = await fetch(`${API_URL}/api/users/${userId}/posts?limit=${limit}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPreferences(userId: string): Promise<AlgorithmPreferences> {
  const res = await fetch(`${API_URL}/api/users/${userId}/preferences`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function putPreferences(userId: string, preferences: AlgorithmPreferences): Promise<AlgorithmPreferences> {
  const res = await fetch(`${API_URL}/api/users/${userId}/preferences`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ preferences }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function engage(userId: string, postId: string, engagementType: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/engage`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ user_id: userId, post_id: postId, engagement_type: engagementType }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function createPost(authorId: string, text: string, topics: string[] = []): Promise<Post> {
  const res = await fetch(`${API_URL}/api/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ author_id: authorId, text: text.slice(0, 280), topics }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUsers(): Promise<User[]> {
  const res = await fetch(`${API_URL}/api/users?limit=100`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.users || [];
}

export async function getTrends(): Promise<{ topic: string; count: number }[]> {
  const res = await fetch(`${API_URL}/api/trends?limit=10`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.trends || [];
}

export async function follow(userId: string, targetId: string): Promise<User> {
  const res = await fetch(`${API_URL}/api/users/${userId}/follow`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ target_id: targetId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function unfollow(userId: string, targetId: string): Promise<User> {
  const res = await fetch(`${API_URL}/api/users/${userId}/unfollow`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ target_id: targetId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export interface NotificationItem {
  id: string;
  notification_type: string;
  actor: User | null;
  post_id: string | null;
  post_preview: string | null;
  created_at: number;
}

export async function getNotifications(limit = 50): Promise<NotificationItem[]> {
  const res = await fetch(`${API_URL}/api/notifications?limit=${limit}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.notifications || [];
}

// -------- Real-time LLM (OpenAI / Gemini) --------
export async function getLlmStatus(): Promise<{ available: boolean }> {
  const res = await fetch(`${API_URL}/api/llm/status`, { headers: authHeaders() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generatePost(userId: string, publish: boolean): Promise<{ text: string; post_id?: string }> {
  const res = await fetch(`${API_URL}/api/llm/generate-post`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ user_id: userId, publish }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function generateReply(userId: string, postId: string): Promise<{ text: string }> {
  const res = await fetch(`${API_URL}/api/llm/generate-reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ user_id: userId, post_id: postId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
