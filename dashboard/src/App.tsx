import { useState, useEffect, useRef, useCallback } from "react";
import { useSocket } from "./hooks/useSocket";
import { useWebRTC } from "./hooks/useWebRTC";
import { StatusBar } from "./components/StatusBar";
import { VideoFeed } from "./components/VideoFeed";
import { TelemetryPanel } from "./components/TelemetryPanel";
import { TelemetryChart } from "./components/TelemetryChart";
import { HoistPanel } from "./components/HoistPanel";
import { ControlPanel } from "./components/ControlPanel";
import type { Telemetry, TelemetryPoint } from "./types";

const HISTORY_WINDOW_S = 15;
const MAX_HISTORY_POINTS = 300;
const UI_UPDATE_INTERVAL_MS = 200;

export default function App() {
  const { socket, connected } = useSocket();
  const { videoRef, streaming, reconnect } = useWebRTC(socket, connected);

  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [history, setHistory] = useState<TelemetryPoint[]>([]);
  const [showDebug, setShowDebug] = useState(false);

  const latestTelemetry = useRef<Telemetry | null>(null);
  const historyBuf = useRef<TelemetryPoint[]>([]);

  const flushToUI = useCallback(() => {
    if (latestTelemetry.current) {
      setTelemetry(latestTelemetry.current);
    }
    setHistory([...historyBuf.current]);
  }, []);

  useEffect(() => {
    if (!socket) return;

    const handler = (data: Telemetry) => {
      latestTelemetry.current = data;

      const now = Date.now() / 1000;
      const buf = historyBuf.current;
      buf.push({ time: now, dy: data.dy, assistance: data.assistance });

      const cutoff = now - HISTORY_WINDOW_S;
      while (buf.length > 0 && buf[0].time < cutoff) {
        buf.shift();
      }
      if (buf.length > MAX_HISTORY_POINTS) {
        buf.splice(0, buf.length - MAX_HISTORY_POINTS);
      }
    };

    socket.on("telemetry", handler);

    const tick = setInterval(flushToUI, UI_UPDATE_INTERVAL_MS);

    return () => {
      socket.off("telemetry", handler);
      clearInterval(tick);
    };
  }, [socket, flushToUI]);

  return (
    <div className="h-screen flex flex-col bg-zinc-950 overflow-hidden">
      <StatusBar
        connected={connected}
        streaming={streaming}
        failure={telemetry?.failure ?? false}
      />

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-3 p-3 min-h-0 overflow-hidden">
        {/* Left column: video + chart + hoist */}
        <div className="flex flex-col gap-3 min-h-0 overflow-hidden">
          <VideoFeed
            videoRef={videoRef}
            socket={socket}
            streaming={streaming}
            onReconnect={reconnect}
          />
          <div className="grid grid-cols-[1fr_1fr] gap-2 min-h-0">
            <TelemetryChart history={history} />
            <HoistPanel
              direction={telemetry?.hoist_direction ?? "N"}
              failure={telemetry?.failure ?? false}
              stalled={telemetry?.stalled ?? false}
              helping={telemetry?.helping ?? false}
            />
          </div>
        </div>

        {/* Right column: telemetry + controls */}
        <div className="flex flex-col gap-3 min-h-0 overflow-y-auto">
          <TelemetryPanel data={telemetry} />
          <ControlPanel
            socket={socket}
            telemetry={telemetry}
            showDebug={showDebug}
            onToggleDebug={setShowDebug}
          />
        </div>
      </main>
    </div>
  );
}
