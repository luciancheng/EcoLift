import { RefObject, useState } from "react";
import { Crosshair, Video, VideoOff } from "lucide-react";
import type { Socket } from "socket.io-client";

interface Props {
  videoRef: RefObject<HTMLVideoElement | null>;
  socket: Socket | null;
  streaming: boolean;
  onReconnect: () => void;
}

export function VideoFeed({ videoRef, socket, streaming, onReconnect }: Props) {
  const [pickMode, setPickMode] = useState(false);

  const handleClick = (e: React.MouseEvent<HTMLVideoElement>) => {
    if (!pickMode || !socket) return;

    const video = e.currentTarget;
    const rect = video.getBoundingClientRect();
    const x = Math.round(
      ((e.clientX - rect.left) / rect.width) * video.videoWidth
    );
    const y = Math.round(
      ((e.clientY - rect.top) / rect.height) * video.videoHeight
    );

    socket.emit("hsv_pick", { x, y });
    setPickMode(false);
  };

  return (
    <div className="flex flex-col gap-1.5 min-h-0">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Live Feed
        </h2>
        <div className="flex gap-1.5">
          <button
            onClick={() => setPickMode(!pickMode)}
            className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-colors ${
              pickMode
                ? "bg-blue-500 text-white"
                : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
            }`}
          >
            <Crosshair className="w-3 h-3" />
            {pickMode ? "Click video to pick" : "HSV Pick"}
          </button>
          <button
            onClick={onReconnect}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors"
          >
            <Video className="w-3 h-3" />
            Reconnect
          </button>
        </div>
      </div>

      <div
        className={`relative rounded-lg overflow-hidden bg-zinc-900 border min-h-0 ${
          pickMode ? "border-blue-500 cursor-crosshair" : "border-zinc-800"
        }`}
      >
        {!streaming && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 z-10 bg-zinc-900/90">
            <VideoOff className="w-8 h-8 text-zinc-600" />
            <p className="text-xs text-zinc-500">Waiting for video stream...</p>
          </div>
        )}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          onClick={handleClick}
          className="w-full max-h-[55vh] object-contain bg-black"
        />
        {pickMode && (
          <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-blue-500/90 rounded text-[11px] text-white font-medium">
            Click on the object to track
          </div>
        )}
      </div>
    </div>
  );
}
