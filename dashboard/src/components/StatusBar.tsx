import { Leaf, Wifi, WifiOff } from "lucide-react";

interface Props {
  connected: boolean;
  streaming: boolean;
  failure: boolean;
  hoistDirection: "U" | "D" | "N";
}

const HOIST_LABELS: Record<string, { text: string; cls: string }> = {
  U: { text: "HOIST ▲ UP", cls: "bg-amber-500/15 text-amber-400" },
  D: { text: "HOIST ▼ DOWN", cls: "bg-blue-500/15 text-blue-400" },
  N: { text: "HOIST — IDLE", cls: "bg-zinc-700/50 text-zinc-400" },
};

export function StatusBar({ connected, streaming, failure, hoistDirection }: Props) {
  const hoist = HOIST_LABELS[hoistDirection] ?? HOIST_LABELS.N;

  return (
    <header className="flex items-center justify-between px-5 py-2 bg-zinc-900 border-b border-zinc-800 shrink-0">
      <div className="flex items-center gap-2.5">
        <Leaf className="w-5 h-5 text-emerald-400" />
        <h1 className="text-base font-semibold text-zinc-100 tracking-tight">
          EcoLift
        </h1>
      </div>

      <div className="flex items-center gap-3 text-sm">
        {failure && (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-500/15 text-red-400 text-xs font-medium animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
            FAILURE
          </span>
        )}

        <span className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold font-mono ${hoist.cls}`}>
          {hoist.text}
        </span>

        <span
          className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
            streaming ? "bg-emerald-500/15 text-emerald-400" : "bg-zinc-700/50 text-zinc-400"
          }`}
        >
          {streaming ? "Stream Live" : "No Stream"}
        </span>

        <span
          className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
            connected ? "bg-emerald-500/15 text-emerald-400" : "bg-red-500/15 text-red-400"
          }`}
        >
          {connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>
    </header>
  );
}
