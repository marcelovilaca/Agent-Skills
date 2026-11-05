# OpenAI-compatible endpoints

Most providers expose the same chat-completions shape, so one small client
covers them all. Keep it in your own code rather than adding a provider
SDK for a single call shape.

## The client

```ts
export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export async function chat(
  messages: ChatMessage[],
  options: { maxTokens?: number; temperature?: number; json?: boolean } = {},
): Promise<string> {
  const response = await fetch(`${base}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
      max_tokens: options.maxTokens ?? 700,
      temperature: options.temperature ?? 0.4,
      // Providers that support it: Qwen3 and friends take this and skip
      // the reasoning pass entirely. It is the difference between a
      // 12-second call and a 104-second one.
      enable_thinking: false,
      ...(options.json ? { response_format: { type: "json_object" } } : {}),
    }),
    signal: AbortSignal.timeout(60_000),
  });
  if (!response.ok) throw new Error(`AI ${response.status}: …`);
  return body.choices?.[0]?.message?.content;
}
```

A reasoning model returns **both** `reasoning_content` and `content`. Read
`content`; the reasoning is the part you asked it to skip.

## Defensive JSON

Ask for JSON and then take the first balanced object in the response —
models wrap JSON in prose or code fences even when told not to, and a
naive `JSON.parse` of the whole reply fails on a reply that is 95% valid.

```ts
export function extractJson<T>(text: string): T {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = fenced?.[1] ?? text;
  const start = candidate.indexOf("{");
  if (start < 0) throw new Error("No JSON object in the model response");
  let depth = 0, inString = false, escaped = false;
  for (let i = start; i < candidate.length; i++) {
    const ch = candidate[i];
    if (escaped) { escaped = false; continue; }
    if (ch === "\\") { escaped = true; continue; }
    if (ch === '"') { inString = !inString; continue; }
    if (inString) continue;
    if (ch === "{") depth += 1;
    else if (ch === "}") {
      depth -= 1;
      if (depth === 0) return JSON.parse(candidate.slice(start, i + 1)) as T;
    }
  }
  throw new Error("Unbalanced JSON in the model response");
}
```

## Measuring a call before trusting it

Time one real request with the real prompt before wiring it up. A small
prompt can answer in seconds while the production prompt times out, which
points at the *content* of the request, not the endpoint. When that
happens, check three things in order: the number of input items, whether
the model is reasoning, and the output token budget.

## Pointing at a locally configured endpoint

On this machine the Bailian/DashScope token plan is already authenticated
for the `bl` CLI, and its credentials live in `~/.bailian/config.json`
under the **active profile**:

```json
{ "active_config": "token-plan",
  "token-plan": { "api_key": "…", "base_url": "https://…", "default_text_model": "…" } }
```

Read the active profile, not a top-level key — the file holds one object
per profile and only the active one applies. The OpenAI-compatible chat
path is `<base_url>/compatible-mode/v1/chat/completions`.

Put the values in the project's gitignored env file:

```
AI_BASE_URL=<base_url>/compatible-mode/v1
AI_API_KEY=…
AI_MODEL=…
```

## Provider flags worth knowing

| Flag | Effect |
|---|---|
| `enable_thinking: false` | Skips the reasoning pass on Qwen3-family models. The single biggest latency win for short generation tasks. |
| `response_format: { type: "json_object" }` | Asks for JSON directly. Worth sending, but do not rely on it — still parse defensively. |
| `max_tokens` | A budget for the **whole** reply, reasoning included. Too low and a reasoning model returns no answer at all. |
