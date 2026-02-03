import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("pet", {
  setClickThrough: (enabled: boolean) => ipcRenderer.invoke("pet:set-click-through", enabled)
});
