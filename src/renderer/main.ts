import "./style.css";
import * as PIXI from "pixi.js";
import { Live2DModel } from "pixi-live2d-display/cubism4";

(globalThis as typeof globalThis & { PIXI: typeof PIXI }).PIXI = PIXI;

const stageEl = document.getElementById("stage");
const statusEl = document.getElementById("status");
const toggleBtn = document.getElementById("toggle-click") as HTMLButtonElement | null;

if (!stageEl || !statusEl || !toggleBtn) {
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
  let offsetX = 0;
  let offsetY = 0;

  model.on("pointerdown", (event: PIXI.InteractionEvent) => {
    dragging = true;
    model.cursor = "grabbing";
    const pos = event.data.getLocalPosition(model.parent);
    offsetX = model.x - pos.x;
    offsetY = model.y - pos.y;
  });

  model.on("pointerup", () => {
    dragging = false;
    model.cursor = "grab";
  });

  model.on("pointerupoutside", () => {
    dragging = false;
    model.cursor = "grab";
  });

  model.on("pointermove", (event: PIXI.InteractionEvent) => {
    if (!dragging) return;
    const pos = event.data.getLocalPosition(model.parent);
    model.position.set(pos.x + offsetX, pos.y + offsetY);
  });
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
