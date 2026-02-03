import "./style.css";
import * as PIXI from "pixi.js";
import { Live2DModel } from "pixi-live2d-display/cubism4";

(globalThis as typeof globalThis & { PIXI: typeof PIXI }).PIXI = PIXI;

const stageEl = document.getElementById("stage");
const statusEl = document.getElementById("status");
const toggleBtn = document.getElementById("toggle-click") as HTMLButtonElement | null;
const bubbleEl = document.getElementById("bubble");

if (!stageEl || !statusEl || !toggleBtn || !bubbleEl) {
  throw new Error("Missing required DOM nodes");
}

const app = new PIXI.Application({
  backgroundAlpha: 0,
  resizeTo: window,
  antialias: true
});

stageEl.appendChild(app.view as HTMLCanvasElement);

const MODEL_URL = "/models/hiyori_free_en/hiyori_free_t08.model3.json";

const fitModel = (model: Live2DModel) => {
  const scale = Math.min(app.renderer.width / model.width, app.renderer.height / model.height) * 0.8;
  model.scale.set(scale, scale);
  model.position.set(app.renderer.width / 2, app.renderer.height * 0.85);
  model.anchor.set(0.5, 1);
};

const setupDragging = (model: Live2DModel) => {
  model.interactive = true;
  model.cursor = "grab";

  let dragging = false;
  let downAt = 0;
  let downX = 0;
  let downY = 0;
  let offsetX = 0;
  let offsetY = 0;
  const clickThreshold = 6;
  const clickTimeMs = 350;

  model.on("pointerdown", (event: PIXI.InteractionEvent) => {
    dragging = false;
    downAt = performance.now();
    const pos = event.data.getLocalPosition(model.parent);
    downX = pos.x;
    downY = pos.y;
    offsetX = model.x - pos.x;
    offsetY = model.y - pos.y;
  });

  model.on("pointerup", (event: PIXI.InteractionEvent) => {
    if (!dragging) {
      const upPos = event.data.getLocalPosition(model.parent);
      const dx = upPos.x - downX;
      const dy = upPos.y - downY;
      const elapsed = performance.now() - downAt;
      if (elapsed <= clickTimeMs && Math.hypot(dx, dy) <= clickThreshold) {
        showBubble(model);
      }
    }

    dragging = false;
    model.cursor = "grab";
  });

  model.on("pointerupoutside", () => {
    dragging = false;
    model.cursor = "grab";
  });

  model.on("pointermove", (event: PIXI.InteractionEvent) => {
    const pos = event.data.getLocalPosition(model.parent);
    if (!dragging) {
      const dx = pos.x - downX;
      const dy = pos.y - downY;
      if (Math.hypot(dx, dy) > clickThreshold) {
        dragging = true;
        model.cursor = "grabbing";
      } else {
        return;
      }
    }
    model.position.set(pos.x + offsetX, pos.y + offsetY);
  });
};

const responses = [
  "嗨！今天也要一起努力吗？",
  "别忘了喝水哦。",
  "我在这儿陪你～",
  "点击我有惊喜！",
  "要不要休息一下？"
];

let bubbleTimer: number | null = null;

const showBubble = (model: Live2DModel) => {
  const message = responses[Math.floor(Math.random() * responses.length)];
  bubbleEl.textContent = message;

  const bounds = model.getBounds();
  const x = bounds.x + bounds.width / 2;
  const y = Math.max(bounds.y, 24);

  bubbleEl.style.left = `${x}px`;
  bubbleEl.style.top = `${y}px`;
  bubbleEl.classList.add("show");

  if (bubbleTimer !== null) {
    window.clearTimeout(bubbleTimer);
  }
  bubbleTimer = window.setTimeout(() => {
    bubbleEl.classList.remove("show");
  }, 2200);
};

const loadPet = async () => {
  try {
    statusEl.textContent = "Loading model...";
    const model = await Live2DModel.from(MODEL_URL, {
      autoInteract: true
    });

    app.stage.addChild(model);
    fitModel(model);
    setupDragging(model);

    window.addEventListener("resize", () => fitModel(model));

    statusEl.textContent = "Model ready";
  } catch (error) {
    console.error(error);
    statusEl.textContent = "Model load failed. See console.";
  }
};

let clickThrough = false;

toggleBtn.addEventListener("click", async () => {
  clickThrough = !clickThrough;
  await window.pet.setClickThrough(clickThrough);
  toggleBtn.classList.toggle("active", clickThrough);
  toggleBtn.textContent = clickThrough ? "Click-Through On" : "Click-Through";
});

loadPet();
