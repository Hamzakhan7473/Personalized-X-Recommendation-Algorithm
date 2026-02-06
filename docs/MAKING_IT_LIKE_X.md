# Making the app more like X (Twitter)

Ideas to make the project feel and function closer to the real X experience.

## Implemented

- **3-column layout** — Left: logo (𝕏), Home, Explore, Profile, Post button, user pill. Center: feed. Right: Search placeholder, Trending, Who to follow.
- **For you / Following tabs** — Two tabs at top of feed; “For you” = ranked mix (in-network + out-of-network); “Following” = in-network only.
- **Profile page** — `/profile/me` or `/profile/[userId]`: avatar, name, handle, bio, followers/following counts, Follow/Unfollow, timeline of that user’s posts.
- **X-style tweet cards** — Avatar on left, name/handle/time, reply/retweet/like actions; optional “Replying to @…” and quoted tweet block.
- **Who to follow** — Right sidebar shows users you don’t follow yet (from `/users`).

## High impact (next steps)

1. **Search** — Backend: search posts by text, users by handle. Frontend: search box in right sidebar or top bar, results page or dropdown.
2. **Single-tweet / thread view** — Click a tweet to open a detail view (or modal) with the full thread (parent + replies).
3. **Bookmarks** — Backend: bookmarks table + API. Frontend: bookmark icon on tweets, “Bookmarks” in nav, `/bookmarks` page.
4. **Compose in modal** — Click “Post” opens a modal (or slide-over) with the composer instead of inline; character count, optional “Add image” placeholder.
5. **Infinite scroll** — “Load more” or infinite scroll using `next_cursor` when the backend supports it.

## Medium impact

6. **Messages (DMs)** — Minimal: backend threads + messages, frontend “Messages” nav and a simple chat view (big feature).
7. **Hashtag & mention links** — Parse `#topic` and `@handle` in post text; link to `/search?q=topic` or `/profile/handle`.
8. **Media in tweets** — Image upload (e.g. base64 or S3), display thumbnail in tweet card.
9. **“Show new posts” bar** — When new posts exist since last load, show a bar at top to refresh (or auto-refresh).
10. **Pinned tweet** — Allow user to pin one tweet; show it at top of profile.

## Polish

11. **Skeleton loaders** — While feed or profile loads, show skeleton cards instead of “Loading…”.
12. **Responsive** — On small screens, collapse sidebars to icons or bottom nav (mobile X-style).
13. **Keyboard shortcuts** — e.g. `n` for new post, `?` for help.
14. **Dark/light theme** — Toggle; persist in localStorage.

Use this list to pick the next features to implement.
