declare global {
  interface Window {
    pet: {
      setClickThrough: (enabled: boolean) => Promise<void>;
    };
  }
}

export {};
