type ChatCompletion = {
  choices?: Array<{ message?: { content?: string } }>;
};

type GeminiResponse = {
  candidates?: Array<{
    content?: { parts?: Array<{ text?: string }> };
  }>;
};

const DEFAULT_BASE_URL = "https://www.packyapi.com/v1";
const DEFAULT_PATH = "/chat/completions";

const normalizeText = (value: unknown) => {
  if (typeof value !== "string") return "";
  return value.trim();
};

const extractText = (data: unknown) => {
  const completion = data as ChatCompletion;
  const choiceText = normalizeText(completion?.choices?.[0]?.message?.content);
  if (choiceText) return choiceText;

  const gemini = data as GeminiResponse;
  const geminiText = normalizeText(gemini?.candidates?.[0]?.content?.parts?.[0]?.text);
  return geminiText;
};

export const generatePetReply = async (prompt: string) => {
  const apiKey = process.env.PACKY_API_KEY || process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error("Missing PACKY_API_KEY or GEMINI_API_KEY");
  }

  const baseUrl = process.env.PACKY_API_BASE_URL || DEFAULT_BASE_URL;
  const apiPath = process.env.PACKY_API_PATH || DEFAULT_PATH;
  const model = process.env.GEMINI_MODEL || "gemini-1.5-flash";

  const url = new URL(apiPath, baseUrl).toString();
  const payload = {
    model,
    messages: [
      {
        role: "system",
        content:
          "You are a cute desktop pet. Reply in short, friendly Chinese. Keep it under 20 characters. Avoid emojis."
      },
      { role: "user", content: prompt }
    ],
    temperature: 0.9,
    max_tokens: 64
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Gemini API error ${response.status}: ${text}`);
  }

  const data = (await response.json()) as unknown;
  const reply = extractText(data);
  if (!reply) {
    throw new Error("Gemini API returned empty response");
  }
  return reply.split(/\n/)[0]?.trim() || reply.trim();
};
