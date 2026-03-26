import { ArrowUp, ArrowDown, Minus, AlertTriangle, Pause, HandHelping, EyeOff } from "lucide-react";

interface Props {
  direction: "U" | "D" | "N";
  failure: boolean;
  stalled: boolean;
  helping: boolean;
  trackingActive: boolean;
}

const HOIST_CONFIG: Record<
  string,
  {
    icon: typeof ArrowUp;
    label: string;
    description: string;
    bg: string;
    border: string;
    text: string;
    iconBg: string;
    glow: string;
  }
> = {
  U: {
    icon: ArrowUp,
    label: "UP",
    description: "Assisting lifter",
    bg: "bg-amber-500/8",
    border: "border-amber-500/25",
    text: "text-amber-400",
    iconBg: "bg-amber-500/15",
    glow: "shadow-[0_0_24px_rgba(245,158,11,0.15)]",
  },
  D: {
    icon: ArrowDown,
    label: "DOWN",
    description: "Returning hoist",
    bg: "bg-blue-500/8",
    border: "border-blue-500/25",
    text: "text-blue-400",
    iconBg: "bg-blue-500/15",
    glow: "shadow-[0_0_24px_rgba(59,130,246,0.15)]",
  },
  N: {
    icon: Minus,
    label: "NEUTRAL",
    description: "Hoist idle",
    bg: "bg-zinc-800/30",
    border: "border-zinc-700/50",
    text: "text-zinc-400",
    iconBg: "bg-zinc-700/50",
    glow: "",
  },
};

function StatusRow({
  icon: Icon,
  label,
  active,
  color = "red",
}: {
  icon: typeof AlertTriangle;
  label: string;
  active: boolean;
  color?: "red" | "amber";
}) {
  const activeClass =
    color === "red"
      ? "text-red-400 bg-red-500/10"
      : "text-amber-400 bg-amber-500/10";
  const dotClass =
    color === "red" ? "bg-red-400 animate-pulse" : "bg-amber-400 animate-pulse";

  return (
    <div
      className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs font-medium ${
        active ? activeClass : "text-zinc-600 bg-zinc-800/30"
      }`}
    >
      <Icon className="w-3 h-3" />
      {label}
      <span
        className={`ml-auto w-1.5 h-1.5 rounded-full ${
          active ? dotClass : "bg-zinc-700"
        }`}
      />
    </div>
  );
}

export function HoistPanel({ direction, failure, stalled, helping, trackingActive }: Props) {
  const cfg = HOIST_CONFIG[direction] ?? HOIST_CONFIG.N;
  const Icon = cfg.icon;

  return (
    <div className="flex flex-col gap-1.5 shrink-0">
      <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
        Hoist Output
      </h2>

      <div
        className={`flex flex-col rounded-lg border ${cfg.bg} ${cfg.border} ${cfg.glow} transition-all duration-300`}
      >
        {/* Track-loss warning */}
        {!trackingActive && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border-b border-red-500/20 rounded-t-lg text-xs font-medium text-red-400">
            <EyeOff className="w-3.5 h-3.5" />
            Track lost — hoist halted
          </div>
        )}

        {/* Main direction indicator */}
        <div className="flex flex-col items-center justify-center gap-0.5 py-3 px-3">
          <div className={`p-2 rounded-xl ${cfg.iconBg} transition-colors duration-300`}>
            <Icon className={`w-6 h-6 ${cfg.text}`} strokeWidth={2.5} />
          </div>
          <span className={`text-xl font-bold font-mono tracking-widest ${cfg.text}`}>
            {cfg.label}
          </span>
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
            {cfg.description}
          </span>
        </div>

        {/* Status flags */}
        <div className="grid grid-cols-2 gap-1 p-2 border-t border-zinc-700/30">
          <StatusRow icon={AlertTriangle} label="Failure" active={failure} />
          <StatusRow icon={Pause} label="Stalled" active={stalled} />
          <StatusRow icon={HandHelping} label="Assisting" active={helping} />
          <StatusRow icon={EyeOff} label="Track Lost" active={!trackingActive} color="amber" />
        </div>
      </div>
    </div>
  );
}
