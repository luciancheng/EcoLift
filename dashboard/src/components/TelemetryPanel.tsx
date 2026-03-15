import {
  ArrowUpDown,
  ArrowLeftRight,
  Gauge,
  LifeBuoy,
  AlertTriangle,
  Pause,
  HandHelping,
} from "lucide-react";
import type { Telemetry } from "../types";

interface Props {
  data: Telemetry | null;
}

function Card({
  label,
  value,
  icon: Icon,
  color = "text-zinc-100",
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
      <div className="p-1.5 rounded-md bg-zinc-700/50">
        <Icon className={`w-3.5 h-3.5 ${color}`} />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] text-zinc-500 uppercase tracking-wider leading-tight">
          {label}
        </p>
        <p className={`text-sm font-mono font-semibold leading-tight ${color}`}>
          {value}
        </p>
      </div>
    </div>
  );
}

function StatusPill({
  label,
  active,
  icon: Icon,
}: {
  label: string;
  active: boolean;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div
      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-medium ${
        active
          ? "bg-red-500/10 border-red-500/30 text-red-400"
          : "bg-zinc-800/50 border-zinc-700/50 text-zinc-500"
      }`}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
      <span
        className={`ml-auto w-1.5 h-1.5 rounded-full ${
          active ? "bg-red-400 animate-pulse" : "bg-zinc-600"
        }`}
      />
    </div>
  );
}

export function TelemetryPanel({ data }: Props) {
  if (!data) {
    return (
      <div className="flex flex-col gap-2">
        <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Telemetry
        </h2>
        <div className="p-4 rounded-lg bg-zinc-800/30 border border-zinc-700/50 text-center text-zinc-500 text-xs">
          Awaiting data...
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
        Telemetry
      </h2>

      <div className="grid grid-cols-2 gap-1.5">
        <Card
          label="X Offset"
          value={data.dx.toString()}
          icon={ArrowLeftRight}
        />
        <Card
          label="Y Offset"
          value={data.dy.toString()}
          icon={ArrowUpDown}
          color={
            data.dy < -300
              ? "text-red-400"
              : data.dy < -100
                ? "text-amber-400"
                : "text-zinc-100"
          }
        />
        <Card
          label="Velocity"
          value={data.velocity.toFixed(1)}
          icon={Gauge}
        />
        <Card
          label="Assistance"
          value={`${(data.assistance * 100).toFixed(0)}%`}
          icon={LifeBuoy}
          color={data.assistance > 0 ? "text-amber-400" : "text-emerald-400"}
        />
      </div>

      <div className="flex flex-col gap-1 mt-0.5">
        <StatusPill
          label="Failure Detected"
          active={data.failure}
          icon={AlertTriangle}
        />
        <StatusPill label="Stalled" active={data.stalled} icon={Pause} />
        <StatusPill
          label="Assisting"
          active={data.helping}
          icon={HandHelping}
        />
      </div>
    </div>
  );
}
