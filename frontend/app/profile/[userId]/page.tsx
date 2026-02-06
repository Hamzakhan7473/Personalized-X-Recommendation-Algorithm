"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { getMe, getUsers, getUserPosts, getTrends, follow, unfollow, engage, type User, type FeedItem as FeedItemType } from "@/lib/api";
import XLayout from "@/components/XLayout";
import PostCard from "@/components/PostCard";

function formatTime(ts: number) {
  const d = new Date(ts * 1000);
  const now = Date.now();
  const diff = (now - d.getTime()) / 1000;
  if (diff < 60) return "now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

export default function ProfilePage() {
  const router = useRouter();
  const params = useParams();
  const userIdParam = typeof params.userId === "string" ? params.userId : "";
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [profileUser, setProfileUser] = useState<User | null>(null);
  const [posts, setPosts] = useState<FeedItemType[]>([]);
  const [trends, setTrends] = useState<{ topic: string; count: number }[]>([]);
  const [whoToFollow, setWhoToFollow] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [following, setFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  const viewerId = currentUser?.id ?? "";
  const profileUserId = userIdParam === "me" ? viewerId : userIdParam;

  useEffect(() => {
    const sid = typeof window !== "undefined" ? localStorage.getItem("session_id") : null;
    if (!sid) {
      router.replace("/login");
      return;
    }
    getMe()
      .then((u) => {
        setCurrentUser(u);
        if (userIdParam === "me" && u?.id) setProfileUser(u);
      })
      .catch(() => {
        localStorage.removeItem("session_id");
        localStorage.removeItem("user");
        router.replace("/login");
      });
  }, [router, userIdParam]);

  useEffect(() => {
    if (!profileUserId || !currentUser) return;
    if (profileUserId === currentUser.id) {
      setProfileUser(currentUser);
      setFollowing(false);
    } else {
      getUsers().then((users) => {
        const u = users.find((x) => x.id === profileUserId);
        if (u) {
          setProfileUser(u);
          setFollowing(currentUser.following_ids?.includes(u.id) ?? false);
        }
        setWhoToFollow(users.filter((x) => x.id !== currentUser.id && !currentUser.following_ids?.includes(x.id)));
      }).catch(() => {});
    }
  }, [profileUserId, currentUser]);

  useEffect(() => {
    if (!profileUserId) return;
    getUserPosts(profileUserId)
      .then((r) => setPosts(r.items))
      .catch(() => setPosts([]))
      .finally(() => setLoading(false));
  }, [profileUserId]);

  useEffect(() => {
    getTrends().then(setTrends).catch(() => {});
  }, []);

  const handleFollow = async () => {
    if (!currentUser || !profileUser || profileUser.id === currentUser.id || followLoading) return;
    setFollowLoading(true);
    try {
      if (following) {
        await unfollow(currentUser.id, profileUser.id);
        setFollowing(false);
        setProfileUser((u) => u && { ...u, followers_count: Math.max(0, u.followers_count - 1) });
      } else {
        await follow(currentUser.id, profileUser.id);
        setFollowing(true);
        setProfileUser((u) => u && { ...u, followers_count: u.followers_count + 1 });
      }
    } finally {
      setFollowLoading(false);
    }
  };

  const handleEngage = async (postId: string, type: string) => {
    if (!viewerId) return;
    try {
      await engage(viewerId, postId, type);
      const r = await getUserPosts(profileUserId);
      setPosts(r.items);
    } catch {
      // ignore
    }
  };

  if (!currentUser && !loading) return null;

  return (
    <XLayout currentUser={currentUser} trends={trends} whoToFollow={whoToFollow}>
      <div style={{ padding: "1rem", borderBottom: "1px solid #2f3336" }}>
        <Link href="/" className="time" style={{ display: "inline-block", marginBottom: "0.5rem" }}>← Back</Link>
        {profileUser ? (
          <>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem", flexWrap: "wrap" }}>
              <div className="tweet-avatar" style={{ width: 80, height: 80, fontSize: "2rem" }}>
                {(profileUser.display_name ?? profileUser.handle ?? "?").charAt(0).toUpperCase()}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h1 style={{ margin: "0 0 0.25rem", fontSize: "1.5rem" }}>{profileUser.display_name}</h1>
                <p className="time" style={{ margin: "0 0 0.5rem" }}>@{profileUser.handle}</p>
                {profileUser.bio && <p style={{ margin: "0 0 0.5rem" }}>{profileUser.bio}</p>}
                <p className="time" style={{ margin: 0 }}>
                  <strong style={{ color: "#e7e9ea" }}>{profileUser.followers_count}</strong> Followers
                  {" · "}
                  <strong style={{ color: "#e7e9ea" }}>{profileUser.following_count}</strong> Following
                </p>
                {profileUser.id !== currentUser?.id && (
                  <button type="button" className={following ? "secondary" : ""} onClick={handleFollow} disabled={followLoading} style={{ marginTop: "0.5rem" }}>
                    {followLoading ? "…" : following ? "Unfollow" : "Follow"}
                  </button>
                )}
              </div>
            </div>
          </>
        ) : (
          <p className="time">User not found.</p>
        )}
      </div>
      <div style={{ padding: "0 1rem 1rem" }}>
        {loading ? <p className="time">Loading posts…</p> : posts.length === 0 ? <p className="time">No posts yet.</p> : (
          posts.map((item) => (
            <PostCard key={item.post.id} item={item} currentUserId={viewerId} onEngage={handleEngage} showExplain={false} />
          ))
        )}
      </div>
    </XLayout>
  );
}
