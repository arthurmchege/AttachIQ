"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

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

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";

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
    <main className="flex h-screen flex-col bg-muted">
      <header className="border-b bg-background px-6 py-4">
        <h1 className="text-lg font-semibold">SupervisorIQ</h1>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Start by telling SupervisorIQ which student you&apos;re ready to
            assess.
          </p>
        )}

        <div className="space-y-4">
          {messages.map((m, i) => (
            <Card
              key={i}
              className={cn(
                "max-w-2xl py-0",
                m.role === "user" &&
                  "ml-auto bg-primary text-primary-foreground",
                m.role === "error" && "border-destructive bg-destructive/10",
              )}
            >
              <CardContent className="px-4 py-2">
                <p
                  className={cn(
                    "whitespace-pre-wrap text-sm",
                    m.role === "error" && "text-destructive",
                  )}
                >
                  {m.content}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
        <div ref={bottomRef} />
      </div>

      <form onSubmit={sendMessage} className="border-t bg-background p-4">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
            placeholder="Type your message..."
            className="flex-1"
          />
          <Button type="submit" disabled={sending || !input.trim()}>
            {sending ? "Sending..." : "Send"}
          </Button>
        </div>
      </form>
    </main>
  );
}
