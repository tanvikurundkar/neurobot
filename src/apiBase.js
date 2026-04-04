/** RAG POST target. Dev default goes through Vite proxy (see vite.config.js). */
export function ragChatUrl() {
  const u = import.meta.env.VITE_CHAT_URL
  if (u) return u
  return '/api/chat'
}
