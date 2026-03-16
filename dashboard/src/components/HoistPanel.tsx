import { ArrowUp, ArrowDown, Minus, AlertTriangle, Pause, HandHelping } from "lucide-react";

interface Props {
  direction: "U" | "D" | "N";
  failure: boolean;
  stalled: boolean;
  helping: boolean;
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
}: {
  icon: typeof AlertTriangle;
  label: string;
  active: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs font-medium ${
        active
          ? "text-red-400 bg-red-500/10"
          : "text-zinc-600 bg-zinc-800/30"
      }`}
    >
      <Icon className="w-3 h-3" />
      {label}
      <span
        className={`ml-auto w-1.5 h-1.5 rounded-full ${
          active ? "bg-red-400 animate-pulse" : "bg-zinc-700"
        }`}
      />
    </div>
  );
}

export function HoistPanel({ direction, failure, stalled, helping }: Props) {
  const cfg = HOIST_CONFIG[direction] ?? HOIST_CONFIG.N;
  const Icon = cfg.icon;

  return (
    <div className="flex flex-col gap-1.5 min-h-0 flex-1">
      <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
        Hoist Output
      </h2>

      <div
        className={`flex-1 flex flex-col rounded-lg border ${cfg.bg} ${cfg.border} ${cfg.glow} transition-all duration-300`}
      >
        {/* Main direction indicator */}
        <div className="flex-1 flex flex-col items-center justify-center gap-1 p-3">
          <div className={`p-3 rounded-xl ${cfg.iconBg} transition-colors duration-300`}>
            <Icon className={`w-8 h-8 ${cfg.text}`} strokeWidth={2.5} />
          </div>
          <span className={`text-2xl font-bold font-mono tracking-widest ${cfg.text}`}>
            {cfg.label}
          </span>
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
            {cfg.description}
          </span>
        </div>

        {/* Status flags */}
        <div className="flex flex-col gap-1 p-2 border-t border-zinc-700/30">
          <StatusRow icon={AlertTriangle} label="Failure" active={failure} />
          <StatusRow icon={Pause} label="Stalled" active={stalled} />
          <StatusRow icon={HandHelping} label="Assisting" active={helping} />
        </div>
      </div>
    </div>
  );
}
