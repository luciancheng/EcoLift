import { useState, useEffect } from "react";
import { RotateCcw, Sliders, Send, Bug } from "lucide-react";
import type { Socket } from "socket.io-client";
import type { Telemetry } from "../types";

interface Props {
  socket: Socket | null;
  telemetry: Telemetry | null;
  showDebug: boolean;
  onToggleDebug: (v: boolean) => void;
}

export function ControlPanel({ socket, telemetry, showDebug, onToggleDebug }: Props) {
  const [lowerH, setLowerH] = useState(0);
  const [lowerS, setLowerS] = useState(120);
  const [lowerV, setLowerV] = useState(70);
  const [upperH, setUpperH] = useState(10);
  const [upperS, setUpperS] = useState(255);
  const [upperV, setUpperV] = useState(255);

  useEffect(() => {
    if (telemetry) {
      setLowerH(telemetry.lower_hsv[0]);
      setLowerS(telemetry.lower_hsv[1]);
      setLowerV(telemetry.lower_hsv[2]);
      setUpperH(telemetry.upper_hsv[0]);
      setUpperS(telemetry.upper_hsv[1]);
      setUpperV(telemetry.upper_hsv[2]);
    }
  }, [telemetry?.lower_hsv[0], telemetry?.lower_hsv[1], telemetry?.lower_hsv[2],
      telemetry?.upper_hsv[0], telemetry?.upper_hsv[1], telemetry?.upper_hsv[2]]);

  const handleApplyHSV = () => {
    if (!socket) return;
    socket.emit("set_hsv", {
      lower: [lowerH, lowerS, lowerV],
      upper: [upperH, upperS, upperV],
    });
  };

  const handleRecalibrate = () => {
    if (!socket) return;
    socket.emit("recalibrate");
  };

  const handleToggleDebug = () => {
    const next = !showDebug;
    onToggleDebug(next);
    socket?.emit("toggle_overlay", { enabled: next });
  };

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
        Controls
      </h2>

      <div className="p-3 rounded-lg bg-zinc-800/30 border border-zinc-700/50">
        <div className="flex items-center gap-2 mb-2">
          <Sliders className="w-3.5 h-3.5 text-blue-400" />
          <p className="text-xs font-medium text-zinc-300">HSV Range</p>
        </div>

        <div className="grid grid-cols-2 gap-2 mb-2">
          <div>
            <p className="text-[10px] text-zinc-500 mb-1">Lower Bound</p>
            <div className="flex gap-1">
              <HSVInput label="H" value={lowerH} max={179} onChange={setLowerH} />
              <HSVInput label="S" value={lowerS} max={255} onChange={setLowerS} />
              <HSVInput label="V" value={lowerV} max={255} onChange={setLowerV} />
            </div>
          </div>
          <div>
            <p className="text-[10px] text-zinc-500 mb-1">Upper Bound</p>
            <div className="flex gap-1">
              <HSVInput label="H" value={upperH} max={179} onChange={setUpperH} />
              <HSVInput label="S" value={upperS} max={255} onChange={setUpperS} />
              <HSVInput label="V" value={upperV} max={255} onChange={setUpperV} />
            </div>
          </div>
        </div>

        <div className="flex gap-1.5">
          <button
            onClick={handleApplyHSV}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors flex-1 justify-center"
          >
            <Send className="w-3 h-3" />
            Apply
          </button>
          <button
            onClick={handleRecalibrate}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium bg-zinc-700 hover:bg-zinc-600 text-zinc-200 transition-colors flex-1 justify-center"
          >
            <RotateCcw className="w-3 h-3" />
            Recalibrate
          </button>
        </div>
      </div>

      <button
        onClick={handleToggleDebug}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
          showDebug
            ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
            : "bg-zinc-800/50 border-zinc-700/50 text-zinc-500 hover:text-zinc-300"
        }`}
      >
        <Bug className="w-3.5 h-3.5" />
        Debug Overlay (dx/dy)
        <span
          className={`ml-auto text-[10px] font-semibold ${
            showDebug ? "text-amber-400" : "text-zinc-600"
          }`}
        >
          {showDebug ? "ON" : "OFF"}
        </span>
      </button>
    </div>
  );
}

function HSVInput({
  label,
  value,
  max,
  onChange,
}: {
  label: string;
  value: number;
  max: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex-1">
      <label className="text-[9px] text-zinc-600 uppercase">{label}</label>
      <input
        type="number"
        min={0}
        max={max}
        value={value}
        onChange={(e) => onChange(Math.min(max, Math.max(0, Number(e.target.value))))}
        className="w-full px-1.5 py-1 rounded bg-zinc-900 border border-zinc-700 text-zinc-200 text-xs font-mono focus:outline-none focus:border-blue-500 transition-colors"
      />
    </div>
  );
}
