export interface Telemetry {
  dx: number;
  dy: number;
  velocity: number;
  assistance: number;
  failure: boolean;
  stalled: boolean;
  helping: boolean;
  hoist_direction: "U" | "D" | "N";
  lower_hsv: [number, number, number];
  upper_hsv: [number, number, number];
}

export interface TelemetryPoint {
  time: number;
  dy: number;
  assistance: number;
}
