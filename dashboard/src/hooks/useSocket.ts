import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";

const PI_URL = `http://${import.meta.env.VITE_PI_HOST || "localhost"}:${import.meta.env.VITE_PI_PORT || "8765"}`;

export function useSocket() {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const s = io(PI_URL, { transports: ["websocket", "polling"] });
    socketRef.current = s;

    s.on("connect", () => setConnected(true));
    s.on("disconnect", () => setConnected(false));

    return () => {
      s.disconnect();
    };
  }, []);

  return { socket: socketRef.current, connected };
}
