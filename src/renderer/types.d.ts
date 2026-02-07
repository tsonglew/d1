declare global {
  interface Window {
    pet: {
      setClickThrough: (enabled: boolean) => Promise<void>;
      generateReply: (prompt: string) => Promise<string>;
    };
  }
}

export {};
