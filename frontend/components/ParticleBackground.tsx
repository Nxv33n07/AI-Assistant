"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function GoldenParticles({ count = 1800 }: { count?: number }) {
  const pointsRef = useRef<THREE.Points>(null);

  const [positions, colors] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 2.5 + Math.random() * 5;
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
      // Gold to warm white palette
      const t = Math.random();
      col[i * 3] = 0.78 + t * 0.22; // R
      col[i * 3 + 1] = 0.63 + t * 0.18; // G
      col[i * 3 + 2] = 0.18 + t * 0.42; // B
    }
    return [pos, col];
  }, [count]);

  useFrame((_, delta) => {
    if (!pointsRef.current) return;
    pointsRef.current.rotation.y += delta * 0.025;
    pointsRef.current.rotation.x += delta * 0.008;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.025}
        vertexColors
        transparent
        opacity={0.75}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}

function NebulaRing() {
  const ringRef = useRef<THREE.Points>(null);

  const positions = useMemo(() => {
    const pos = new Float32Array(600 * 3);
    for (let i = 0; i < 600; i++) {
      const angle = (i / 600) * Math.PI * 2;
      const r = 3.2 + (Math.random() - 0.5) * 0.6;
      const tilt = (Math.random() - 0.5) * 0.3;
      pos[i * 3] = r * Math.cos(angle);
      pos[i * 3 + 1] = tilt;
      pos[i * 3 + 2] = r * Math.sin(angle);
    }
    return pos;
  }, []);

  useFrame((_, delta) => {
    if (ringRef.current) ringRef.current.rotation.y -= delta * 0.04;
  });

  return (
    <points ref={ringRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color="#e8c86a"
        transparent
        opacity={0.35}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}

function Scene() {
  return (
    <>
      <GoldenParticles count={1800} />
      <NebulaRing />
    </>
  );
}

export default function ParticleBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      <Canvas
        camera={{ position: [0, 0, 1], fov: 75 }}
        gl={{ antialias: false }}
        onCreated={() => {
          // Suppress the THREE.Clock deprecation warning from r3f internals
          const orig = console.warn.bind(console);
          console.warn = (...args: unknown[]) => {
            if (typeof args[0] === "string" && args[0].includes("THREE.Clock"))
              return;
            orig(...args);
          };
        }}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
