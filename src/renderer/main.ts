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
  const maxWidthScale = (app.renderer.width / model.width) * 0.5;
  const maxHeightScale = (app.renderer.height / model.height) * 0.4;
  const scale = Math.min(maxWidthScale, maxHeightScale);
  model.scale.set(scale, scale);
  model.position.set(app.renderer.width / 2, app.renderer.height * 0.85);
  model.anchor.set(0.5, 1);
};

const setupDragging = (model: Live2DModel) => {
  model.interactive = true;
  model.cursor = "grab";

  let dragging = false;
  let dragOverride = false;
  let hoverOverride = false;
  let downAt = 0;
  let downX = 0;
  let downY = 0;
  let downOnModel = false;
  let offsetX = 0;
  let offsetY = 0;
  let longPressTimer: number | null = null;
  const clickThreshold = 6;
  const longPressMs = 450;

  let clickThroughPreference = true;
  let appliedClickThrough: boolean | null = null;

  const applyClickThrough = async () => {
    const shouldIgnore = clickThroughPreference && !hoverOverride && !dragOverride;
    if (appliedClickThrough === shouldIgnore) return;
    appliedClickThrough = shouldIgnore;
    await window.pet.setClickThrough(shouldIgnore);
  };

  const updateToggle = () => {
    toggleBtn.classList.toggle("active", clickThroughPreference);
    toggleBtn.textContent = clickThroughPreference ? "Click-Through On" : "Click-Through";
  };

  const getPointer = (event: MouseEvent) => {
    const rect = app.view.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top
    };
  };

  const isOverModel = (x: number, y: number) => {
    const bounds = model.getBounds();
    return x >= bounds.x && x <= bounds.x + bounds.width && y >= bounds.y && y <= bounds.y + bounds.height;
  };

  const clearLongPress = () => {
    if (longPressTimer !== null) {
      window.clearTimeout(longPressTimer);
      longPressTimer = null;
    }
  };

  const beginDrag = (x: number, y: number) => {
    dragging = true;
    dragOverride = true;
    void applyClickThrough();
    model.cursor = "grabbing";
    offsetX = model.x - x;
    offsetY = model.y - y;
  };

  const endDrag = () => {
    dragging = false;
    dragOverride = false;
    model.cursor = "grab";
    void applyClickThrough();
  };

  const scheduleLongPress = (x: number, y: number) => {
    if (longPressTimer !== null) return;
    longPressTimer = window.setTimeout(() => {
      longPressTimer = null;
      if (!downOnModel) return;
      beginDrag(x, y);
    }, longPressMs);
  };

  const updateHover = (x: number, y: number) => {
    if (!clickThroughPreference || dragOverride) return;
    const over = isOverModel(x, y);
    if (hoverOverride === over) return;
    hoverOverride = over;
    void applyClickThrough();
  };

  const onMouseDown = (event: MouseEvent) => {
    if (event.button !== 0) return;
    const pos = getPointer(event);
    downAt = performance.now();
    downX = pos.x;
    downY = pos.y;
    downOnModel = isOverModel(pos.x, pos.y);
    if (downOnModel) {
      scheduleLongPress(pos.x, pos.y);
    }
  };

  const onMouseMove = (event: MouseEvent) => {
    const pos = getPointer(event);
    updateHover(pos.x, pos.y);

    if (dragging) {
      model.position.set(pos.x + offsetX, pos.y + offsetY);
      return;
    }

    if (event.buttons === 1 && downOnModel) {
      scheduleLongPress(pos.x, pos.y);
    }
  };

  const onMouseUp = (event: MouseEvent) => {
    clearLongPress();
    const elapsed = performance.now() - downAt;
    const pos = getPointer(event);
    const dx = pos.x - downX;
    const dy = pos.y - downY;

    if (!dragging && downOnModel && elapsed <= longPressMs && Math.hypot(dx, dy) <= clickThreshold) {
      showBubble(model);
    }

    downOnModel = false;
    if (dragging) {
      endDrag();
    }
  };

  const onMouseLeave = () => {
    clearLongPress();
    downOnModel = false;
    if (hoverOverride) {
      hoverOverride = false;
      void applyClickThrough();
    }
    if (dragging) {
      endDrag();
    }
  };

  window.addEventListener("mousedown", onMouseDown);
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("mouseup", onMouseUp);
  window.addEventListener("blur", onMouseLeave);

  toggleBtn.addEventListener("click", async () => {
    clickThroughPreference = !clickThroughPreference;
    updateToggle();
    await applyClickThrough();
  });

  updateToggle();
  void applyClickThrough();
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

loadPet();
