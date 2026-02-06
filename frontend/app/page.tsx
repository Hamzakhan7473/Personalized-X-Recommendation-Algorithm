"use client";

import { useEffect, useState } from "react";
import {
  getFeed,
  getPreferences,
  putPreferences,
  engage,
  getTrends,
  type FeedItem as FeedItemType,
  type AlgorithmPreferences,
} from "@/lib/api";

const DEFAULT_USER_ID = "u0";

function formatTime(ts: number) {
  const d = new Date(ts * 1000);
  const now = Date.now();
  const diff = (now - d.getTime()) / 1000;
  if (diff < 60) return "now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

function PostCard({
  item,
  currentUserId,
  onEngage,
  showExplain,
}: {
  item: FeedItemType;
  currentUserId: string;
  onEngage: (postId: string, type: string) => void;
  showExplain: boolean;
}) {
  const { post, ranking_explanation } = item;
  const author = post.author;

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <strong>{author?.display_name ?? "?"}</strong>
          <span className="time" style={{ marginLeft: "0.5rem" }}>
            @{author?.handle ?? post.author_id} · {formatTime(post.created_at)}
          </span>
        </div>
        {ranking_explanation && (
          <span
            style={{
              fontSize: "0.75rem",
              color: ranking_explanation.source === "in_network" ? "#00ba7c" : "#1d9bf0",
              background: "#1a1a1a",
              padding: "0.2rem 0.4rem",
              borderRadius: "4px",
            }}
          >
            {ranking_explanation.source === "in_network" ? "Following" : "For you"}
          </span>
        )}
      </div>
      <p style={{ margin: "0.5rem 0", whiteSpace: "pre-wrap" }}>{post.text}</p>
      {post.topics?.length > 0 && (
        <div style={{ marginBottom: "0.5rem" }}>
          {post.topics.map((t: string) => (
            <span key={t} className="trend-tag">
              #{t}
            </span>
          ))}
        </div>
      )}
      <div className="engagement-bar">
        <button type="button" onClick={() => onEngage(post.id, "like")}>
          ♥ {post.like_count}
        </button>
        <button type="button" onClick={() => onEngage(post.id, "repost")}>
          ↻ {post.repost_count}
        </button>
        <button type="button" onClick={() => onEngage(post.id, "reply")}>
          ↩ {post.reply_count}
        </button>
      </div>
      {showExplain && ranking_explanation && (
        <div className="explain">
          <strong>Why this post:</strong> rank #{ranking_explanation.rank}, score {ranking_explanation.final_score.toFixed(2)}
          {ranking_explanation.diversity_penalty !== 0 && ` · diversity penalty ${ranking_explanation.diversity_penalty.toFixed(2)}`}
          {ranking_explanation.recency_boost > 0 && ` · recency boost ${ranking_explanation.recency_boost.toFixed(2)}`}
        </div>
      )}
    </div>
  );
}

function PreferenceSliders({
  prefs,
  onChange,
  onSave,
}: {
  prefs: AlgorithmPreferences;
  onChange: (p: AlgorithmPreferences) => void;
  onSave: () => void;
}) {
  const update = (key: keyof AlgorithmPreferences, value: number) => {
    onChange({ ...prefs, [key]: value });
  };

  return (
    <div className="card" style={{ marginBottom: "1rem" }}>
      <h3 style={{ marginTop: 0 }}>Algorithm preferences</h3>
      <div className="slider-row">
        <label>Recency vs popularity</label>
        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={prefs.recency_vs_popularity}
          onChange={(e) => update("recency_vs_popularity", parseFloat(e.target.value))}
        />
        <span>{prefs.recency_vs_popularity.toFixed(1)}</span>
      </div>
      <div className="slider-row">
        <label>Friends vs global</label>
        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={prefs.friends_vs_global}
          onChange={(e) => update("friends_vs_global", parseFloat(e.target.value))}
        />
        <span>{prefs.friends_vs_global.toFixed(1)}</span>
      </div>
      <div className="slider-row">
        <label>Diversity strength</label>
        <input
          type="range"
          min={0}
          max={1}
          step={0.1}
          value={prefs.diversity_strength}
          onChange={(e) => update("diversity_strength", parseFloat(e.target.value))}
        />
        <span>{prefs.diversity_strength.toFixed(1)}</span>
      </div>
      <button type="button" onClick={onSave}>
        Save & refresh feed
      </button>
    </div>
  );
}

export default function Home() {
  const [feed, setFeed] = useState<FeedItemType[]>([]);
  const [trends, setTrends] = useState<{ topic: string; count: number }[]>([]);
  const [prefs, setPrefs] = useState<AlgorithmPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showExplain, setShowExplain] = useState(true);
  const userId = DEFAULT_USER_ID;

  const loadFeed = async () => {
    try {
      setError(null);
      const res = await getFeed(userId, true);
      setFeed(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load feed");
    } finally {
      setLoading(false);
    }
  };

  const loadPrefs = async () => {
    try {
      const p = await getPreferences(userId);
      setPrefs(p);
    } catch {
      setPrefs({
        recency_vs_popularity: 0.3,
        friends_vs_global: 0.4,
        niche_vs_viral: 0.5,
        tech_weight: 0.2,
        politics_weight: 0.2,
        culture_weight: 0.2,
        memes_weight: 0.2,
        finance_weight: 0.2,
        diversity_strength: 0.6,
        exploration: 0.3,
        negative_signal_strength: 0.8,
      });
    }
  };

  const loadTrends = async () => {
    try {
      const t = await getTrends();
      setTrends(t);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadFeed();
    loadPrefs();
    loadTrends();
  }, []);

  const handleSavePrefs = async () => {
    if (!prefs) return;
    try {
      await putPreferences(userId, prefs);
      await loadFeed();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save preferences");
    }
  };

  const handleEngage = async (postId: string, type: string) => {
    try {
      await engage(userId, postId, type);
      await loadFeed();
    } catch {
      // ignore
    }
  };

  if (loading && feed.length === 0) {
    return (
      <div className="container">
        <p>Loading feed…</p>
      </div>
    );
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: "0.5rem" }}>For You</h1>
      <p style={{ color: "#71767b", marginBottom: "1rem" }}>
        Viewing as <strong>@{userId}</strong>. Feed powered by the ranking pipeline.{" "}
        <a href="/users">People</a>
      </p>

      {error && (
        <div className="card" style={{ background: "#3a1a1a", borderColor: "#8b0000" }}>
          {error}. Is the backend running at {process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}?
        </div>
      )}

      {prefs && (
        <PreferenceSliders
          prefs={prefs}
          onChange={setPrefs}
          onSave={handleSavePrefs}
        />
      )}

      {trends.length > 0 && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h3 style={{ marginTop: 0 }}>Trending</h3>
          {trends.map(({ topic, count }) => (
            <span key={topic} className="trend-tag">
              #{topic} ({count})
            </span>
          ))}
        </div>
      )}

      <div style={{ marginBottom: "0.5rem" }}>
        <button
          type="button"
          className="secondary"
          onClick={() => setShowExplain(!showExplain)}
        >
          {showExplain ? "Hide" : "Show"} why this post
        </button>
      </div>

      {feed.length === 0 && !error && (
        <p>No posts in feed. Start the backend and seed data.</p>
      )}
      {feed.map((item) => (
        <PostCard
          key={item.post.id}
          item={item}
          currentUserId={userId}
          onEngage={handleEngage}
          showExplain={showExplain}
        />
      ))}
    </div>
  );
}
