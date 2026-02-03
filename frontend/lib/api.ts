const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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

export async function getFeed(userId: string, includeExplanations = true): Promise<FeedResponse> {
  const res = await fetch(`${API_URL}/api/feed/${userId}?limit=50&include_explanations=${includeExplanations}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPreferences(userId: string): Promise<AlgorithmPreferences> {
  const res = await fetch(`${API_URL}/api/users/${userId}/preferences`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function putPreferences(userId: string, preferences: AlgorithmPreferences): Promise<AlgorithmPreferences> {
  const res = await fetch(`${API_URL}/api/users/${userId}/preferences`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preferences }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function engage(userId: string, postId: string, engagementType: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/engage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, post_id: postId, engagement_type: engagementType }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function getUsers(): Promise<User[]> {
  const res = await fetch(`${API_URL}/api/users?limit=100`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.users || [];
}

export async function getTrends(): Promise<{ topic: string; count: number }[]> {
  const res = await fetch(`${API_URL}/api/trends?limit=10`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.trends || [];
}

export async function follow(userId: string, targetId: string): Promise<User> {
  const res = await fetch(`${API_URL}/api/users/${userId}/follow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_id: targetId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function unfollow(userId: string, targetId: string): Promise<User> {
  const res = await fetch(`${API_URL}/api/users/${userId}/unfollow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_id: targetId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
