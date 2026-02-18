import { app, BrowserWindow, ipcMain, nativeTheme, screen } from "electron";
import { join } from "path";
import { generatePetReply } from "./ai";

const isDev = !app.isPackaged;
let mainWindow: BrowserWindow | null = null;

ipcMain.handle("pet:generate-reply", async (_event, prompt: string) => {
  return generatePetReply(prompt);
});

ipcMain.handle("pet:set-click-through", (_event, enabled: boolean) => {
  if (mainWindow) {
    mainWindow.setIgnoreMouseEvents(enabled, { forward: true });
  }
});

const applyFullScreenBounds = (win: BrowserWindow) => {
  const display = screen.getPrimaryDisplay();
  win.setBounds(display.bounds);
};

const createWindow = () => {
  const display = screen.getPrimaryDisplay();
  const { bounds } = display;

  const win = new BrowserWindow({
    x: bounds.x,
    y: bounds.y,
    width: bounds.width,
    height: bounds.height,
    transparent: true,
    frame: false,
    resizable: false,
    alwaysOnTop: true,
    hasShadow: false,
    skipTaskbar: true,
    webPreferences: {
      preload: join(__dirname, "../preload/preload.js"),
      contextIsolation: true,
      sandbox: false
    }
  });

  win.setBackgroundColor("#00000000");
  win.setAlwaysOnTop(true, "screen-saver");
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  win.setIgnoreMouseEvents(true, { forward: true });

  screen.on("display-metrics-changed", () => applyFullScreenBounds(win));
  screen.on("display-added", () => applyFullScreenBounds(win));
  screen.on("display-removed", () => applyFullScreenBounds(win));

  if (isDev) {
    win.loadURL("http://localhost:5173");
  } else {
    win.loadFile(join(__dirname, "../renderer/index.html"));
  }

  return win;
};

app.whenReady().then(() => {
  nativeTheme.themeSource = "system";

  if (process.platform === "darwin") {
    app.dock.hide();
  }

  mainWindow = createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
