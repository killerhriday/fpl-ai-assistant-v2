import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Environment, Grid } from '@react-three/drei'
import { useRef } from 'react'

// The 'Football' - A detailed sphere with a subtle wireframe overlay
function Football({ position, scale }) {
  const mesh = useRef()
  const wireMesh = useRef()
  
  useFrame((state, delta) => {
    if (mesh.current) {
      mesh.current.rotation.x += delta * 0.2
      mesh.current.rotation.y += delta * 0.3
    }
    if (wireMesh.current) {
      wireMesh.current.rotation.x += delta * 0.2
      wireMesh.current.rotation.y += delta * 0.3
    }
  })
  return (
    <Float speed={1.5} rotationIntensity={0.5} floatIntensity={1}>
      <mesh ref={mesh} position={position} scale={scale}>
        <icosahedronGeometry args={[1, 2]} />
        <meshStandardMaterial color="#1a1a1a" roughness={0.3} metalness={0.8} />
      </mesh>
      {/* Wireframe shell to give it that tactical/data feel */}
      <mesh ref={wireMesh} position={position} scale={scale * 1.01}>
        <icosahedronGeometry args={[1, 2]} />
        <meshBasicMaterial color="#00ff87" wireframe={true} transparent opacity={0.15} />
      </mesh>
    </Float>
  )
}

// 3D Data Bars (representing FPL points/stats)
function DataBar({ position, height, delay }) {
  const mesh = useRef()
  
  useFrame(({ clock }) => {
    // Subtle breathing animation for data bars
    const t = clock.getElapsedTime() + delay
    if (mesh.current) {
      mesh.current.scale.y = 1 + Math.sin(t) * 0.05
    }
  })
  
  return (
    <mesh ref={mesh} position={[position[0], position[1] + height/2, position[2]]}>
      <boxGeometry args={[0.5, height, 0.5]} />
      <meshStandardMaterial color="#222222" roughness={0.1} metalness={0.9} />
      {/* Glowing top cap */}
      <mesh position={[0, height/2 + 0.01, 0]} rotation={[-Math.PI/2, 0, 0]}>
         <planeGeometry args={[0.5, 0.5]} />
         <meshBasicMaterial color="#00ff87" transparent opacity={0.5} />
      </mesh>
    </mesh>
  )
}

// Tactical Pitch Grid
function TacticalPitch() {
  return (
    <group position={[0, -4, 0]}>
      <Grid 
        args={[40, 40]} 
        cellSize={1} 
        cellThickness={1} 
        cellColor="#222222" 
        sectionSize={5} 
        sectionThickness={1.5} 
        sectionColor="#00ff87" 
        fadeDistance={25} 
        fadeStrength={1} 
      />
    </group>
  )
}

export default function Background3D() {
  return (
    <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, pointerEvents: 'none' }}>
      <Canvas camera={{ position: [0, 2, 12], fov: 45 }}>
        <color attach="background" args={['#030504']} />
        <fog attach="fog" args={['#030504', 10, 25]} />
        
        {/* Cinematic FPL Lighting: Stark white with subtle green rim lights */}
        <ambientLight intensity={0.5} color="#ffffff" />
        <directionalLight position={[10, 10, 5]} intensity={1.5} color="#ffffff" />
        <spotLight position={[-10, 5, -5]} intensity={150} color="#00ff87" distance={30} angle={0.5} penumbra={1} />
        
        {/* Floating Footballs / Spheres */}
        <Football position={[-5, 0, -4]} scale={2} />
        <Football position={[6, 3, -8]} scale={1.2} />
        
        {/* Data Bars representing player forms/points */}
        <DataBar position={[3, -4, -2]} height={3} delay={0} />
        <DataBar position={[4, -4, -3]} height={5} delay={1} />
        <DataBar position={[5, -4, -1]} height={2} delay={2} />
        
        <DataBar position={[-6, -4, -6]} height={4} delay={0.5} />
        <DataBar position={[-7, -4, -5]} height={6} delay={1.5} />
        <DataBar position={[-5, -4, -8]} height={3.5} delay={0.8} />
        
        {/* Glowing Pitch Floor */}
        <TacticalPitch />
        
        <Environment preset="city" />
      </Canvas>
    </div>
  )
}
