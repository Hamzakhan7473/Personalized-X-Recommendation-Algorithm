"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { User } from "@/lib/api";

export default function XLayout({
  children,
  currentUser,
  trends,
  whoToFollow,
}: {
  children: React.ReactNode;
  currentUser: User | null;
  trends: { topic: string; count: number }[];
  whoToFollow: User[];
}) {
  const pathname = usePathname();
  const isActive = (path: string) => pathname === path || (path === "/" && pathname === "/");

  return (
    <div className="x-root">
      <aside className="x-left">
        <Link href="/" className="x-logo">
          𝕏
        </Link>
        <nav className="x-nav">
          <Link href="/" className={isActive("/") ? "x-nav-item active" : "x-nav-item"}>
            <span className="x-nav-icon">⌂</span>
            <span>Home</span>
          </Link>
          <Link href="/users" className={pathname === "/users" ? "x-nav-item active" : "x-nav-item"}>
            <span className="x-nav-icon">◇</span>
            <span>Explore</span>
          </Link>
          {currentUser && (
            <Link href="/profile/me" className={pathname?.startsWith("/profile") ? "x-nav-item active" : "x-nav-item"}>
              <span className="x-nav-icon">👤</span>
              <span>Profile</span>
            </Link>
          )}
        </nav>
        {currentUser && (
          <Link href="/" className="x-post-btn">
            Post
          </Link>
        )}
        {currentUser && (
          <div className="x-user-pill">
            <span className="x-user-pill-avatar">{currentUser.display_name?.charAt(0) ?? "?"}</span>
            <div className="x-user-pill-text">
              <strong>{currentUser.display_name}</strong>
              <span className="time">@{currentUser.handle}</span>
            </div>
          </div>
        )}
      </aside>
      <main className="x-center">{children}</main>
      <aside className="x-right">
        <div className="x-search-placeholder">Search</div>
        {trends.length > 0 && (
          <div className="x-card">
            <h3 className="x-card-title">Trending</h3>
            {trends.slice(0, 5).map(({ topic, count }) => (
              <div key={topic} className="x-trend-row">
                <span className="x-trend-topic">#{topic}</span>
                <span className="time">{count} posts</span>
              </div>
            ))}
          </div>
        )}
        {whoToFollow.length > 0 && (
          <div className="x-card">
            <h3 className="x-card-title">Who to follow</h3>
            {whoToFollow.slice(0, 3).map((u) => (
              <Link key={u.id} href={`/profile/${u.id}`} className="x-wtf-row">
                <span className="x-avatar-sm">{u.display_name?.charAt(0) ?? "?"}</span>
                <div className="x-wtf-info">
                  <strong>{u.display_name}</strong>
                  <span className="time">@{u.handle}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}
