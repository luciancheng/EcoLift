import { useEffect, useRef, useCallback, useState } from "react";
import type { Socket } from "socket.io-client";

export function useWebRTC(socket: Socket | null, connected: boolean) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [streaming, setStreaming] = useState(false);

  const startStream = useCallback(async () => {
    if (!socket || !connected) return;

    pcRef.current?.close();

    const pc = new RTCPeerConnection({
      iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
    });
    pcRef.current = pc;

    pc.addTransceiver("video", { direction: "recvonly" });

    pc.ontrack = (event) => {
      if (videoRef.current && event.streams[0]) {
        videoRef.current.srcObject = event.streams[0];
        setStreaming(true);
      }
    };

    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "failed" || pc.connectionState === "disconnected") {
        setStreaming(false);
      }
    };

    const answerHandler = async (data: { sdp: string; type: RTCSdpType }) => {
      try {
        await pc.setRemoteDescription(new RTCSessionDescription(data));
      } catch (e) {
        console.error("Failed to set remote description:", e);
      }
    };
    socket.on("answer", answerHandler);

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    // Wait for ICE gathering to complete before sending the offer
    await new Promise<void>((resolve) => {
      if (pc.iceGatheringState === "complete") {
        resolve();
      } else {
        const check = () => {
          if (pc.iceGatheringState === "complete") {
            pc.removeEventListener("icegatheringstatechange", check);
            resolve();
          }
        };
        pc.addEventListener("icegatheringstatechange", check);
      }
    });

    socket.emit("offer", {
      sdp: pc.localDescription!.sdp,
      type: pc.localDescription!.type,
    });
  }, [socket, connected]);

  useEffect(() => {
    if (connected) startStream();
    return () => {
      pcRef.current?.close();
      pcRef.current = null;
      setStreaming(false);
    };
  }, [connected, startStream]);

  return { videoRef, streaming, reconnect: startStream };
}
