"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getUsers, follow, unfollow, type User } from "@/lib/api";

const DEFAULT_USER_ID = "u0";

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [following, setFollowing] = useState<Set<string>>(new Set());
  const currentUserId = DEFAULT_USER_ID;

  useEffect(() => {
    getUsers()
      .then((list) => {
        setUsers(list);
        const me = list.find((u) => u.id === currentUserId);
        if (me) setFollowing(new Set(me.following_ids));
      })
      .finally(() => setLoading(false));
  }, [currentUserId]);

  const handleFollow = async (targetId: string) => {
    if (targetId === currentUserId) return;
    try {
      await follow(currentUserId, targetId);
      setFollowing((prev) => new Set(Array.from(prev).concat(targetId)));
      setUsers((prev) =>
        prev.map((u) =>
          u.id === targetId ? { ...u, followers_count: u.followers_count + 1 } : u
        )
      );
    } catch {
      // ignore
    }
  };

  const handleUnfollow = async (targetId: string) => {
    try {
      await unfollow(currentUserId, targetId);
      setFollowing((prev) => {
        const next = new Set(prev);
        next.delete(targetId);
        return next;
      });
      setUsers((prev) =>
        prev.map((u) =>
          u.id === targetId ? { ...u, followers_count: Math.max(0, u.followers_count - 1) } : u
        )
      );
    } catch {
      // ignore
    }
  };

  if (loading) return <div className="container"><p>Loading users…</p></div>;

  return (
    <div className="container">
      <p style={{ marginBottom: "1rem" }}>
        <Link href="/">← For You</Link>
      </p>
      <h1>People</h1>
      <p style={{ color: "#71767b", marginBottom: "1rem" }}>
        Viewing as <strong>@{currentUserId}</strong>. Follow/unfollow updates your feed.
      </p>
      {users.map((u) => (
        <div key={u.id} className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <strong>{u.display_name}</strong>
            <span className="time" style={{ marginLeft: "0.5rem" }}>@{u.handle}</span>
            {u.bio && <p style={{ margin: "0.25rem 0 0", fontSize: "0.9rem", color: "#71767b" }}>{u.bio}</p>}
            <span className="time" style={{ fontSize: "0.85rem" }}>{u.followers_count} followers · {u.following_count} following</span>
          </div>
          {u.id !== currentUserId && (
            following.has(u.id) ? (
              <button type="button" className="secondary" onClick={() => handleUnfollow(u.id)}>Unfollow</button>
            ) : (
              <button type="button" onClick={() => handleFollow(u.id)}>Follow</button>
            )
          )}
        </div>
      ))}
    </div>
  );
}
