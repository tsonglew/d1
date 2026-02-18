# hiyoriclaw (Electron + Live2D)

A lightweight desktop pet powered by Electron, TypeScript, and Live2D.

Project name: **hiyoriclaw** (a combination of hiyori and [open]claw).

## Requirements

- Node.js 20+
- npm (or pnpm/yarn if you prefer)

## Setup

```bash
npm install
```

## Gemini API 配置

请在运行前设置环境变量（不要提交密钥到仓库）：

```bash
export PACKY_API_BASE_URL="https://www.packyapi.com/v1"
export PACKY_API_KEY="你的密钥"
export GEMINI_MODEL="gemini-1.5-flash"
```

也支持自定义接口路径（如兼容 OpenAI 的代理）：

```bash
export PACKY_API_PATH="/chat/completions"
```

## Add a Live2D model

Place your model files under `public/models/your-model/` and update the path in `src/renderer/main.ts`:

```ts
const MODEL_URL = "/models/your-model/your-model.model3.json";
```

## Development

```bash
npm run dev
```

## Build

```bash
npm run build
npm run dist
```

## Notes

- The app window is frameless, transparent, and always on top.
- Use the Click-Through button to allow clicking through the pet.
