// src/pages/CreativeDashboard.tsx
import { useMemo, useState } from "react";
import { submitCreativeReaction } from "@/lib/api";

// If you already have shadcn components, use them.
// Otherwise you can replace with plain HTML inputs.
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const DEFAULT_PERSONAS = {
  hcp_early:
    "Dermatologist, 8 years experience, early adopter, comfortable with new therapies, values mechanism and emerging evidence.",
  hcp_conservative:
    "Dermatologist, 15 years experience, conservative prescriber, skeptical of new drugs, guideline-driven, high safety/evidence threshold.",
  patient_new:
    "Patient newly diagnosed with microcystic lymphatic malformation, anxious, low-to-medium health literacy, wants reassurance and next steps.",
  patient_long:
    "Patient living with microcystic lymphatic malformation for 10+ years, has tried treatments, skeptical of generic education, wants specific actionable info.",
};

export default function CreativeDashboard() {
  const [headline, setHeadline] = useState(
    "Understanding microcystic lymphatic malformation (mLM) and care options"
  );
  const [personasJson, setPersonasJson] = useState(
    JSON.stringify(DEFAULT_PERSONAS, null, 2)
  );

  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string>("");

  const previewUrl = useMemo(() => {
    if (!file) return "";
    return URL.createObjectURL(file);
  }, [file]);

  function onPickFile(f: File | null) {
    setError(null);
    setResult("");
    if (!f) {
      setFile(null);
      return;
    }

    // Enforce PNG support (and allow JPG/JPEG if you want)
    const okTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!okTypes.includes(f.type)) {
      setFile(null);
      setError(
        `Unsupported file type: ${f.type || "unknown"}. Please upload PNG (or JPG/JPEG/WEBP).`
      );
      return;
    }

    // Optional: size guard (e.g., 10MB)
    const maxBytes = 10 * 1024 * 1024;
    if (f.size > maxBytes) {
      setFile(null);
      setError("File is too large. Please upload an image under 10MB.");
      return;
    }

    setFile(f);
  }

  async function onSubmit() {
    setError(null);
    setResult("");

    if (!file) {
      setError("Please upload a creative image (PNG recommended).");
      return;
    }

    // Validate personas JSON
    try {
      JSON.parse(personasJson);
    } catch (e) {
      setError("personas_json is not valid JSON. Please fix it.");
      return;
    }

    setBusy(true);
    try {
      const resp = await submitCreativeReaction({
        headline,
        personasJson,
        imageFile: file,
      });
      setResult(resp.answer);
    } catch (e: any) {
      setError(e?.message ?? "Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Pharma Creative Testing Dashboard</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="headline">Headline</Label>
            <Input
              id="headline"
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="Headline for the creative"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="personas">Personas (JSON)</Label>
            <Textarea
              id="personas"
              value={personasJson}
              onChange={(e) => setPersonasJson(e.target.value)}
              rows={10}
              spellCheck={false}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="image">Creative image (PNG)</Label>
            <Input
              id="image"
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp"
              onChange={(e) => onPickFile(e.target.files?.[0] ?? null)}
            />
            {previewUrl ? (
              <div className="pt-2">
                <div className="text-sm text-muted-foreground pb-2">
                  Preview:
                </div>
                <img
                  src={previewUrl}
                  alt="creative preview"
                  className="max-h-80 rounded-md border"
                />
              </div>
            ) : null}
          </div>

          {error ? (
            <div className="text-sm text-red-600 whitespace-pre-wrap">
              {error}
            </div>
          ) : null}

          <Button onClick={onSubmit} disabled={busy}>
            {busy ? "Running…" : "Run synthetic reactions"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Output</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap text-sm">{result}</pre>
        </CardContent>
      </Card>
    </div>
  );
}