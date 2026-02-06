"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  getFeed,
  getPreferences,
  putPreferences,
  engage,
  getTrends,
  createPost,
  getMe,
  getNotifications,
  getLlmStatus,
  generatePost as apiGeneratePost,
  getUsers,
  type FeedItem as FeedItemType,
  type AlgorithmPreferences,
  type User,
  type NotificationItem,
} from "@/lib/api";
import XLayout from "@/components/XLayout";
import PostCard from "@/components/PostCard";

/** Fallback user id (seed "me" user) when currentUser not yet loaded; do not use for authenticated actions. */
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

function PreferenceSliders({
  prefs,
  onChange,
  onSave,
}: {
  prefs: AlgorithmPreferences;
  onChange: (p: AlgorithmPreferences) => void;
  onSave: () => void;
}) {
  const [showMorePrefs, setShowMorePrefs] = useState(false);
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
      <div style={{ marginTop: "0.5rem" }}>
        <button type="button" className="secondary" onClick={() => setShowMorePrefs((s) => !s)} style={{ padding: "0.2rem 0.5rem", fontSize: "0.9rem" }}>
          {showMorePrefs ? "Hide" : "Show"} niche vs viral & topic weights
        </button>
      </div>
      {showMorePrefs && (
        <>
          <div className="slider-row">
            <label>Niche vs viral</label>
            <input type="range" min={0} max={1} step={0.1} value={prefs.niche_vs_viral} onChange={(e) => update("niche_vs_viral", parseFloat(e.target.value))} />
            <span>{prefs.niche_vs_viral.toFixed(1)}</span>
          </div>
          <div className="slider-row">
            <label>Tech weight</label>
            <input type="range" min={0} max={1} step={0.1} value={prefs.tech_weight} onChange={(e) => update("tech_weight", parseFloat(e.target.value))} />
            <span>{prefs.tech_weight.toFixed(1)}</span>
          </div>
          <div className="slider-row">
            <label>Politics weight</label>
            <input type="range" min={0} max={1} step={0.1} value={prefs.politics_weight} onChange={(e) => update("politics_weight", parseFloat(e.target.value))} />
            <span>{prefs.politics_weight.toFixed(1)}</span>
          </div>
          <div className="slider-row">
            <label>Culture weight</label>
            <input type="range" min={0} max={1} step={0.1} value={prefs.culture_weight} onChange={(e) => update("culture_weight", parseFloat(e.target.value))} />
            <span>{prefs.culture_weight.toFixed(1)}</span>
          </div>
          <div className="slider-row">
            <label>Memes weight</label>
            <input type="range" min={0} max={1} step={0.1} value={prefs.memes_weight} onChange={(e) => update("memes_weight", parseFloat(e.target.value))} />
            <span>{prefs.memes_weight.toFixed(1)}</span>
          </div>
          <div className="slider-row">
            <label>Finance weight</label>
            <input type="range" min={0} max={1} step={0.1} value={prefs.finance_weight} onChange={(e) => update("finance_weight", parseFloat(e.target.value))} />
            <span>{prefs.finance_weight.toFixed(1)}</span>
          </div>
        </>
      )}
      <button type="button" onClick={onSave} style={{ marginTop: "0.5rem" }}>
        Save & refresh feed
      </button>
    </div>
  );
}

const defaultPrefs: AlgorithmPreferences = {
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
};

export default function Home() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [feed, setFeed] = useState<FeedItemType[]>([]);
  const [trends, setTrends] = useState<{ topic: string; count: number }[]>([]);
  const [prefs, setPrefs] = useState<AlgorithmPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showExplain, setShowExplain] = useState(true);
  const [composeText, setComposeText] = useState("");
  const [posting, setPosting] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [loadingNotifications, setLoadingNotifications] = useState(false);
  const [llmAvailable, setLlmAvailable] = useState(false);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [whoToFollow, setWhoToFollow] = useState<User[]>([]);
  const [feedTab, setFeedTab] = useState<"for_you" | "following">("for_you");
  const [generateAsUserId, setGenerateAsUserId] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generatedPreview, setGeneratedPreview] = useState<string | null>(null);

  useEffect(() => {
    const sid = typeof window !== "undefined" ? localStorage.getItem("session_id") : null;
    if (!sid) {
      router.replace("/login");
      return;
    }
    const cached = typeof window !== "undefined" ? localStorage.getItem("user") : null;
    if (cached) {
      try {
        setCurrentUser(JSON.parse(cached));
      } catch {
        // ignore
      }
    }
    getMe()
      .then((u) => {
        setCurrentUser(u);
        if (typeof window !== "undefined") localStorage.setItem("user", JSON.stringify(u));
      })
      .catch(() => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("session_id");
          localStorage.removeItem("user");
        }
        router.replace("/login");
      });
  }, [router]);

  const userId = currentUser?.id ?? DEFAULT_USER_ID;

  const loadFeed = async (followingOnly = false) => {
    if (!userId) return;
    try {
      setError(null);
      const res = await getFeed(userId, true, followingOnly);
      setFeed(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load feed");
    } finally {
      setLoading(false);
    }
  };

  const loadPrefs = async () => {
    if (!userId) return;
    try {
      const p = await getPreferences(userId);
      setPrefs(p);
    } catch {
      setPrefs(defaultPrefs);
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

  const loadNotifications = async () => {
    setLoadingNotifications(true);
    try {
      const list = await getNotifications(30);
      setNotifications(list);
    } catch {
      setNotifications([]);
    } finally {
      setLoadingNotifications(false);
    }
  };

  useEffect(() => {
    if (!userId) return;
    loadFeed(feedTab === "following");
    loadPrefs();
    loadTrends();
    getLlmStatus().then((s) => setLlmAvailable(s.available)).catch(() => setLlmAvailable(false));
    getUsers().then((users) => {
      setAllUsers(users);
      const following = new Set(currentUser?.following_ids ?? []);
      setWhoToFollow(users.filter((u) => u.id !== userId && !following.has(u.id)));
    }).catch(() => setAllUsers([]));
  }, [userId, feedTab]);

  useEffect(() => {
    if (!currentUser || !allUsers.length) return;
    const following = new Set(currentUser.following_ids ?? []);
    setWhoToFollow(allUsers.filter((u) => u.id !== currentUser.id && !following.has(u.id)));
  }, [currentUser?.following_ids, currentUser?.id, allUsers]);

  const handleSavePrefs = async () => {
    if (!prefs || !userId) return;
    try {
      await putPreferences(userId, prefs);
      await loadFeed(feedTab === "following");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save preferences");
    }
  };

  const handleEngage = async (postId: string, type: string) => {
    try {
      await engage(userId, postId, type);
      await loadFeed(feedTab === "following");
    } catch {
      // ignore
    }
  };

  const handlePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId || !composeText.trim() || posting) return;
    setPosting(true);
    try {
      await createPost(userId, composeText.trim(), []);
      setComposeText("");
      await loadFeed(feedTab === "following");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to post");
    } finally {
      setPosting(false);
    }
  };

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("session_id");
      localStorage.removeItem("user");
    }
    router.replace("/login");
  };

  const handleGeneratePost = async (publish: boolean) => {
    const uid = generateAsUserId || allUsers[0]?.id;
    if (!uid || generating) return;
    setGenerating(true);
    setGeneratedPreview(null);
    setError(null);
    try {
      const result = await apiGeneratePost(uid, publish);
      setGeneratedPreview(result.text);
      if (publish && result.post_id) await loadFeed(feedTab === "following");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generate failed");
    } finally {
      setGenerating(false);
    }
  };

  if (!currentUser && !loading) return null;
  if (loading && feed.length === 0 && !error) {
    return (
      <XLayout currentUser={currentUser} trends={[]} whoToFollow={[]}>
        <div style={{ padding: "1rem" }}><p>Loading feed…</p></div>
      </XLayout>
    );
  }

  const toggleNotifications = () => {
    if (!notificationsOpen) loadNotifications();
    setNotificationsOpen((o) => !o);
  };

  const notificationLabel = (n: NotificationItem) => {
    const name = n.actor?.display_name ?? n.actor?.handle ?? "Someone";
    switch (n.notification_type) {
      case "like": return `${name} liked your post`;
      case "repost": return `${name} reposted your post`;
      case "reply": return `${name} replied to your post`;
      case "quote": return `${name} quoted your post`;
      case "follow": return `${name} followed you`;
      default: return `${name} — ${n.notification_type}`;
    }
  };

  return (
    <XLayout currentUser={currentUser} trends={trends} whoToFollow={whoToFollow}>
      <div className="x-feed-tabs">
        <button type="button" className={`x-feed-tab ${feedTab === "for_you" ? "active" : ""}`} onClick={() => { setFeedTab("for_you"); loadFeed(false); }}>For you</button>
        <button type="button" className={`x-feed-tab ${feedTab === "following" ? "active" : ""}`} onClick={() => { setFeedTab("following"); loadFeed(true); }}>Following</button>
      </div>
      <div style={{ padding: "0 1rem 1rem" }}>
        <p style={{ color: "#71767b", marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <span style={{ position: "relative", display: "inline-flex" }}>
            <button type="button" className="secondary" onClick={toggleNotifications} style={{ padding: "0.25rem 0.5rem" }} title="Notifications">🔔 {notifications.length > 0 ? `(${notifications.length})` : ""}</button>
            {notificationsOpen && (
              <div className="card" style={{ position: "absolute", top: "100%", left: 0, marginTop: "0.25rem", minWidth: "320px", maxWidth: "400px", maxHeight: "70vh", overflow: "auto", zIndex: 50 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}><strong>Notifications</strong><button type="button" className="secondary" onClick={() => setNotificationsOpen(false)} style={{ padding: "0.2rem 0.4rem" }}>Close</button></div>
                {loadingNotifications ? <p className="time">Loading…</p> : notifications.length === 0 ? <p className="time">No notifications yet.</p> : (
                  <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>{notifications.map((n) => (
                    <li key={n.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid #2f3336" }}><div className="time" style={{ marginBottom: "0.2rem" }}>{formatTime(n.created_at)}</div><div>{notificationLabel(n)}</div>{n.post_preview && <div style={{ fontSize: "0.9rem", color: "#71767b", marginTop: "0.25rem" }}>"{n.post_preview}"</div>}</li>
                  ))}</ul>
                )}
              </div>
            )}
          </span>
          <Link href="/profile/me">Profile</Link>
          <button type="button" className="secondary" onClick={handleLogout} style={{ padding: "0.25rem 0.5rem" }}>Log out</button>
        </p>

        <form onSubmit={handlePost} className="card" style={{ marginBottom: "1rem" }}>
        <textarea
          value={composeText}
          onChange={(e) => setComposeText(e.target.value)}
          placeholder="What's happening?"
          maxLength={280}
          rows={3}
          style={{
            width: "100%",
            padding: "0.75rem",
            borderRadius: "8px",
            border: "1px solid #2f3336",
            background: "#0a0a0a",
            color: "#e7e9ea",
            fontSize: "1rem",
            resize: "vertical",
            marginBottom: "0.5rem",
          }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="time">{composeText.length}/280</span>
          <button type="submit" disabled={posting || !composeText.trim()}>
            {posting ? "Posting…" : "Post"}
          </button>
        </div>
      </form>

      {llmAvailable && allUsers.length > 0 && (
        <div className="card" style={{ marginBottom: "1rem", background: "rgba(29, 155, 240, 0.08)", borderColor: "#1d9bf0" }}>
          <h3 style={{ marginTop: 0 }}>Real-time post (OpenAI / Gemini)</h3>
          <p style={{ color: "#71767b", fontSize: "0.9rem", marginBottom: "0.75rem" }}>
            Generate a tweet as another user and optionally add it to the feed so it appears for everyone.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
            <label>
              Post as:{" "}
              <select
                value={generateAsUserId || allUsers[0]?.id}
                onChange={(e) => setGenerateAsUserId(e.target.value)}
                style={{ marginLeft: "0.25rem", padding: "0.25rem", background: "#0a0a0a", color: "#e7e9ea", border: "1px solid #2f3336", borderRadius: "4px" }}
              >
                {allUsers.map((u) => (
                  <option key={u.id} value={u.id}>
                    @{u.handle} ({u.display_name})
                  </option>
                ))}
              </select>
            </label>
            <button type="button" onClick={() => handleGeneratePost(false)} disabled={generating}>
              {generating ? "Generating…" : "Preview"}
            </button>
            <button type="button" onClick={() => handleGeneratePost(true)} disabled={generating}>
              {generating ? "…" : "Generate & add to feed"}
            </button>
          </div>
          {generatedPreview && (
            <div style={{ marginTop: "0.5rem", padding: "0.5rem", background: "#1a1a1a", borderRadius: "6px", fontSize: "0.95rem" }}>
              {generatedPreview}
            </div>
          )}
        </div>
      )}

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
        <p>No posts in feed. Follow people or check the backend.</p>
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
    </XLayout>
  );
}
