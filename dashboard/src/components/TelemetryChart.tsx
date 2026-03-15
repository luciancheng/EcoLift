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
      <div className="flex flex-col gap-1.5">
        <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          History
        </h2>
        <div className="p-4 rounded-lg bg-zinc-800/30 border border-zinc-700/50 text-center text-zinc-500 text-xs">
          Collecting data...
        </div>
      </div>
    );
  }

  const now = history[history.length - 1].time;
  const chartData = history.map((p) => ({
    t: parseFloat((p.time - now).toFixed(1)),
    dy: p.dy,
    u: parseFloat((p.assistance * 100).toFixed(1)),
  }));

  return (
    <div className="flex flex-col gap-1.5 min-h-0">
      <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
        History
      </h2>

      <div className="grid grid-cols-2 gap-2">
        <div className="p-2.5 rounded-lg bg-zinc-800/30 border border-zinc-700/50">
          <p className="text-[10px] text-zinc-500 mb-1 font-medium">
            Bar Height (dy)
          </p>
          <ResponsiveContainer width="100%" height={120}>
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
                domain={[-500, 100]}
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

        <div className="p-2.5 rounded-lg bg-zinc-800/30 border border-zinc-700/50">
          <p className="text-[10px] text-zinc-500 mb-1 font-medium">
            Assistance (%)
          </p>
          <ResponsiveContainer width="100%" height={120}>
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
                domain={[0, 100]}
                width={35}
              />
              <Line
                type="monotone"
                dataKey="u"
                stroke="#f59e0b"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
