import { Leaf, Wifi, WifiOff, Cpu, Eye, EyeOff } from "lucide-react";

interface Props {
  connected: boolean;
  streaming: boolean;
  failure: boolean;
  trackingActive: boolean;
  piConnected: boolean;
}

function Pill({
  active,
  activeClass,
  inactiveClass = "bg-zinc-700/50 text-zinc-400",
  children,
}: {
  active: boolean;
  activeClass: string;
  inactiveClass?: string;
  children: React.ReactNode;
}) {
  return (
    <span
      className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
        active ? activeClass : inactiveClass
      }`}
    >
      {children}
    </span>
  );
}

export function StatusBar({
  connected,
  streaming,
  failure,
  trackingActive,
  piConnected,
}: Props) {
  return (
    <header className="flex items-center justify-between px-5 py-2 bg-zinc-900 border-b border-zinc-800 shrink-0">
      <div className="flex items-center gap-2.5">
        <Leaf className="w-5 h-5 text-emerald-400" />
        <h1 className="text-base font-semibold text-zinc-100 tracking-tight">
          EcoLift
        </h1>
      </div>

      <div className="flex items-center gap-2 text-sm">
        {failure && (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-500/15 text-red-400 text-xs font-medium animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
            FAILURE
          </span>
        )}

        <Pill
          active={trackingActive}
          activeClass="bg-emerald-500/15 text-emerald-400"
          inactiveClass="bg-red-500/15 text-red-400"
        >
          {trackingActive ? (
            <Eye className="w-3 h-3" />
          ) : (
            <EyeOff className="w-3 h-3" />
          )}
          {trackingActive ? "Tracking" : "Track Lost"}
        </Pill>

        <Pill
          active={streaming}
          activeClass="bg-emerald-500/15 text-emerald-400"
        >
          {streaming ? "Stream" : "No Stream"}
        </Pill>

        <Pill
          active={connected}
          activeClass="bg-emerald-500/15 text-emerald-400"
          inactiveClass="bg-red-500/15 text-red-400"
        >
          {connected ? (
            <Wifi className="w-3 h-3" />
          ) : (
            <WifiOff className="w-3 h-3" />
          )}
          Server
        </Pill>

        <Pill
          active={piConnected}
          activeClass="bg-emerald-500/15 text-emerald-400"
        >
          <Cpu className="w-3 h-3" />
          Pi
        </Pill>
      </div>
    </header>
  );
}
