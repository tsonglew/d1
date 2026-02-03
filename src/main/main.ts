import { app, BrowserWindow, ipcMain, nativeTheme } from "electron";
import { join } from "path";

const isDev = !app.isPackaged;

const createWindow = () => {
  const win = new BrowserWindow({
    width: 500,
    height: 700,
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
  win.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  if (isDev) {
    win.loadURL("http://localhost:5173");
    win.webContents.openDevTools({ mode: "detach" });
  } else {
    win.loadFile(join(__dirname, "../renderer/index.html"));
  }

  return win;
};

app.whenReady().then(() => {
  nativeTheme.themeSource = "system";
  const win = createWindow();

  ipcMain.handle("pet:set-click-through", (_event, enabled: boolean) => {
    win.setIgnoreMouseEvents(enabled, { forward: true });
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
