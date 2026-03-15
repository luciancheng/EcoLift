import { useState, useEffect, useRef } from "react";
import { useSocket } from "./hooks/useSocket";
import { useWebRTC } from "./hooks/useWebRTC";
import { StatusBar } from "./components/StatusBar";
import { VideoFeed } from "./components/VideoFeed";
import { TelemetryPanel } from "./components/TelemetryPanel";
import { TelemetryChart } from "./components/TelemetryChart";
import { ControlPanel } from "./components/ControlPanel";
import type { Telemetry, TelemetryPoint } from "./types";

const HISTORY_WINDOW_S = 15;

export default function App() {
  const { socket, connected } = useSocket();
  const { videoRef, streaming, reconnect } = useWebRTC(socket, connected);

  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [history, setHistory] = useState<TelemetryPoint[]>([]);
  const [showDebug, setShowDebug] = useState(false);
  const historyRef = useRef<TelemetryPoint[]>([]);

  useEffect(() => {
    if (!socket) return;

    const handler = (data: Telemetry) => {
      setTelemetry(data);

      const now = Date.now() / 1000;
      const point: TelemetryPoint = {
        time: now,
        dy: data.dy,
        assistance: data.assistance,
      };
      const cutoff = now - HISTORY_WINDOW_S;
      const updated = [...historyRef.current, point].filter(
        (p) => p.time > cutoff
      );
      historyRef.current = updated;
      setHistory(updated);
    };

    socket.on("telemetry", handler);
    return () => {
      socket.off("telemetry", handler);
    };
  }, [socket]);

  return (
    <div className="h-screen flex flex-col bg-zinc-950 overflow-hidden">
      <StatusBar
        connected={connected}
        streaming={streaming}
        failure={telemetry?.failure ?? false}
        hoistDirection={telemetry?.hoist_direction ?? "N"}
      />

      <main className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-3 p-3 min-h-0 overflow-hidden">
        {/* Left column: video + charts */}
        <div className="flex flex-col gap-3 min-h-0 overflow-hidden">
          <VideoFeed
            videoRef={videoRef}
            socket={socket}
            streaming={streaming}
            onReconnect={reconnect}
          />
          <TelemetryChart history={history} />
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
