# Desktop Pet (Electron + Live2D)

A lightweight desktop pet powered by Electron, TypeScript, and Live2D.

## Requirements

- Node.js 20+
- npm (or pnpm/yarn if you prefer)

## Setup

```bash
npm install
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
