const socket = io({
    autoConnect: false,
    transports: ["websocket"]
  }
  );