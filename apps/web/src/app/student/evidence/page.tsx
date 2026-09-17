"use client";

import { useState } from "react";
import { getToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Hardcoded for MVP demo — Aaron Minish's known placement + CSC103 (next
// pending unit after CSC101/CSC102 were assessed in earlier testing).
// Replace with a real "my placements/units" lookup post-MVP.
const DEMO_PLACEMENT_ID = "f8330acd-0908-436c-be6e-ae95774452e6";
const DEMO_COMPETENCY_UNIT_ID = "f240719b-cbcb-4212-b076-c573a1e109e9";
export default function EvidenceUploadPage() {
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<
    "idle" | "submitting" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setStatus("error");
      setMessage("Please choose a file to upload.");
      return;
    }

    const token = getToken();
    if (!token) {
      setStatus("error");
      setMessage("You are not signed in.");
      return;
    }

    setStatus("submitting");
    setMessage(null);

    const formData = new FormData();
    formData.append("placement_id", DEMO_PLACEMENT_ID);
    formData.append("competency_unit_id", DEMO_COMPETENCY_UNIT_ID);
    formData.append("description", description);
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/evidence/submit`, {
        method: "POST",
        headers: {
          // No Content-Type here — the browser sets the correct
          // multipart boundary automatically when body is FormData.
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Upload failed (${res.status}).`);
      }

      const data = await res.json();
      setStatus("success");
      setMessage(
        `Evidence submitted. File: ${data.data?.file_url ?? "uploaded"}`,
      );
      setDescription("");
      setFile(null);
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Submit Evidence</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Screenshot of the caching feature implementation"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="file">File</Label>
              <Input
                id="file"
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </div>

            {message && (
              <p
                className={
                  status === "error"
                    ? "text-sm text-destructive"
                    : "text-sm text-muted-foreground"
                }
              >
                {message}
              </p>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={status === "submitting"}
            >
              {status === "submitting" ? "Uploading..." : "Submit Evidence"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
