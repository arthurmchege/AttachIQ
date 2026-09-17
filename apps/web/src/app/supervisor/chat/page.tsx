"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Message = {
  role: "user" | "agent" | "error";
  content: string;
};

export default function SupervisorChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const sessionIdRef = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;

    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setSending(true);

    try {
      const res = await fetch(`${API_BASE}/agents/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          session_id: sessionIdRef.current,
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Request failed (${res.status})`);
      }

      // Parse the SSE stream manually: read raw bytes, decode to text,
      // and split on the blank-line-terminated "data: {...}\n\n" frames
      // that StreamingResponse emits.
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? ""; // last chunk may be incomplete, keep it

        for (const frame of frames) {
          if (!frame.startsWith("data: ")) continue;
          const payload = JSON.parse(frame.slice(6));

          if (payload.type === "session") {
            sessionIdRef.current = payload.session_id;
          } else if (payload.type === "done") {
            setMessages((prev) => [
              ...prev,
              { role: "agent", content: payload.content },
            ]);
          } else if (payload.type === "error") {
            setMessages((prev) => [
              ...prev,
              { role: "error", content: payload.content },
            ]);
          }
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "error",
          content: err instanceof Error ? err.message : "Something went wrong.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="flex h-screen flex-col bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-6 py-4">
        <h1 className="text-lg font-semibold text-gray-900">SupervisorIQ</h1>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400">
            Start by telling SupervisorIQ which student you&apos;re ready to
            assess.
          </p>
        )}

        <div className="space-y-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-2xl rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "ml-auto bg-blue-600 text-white"
                  : m.role === "error"
                    ? "bg-red-50 text-red-700 border border-red-200"
                    : "bg-white border border-gray-200 text-gray-900"
              }`}
            >
              {m.content}
            </div>
          ))}
        </div>
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={sendMessage}
        className="border-t border-gray-200 bg-white p-4"
      >
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
            placeholder="Type your message..."
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </main>
  );
}
