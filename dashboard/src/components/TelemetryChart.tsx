import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import type { TelemetryPoint } from "../types";

interface Props {
  history: TelemetryPoint[];
}

export function TelemetryChart({ history }: Props) {
  if (history.length < 2) {
    return (
      <div className="flex flex-col gap-1.5 flex-1 min-h-[120px]">
        <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Bar Height
        </h2>
        <div className="flex-1 flex items-center justify-center rounded-lg bg-zinc-800/30 border border-zinc-700/50 text-zinc-500 text-xs min-h-0">
          Collecting data...
        </div>
      </div>
    );
  }

  const now = history[history.length - 1].time;
  const chartData = history.map((p) => ({
    t: parseFloat((p.time - now).toFixed(1)),
    dy: p.dy,
  }));

  return (
    <div className="flex flex-col gap-1.5 flex-1 min-h-[120px]">
      <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
        Bar Height (dy)
      </h2>

      <div className="flex-1 p-2.5 rounded-lg bg-zinc-800/30 border border-zinc-700/50 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              dataKey="t"
              stroke="#52525b"
              tick={{ fontSize: 9, fill: "#71717a" }}
              tickFormatter={(v: number) => `${v}s`}
            />
            <YAxis
              stroke="#52525b"
              tick={{ fontSize: 9, fill: "#71717a" }}
              domain={[-700, 100]}
              width={35}
            />
            <ReferenceLine y={0} stroke="#52525b" strokeDasharray="3 3" />
            <ReferenceLine y={-300} stroke="#ef4444" strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="dy"
              stroke="#22c55e"
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
