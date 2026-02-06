"use client";

import Link from "next/link";
import type { FeedItem } from "@/lib/api";

function formatTime(ts: number) {
  const d = new Date(ts * 1000);
  const now = Date.now();
  const diff = (now - d.getTime()) / 1000;
  if (diff < 60) return "now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

export default function PostCard({
  item,
  currentUserId,
  onEngage,
  showExplain,
}: {
  item: FeedItem;
  currentUserId: string;
  onEngage: (postId: string, type: string) => void;
  showExplain: boolean;
}) {
  const { post, ranking_explanation, parent_post, quoted_post } = item;
  const author = post.author;
  const initial = (author?.display_name ?? author?.handle ?? "?").charAt(0).toUpperCase();

  return (
    <article className="tweet-card">
      <Link href={`/profile/${post.author_id}`} className="tweet-avatar" title={author?.handle}>
        {initial}
      </Link>
      <div className="tweet-body">
        <div className="tweet-header" style={{ justifyContent: "space-between", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", flexWrap: "wrap" }}>
            <Link href={`/profile/${post.author_id}`} style={{ color: "#e7e9ea", textDecoration: "none", fontWeight: 700 }}>
              {author?.display_name ?? "?"}
            </Link>
            <span className="time">@{author?.handle ?? post.author_id}</span>
            <span className="time">· {formatTime(post.created_at)}</span>
            {ranking_explanation && (
              <span
                style={{
                  fontSize: "0.75rem",
                  color: ranking_explanation.source === "in_network" ? "#00ba7c" : "#1d9bf0",
                  background: "#1a1a1a",
                  padding: "0.15rem 0.35rem",
                  borderRadius: "4px",
                }}
              >
                {ranking_explanation.source === "in_network" ? "Following" : "For you"}
              </span>
            )}
          </div>
        </div>
        {parent_post && (
          <p className="time" style={{ margin: "0.15rem 0 0.35rem", fontSize: "0.9rem" }}>
            Replying to <Link href={`/profile/${parent_post.author_id}`} style={{ color: "#1d9bf0" }}>@{parent_post.author?.handle ?? parent_post.author_id}</Link>
          </p>
        )}
        {quoted_post && (
          <div style={{ marginBottom: "0.5rem", padding: "0.5rem", border: "1px solid #2f3336", borderRadius: "8px", background: "#16181c" }}>
            <div className="time" style={{ fontSize: "0.85rem", marginBottom: "0.25rem" }}>
              <strong>{quoted_post.author?.display_name ?? "?"}</strong> @{quoted_post.author?.handle ?? quoted_post.author_id}
            </div>
            <p style={{ margin: 0, whiteSpace: "pre-wrap", fontSize: "0.95rem" }}>{quoted_post.text}</p>
          </div>
        )}
        <p style={{ margin: "0.35rem 0", whiteSpace: "pre-wrap" }}>{post.text}</p>
        {post.topics?.length > 0 && (
          <div style={{ marginBottom: "0.35rem" }}>
            {post.topics.map((t: string) => (
              <span key={t} className="trend-tag">#{t}</span>
            ))}
          </div>
        )}
        <div className="tweet-actions">
          <button type="button" onClick={() => onEngage(post.id, "reply")} title="Reply">💬 {post.reply_count || ""}</button>
          <button type="button" onClick={() => onEngage(post.id, "repost")} title="Repost">↻ {post.repost_count || ""}</button>
          <button type="button" onClick={() => onEngage(post.id, "like")} title="Like">♥ {post.like_count || ""}</button>
        </div>
        {showExplain && ranking_explanation && (
          <div className="explain" style={{ marginTop: "0.5rem" }}>
            <strong>Why this post:</strong> rank #{ranking_explanation.rank}, score {ranking_explanation.final_score.toFixed(2)}
            {ranking_explanation.diversity_penalty !== 0 && ` · diversity ${ranking_explanation.diversity_penalty.toFixed(2)}`}
            {ranking_explanation.recency_boost > 0 && ` · recency ${ranking_explanation.recency_boost.toFixed(2)}`}
          </div>
        )}
      </div>
    </article>
  );
}
