export interface Telemetry {
  dx: number;
  dy: number;
  velocity: number;
  assistance: number;
  failure: boolean;
  stalled: boolean;
  helping: boolean;
  hoist_direction: "U" | "D" | "N";
  failure_y_threshold: number;
  tracking_active: boolean;
  pi_connected: boolean;
  lower_hsv: [number, number, number];
  upper_hsv: [number, number, number];
}

export interface TelemetryPoint {
  time: number;
  dy: number;
  assistance: number;
}
