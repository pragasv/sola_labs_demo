// src/lib/api.ts
export const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export type CreativeReactResponse = {
  answer: string; // backend returns { "answer": "..." }
};

export async function submitCreativeReaction(params: {
  headline: string;
  personasJson: string;
  imageFile: File;
}): Promise<CreativeReactResponse> {
  console.log("VITE_API_BASE =", import.meta.env.VITE_API_BASE);
  console.log("API_BASE used =", API_BASE);
  console.log("POST URL =", `${API_BASE}/creative/react`);

  const form = new FormData();
  form.append("headline", params.headline);
  form.append("personas_json", params.personasJson);
  form.append("image", params.imageFile);

  const res = await fetch(`${API_BASE}/creative/react`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed (${res.status}): ${text || res.statusText}`);
  }

  return res.json();
}