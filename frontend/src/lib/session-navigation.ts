// A new document discards client and RSC caches belonging to the previous session.
// Keep this full navigation for login, logout and expired-session redirects.
export function navigateToFreshSession(path: "/login" | "/dashboard") {
  const destination = new URL(path, window.location.origin);
  window.location.assign(destination.href);
}
