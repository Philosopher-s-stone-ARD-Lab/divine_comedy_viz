/**
 * Three.js helper utilities for the Divine Comedy 3D Journey visualization.
 */
import * as THREE from 'three';
import { journeyColorScale } from './d3Helpers.js';
import * as d3 from 'd3';

// ─── Constants ──────────────────────────────────────────────────────

const SCALE_XZ = 4.0;
const SCALE_Y = 5.0;

export const REALM_3D_CONFIG = {
  Inferno: {
    yMin: -2.1, yMax: -0.1,
    color: 0x8B0000,
    particleColor: 0xFF4500,
    particleCount: 400,
    particleSpread: 8,
  },
  Purgatorio: {
    yMin: 0.1, yMax: 1.7,
    color: 0x8B7355,
    particleColor: 0xA0926B,
    particleCount: 250,
    particleSpread: 6,
  },
  Paradiso: {
    yMin: 5.0, yMax: 6.8,
    color: 0x1E90FF,
    particleColor: 0xFFD700,
    particleCount: 500,
    particleSpread: 10,
  },
};

// ─── Coordinate Mapping ─────────────────────────────────────────────

/**
 * Map a canto's raw x/y/z to scaled 3D world coordinates.
 * Adds small jitter to prevent overlapping nodes.
 */
export function mapCantoTo3D(canto, index) {
  // Deterministic jitter based on global_canto to separate overlapping nodes
  const jitterSeed = canto.global_canto * 137.5;
  const jx = (Math.sin(jitterSeed) * 0.08);
  const jz = (Math.cos(jitterSeed) * 0.08);

  return new THREE.Vector3(
    canto.x * SCALE_XZ + jx,
    canto.y * SCALE_Y,
    canto.z * SCALE_XZ + jz
  );
}

// ─── Canto Nodes (InstancedMesh) ────────────────────────────────────

/**
 * Create an InstancedMesh of sphere nodes for a set of cantos.
 * Returns the mesh with .userData.cantos set for raycasting lookups.
 */
export function createCantoNodes(cantos, allJourneyData) {
  const wordExtent = d3.extent(allJourneyData, d => d.word_count);
  const sizeScale = d3.scaleSqrt().domain(wordExtent).range([0.07, 0.22]);
  const colorScale = journeyColorScale();

  const geometry = new THREE.SphereGeometry(1, 16, 12);
  const material = new THREE.MeshStandardMaterial({
    roughness: 0.3,
    metalness: 0.2,
  });

  const mesh = new THREE.InstancedMesh(geometry, material, cantos.length);
  const dummy = new THREE.Object3D();
  const color = new THREE.Color();

  cantos.forEach((canto, i) => {
    const pos = mapCantoTo3D(canto, i);
    const size = sizeScale(canto.word_count);

    dummy.position.copy(pos);
    dummy.scale.set(size, size, size);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);

    // Color from journey gradient
    color.set(colorScale(canto.global_canto));
    mesh.setColorAt(i, color);
  });

  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;

  // Add emissive properties for sentiment-based glow
  // High positive sentiment → gold emissive, high negative → red emissive
  mesh.material.emissive = new THREE.Color(0x000000);
  mesh.material.emissiveIntensity = 0;

  // Store canto data for raycaster lookups
  mesh.userData.cantos = cantos;

  return mesh;
}

// ─── Journey Path (TubeGeometry) ────────────────────────────────────

/**
 * Create the connecting tube path through all cantos.
 */
export function createJourneyPath(cantos) {
  const points = cantos.map((c, i) => mapCantoTo3D(c, i));
  const curve = new THREE.CatmullRomCurve3(points);
  const tubeSegments = Math.max(200, cantos.length * 3);
  const tubeGeometry = new THREE.TubeGeometry(curve, tubeSegments, 0.025, 8, false);

  // Vertex colors matching the journey gradient
  const colorScale = journeyColorScale();
  const colors = [];
  const posAttr = tubeGeometry.attributes.position;
  for (let i = 0; i < posAttr.count; i++) {
    const t = i / posAttr.count;
    const cantoNum = Math.floor(t * 99) + 1;
    const c = new THREE.Color(colorScale(cantoNum));
    colors.push(c.r, c.g, c.b);
  }
  tubeGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

  const material = new THREE.MeshBasicMaterial({
    vertexColors: true,
    transparent: true,
    opacity: 0.5,
  });

  return new THREE.Mesh(tubeGeometry, material);
}

// ─── Realm Backdrops ────────────────────────────────────────────────

/**
 * Create wireframe backdrop shapes for each realm.
 */
export function createRealmBackdrop(realmName) {
  const config = REALM_3D_CONFIG[realmName];
  const group = new THREE.Group();
  const yCenter = (config.yMin + config.yMax) / 2;
  const yHeight = config.yMax - config.yMin;

  if (realmName === 'Inferno') {
    // Inverted cone (funnel descending)
    const geom = new THREE.ConeGeometry(4, yHeight + 2, 32, 1, true);
    const mat = new THREE.MeshBasicMaterial({
      color: config.color, wireframe: true, transparent: true, opacity: 0.05,
    });
    const cone = new THREE.Mesh(geom, mat);
    cone.position.y = yCenter;
    cone.rotation.x = Math.PI; // Invert
    group.add(cone);
  } else if (realmName === 'Purgatorio') {
    // Upright mountain cone
    const geom = new THREE.ConeGeometry(3, yHeight + 2, 32, 1, true);
    const mat = new THREE.MeshBasicMaterial({
      color: config.color, wireframe: true, transparent: true, opacity: 0.05,
    });
    const cone = new THREE.Mesh(geom, mat);
    cone.position.y = yCenter;
    group.add(cone);
  } else if (realmName === 'Paradiso') {
    // Concentric celestial spheres
    [1.5, 2.5, 3.5].forEach(radius => {
      const geom = new THREE.SphereGeometry(radius, 24, 16);
      const mat = new THREE.MeshBasicMaterial({
        color: config.color, wireframe: true, transparent: true, opacity: 0.03,
      });
      const sphere = new THREE.Mesh(geom, mat);
      sphere.position.y = yCenter;
      group.add(sphere);
    });
  }

  return group;
}

// ─── Particle Systems ───────────────────────────────────────────────

/**
 * Create a particle system for a realm's atmosphere.
 */
export function createParticles(realmName) {
  const config = REALM_3D_CONFIG[realmName];
  const count = config.particleCount;
  const positions = new Float32Array(count * 3);
  const spread = config.particleSpread;

  for (let i = 0; i < count; i++) {
    positions[i * 3] = (Math.random() - 0.5) * spread;
    positions[i * 3 + 1] = config.yMin + Math.random() * (config.yMax - config.yMin);
    positions[i * 3 + 2] = (Math.random() - 0.5) * spread;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));

  const material = new THREE.PointsMaterial({
    color: config.particleColor,
    size: realmName === 'Paradiso' ? 0.04 : 0.03,
    transparent: true,
    opacity: 0.35,
    sizeAttenuation: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  const points = new THREE.Points(geometry, material);
  points.userData.realmName = realmName;
  points.userData.config = config;
  return points;
}

/**
 * Animate particles in the render loop.
 */
export function updateParticles(particleSystems, time) {
  particleSystems.forEach(ps => {
    const realmName = ps.userData.realmName;
    const config = ps.userData.config;
    const posAttr = ps.geometry.attributes.position;

    if (realmName === 'Inferno') {
      // Falling embers — slow downward drift
      for (let i = 0; i < posAttr.count; i++) {
        posAttr.array[i * 3 + 1] -= 0.003;
        if (posAttr.array[i * 3 + 1] < config.yMin) {
          posAttr.array[i * 3 + 1] = config.yMax;
          posAttr.array[i * 3] = (Math.random() - 0.5) * config.particleSpread;
          posAttr.array[i * 3 + 2] = (Math.random() - 0.5) * config.particleSpread;
        }
      }
      posAttr.needsUpdate = true;
    } else if (realmName === 'Purgatorio') {
      // Drifting dust — gentle horizontal sway
      for (let i = 0; i < posAttr.count; i++) {
        posAttr.array[i * 3] += Math.sin(time * 0.0003 + i) * 0.0005;
        posAttr.array[i * 3 + 1] += 0.001;
        if (posAttr.array[i * 3 + 1] > config.yMax) {
          posAttr.array[i * 3 + 1] = config.yMin;
        }
      }
      posAttr.needsUpdate = true;
    } else if (realmName === 'Paradiso') {
      // Twinkling stars — opacity shimmer
      ps.material.opacity = 0.25 + Math.sin(time * 0.001) * 0.15;
      // Gentle rotation
      ps.rotation.y += 0.0002;
    }
  });
}

// ─── Highlight Sphere ───────────────────────────────────────────────

/**
 * Create a highlight sphere used to indicate the hovered canto.
 */
export function createHighlightSphere() {
  const geometry = new THREE.SphereGeometry(1, 20, 14);
  const material = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.25,
    emissive: 0xffffff,
    emissiveIntensity: 0.6,
    roughness: 0.1,
    metalness: 0.0,
    depthWrite: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.visible = false;
  return mesh;
}

// ─── Scene Disposal ─────────────────────────────────────────────────

/**
 * Dispose all geometries and materials in a scene to prevent memory leaks.
 */
export function disposeScene(scene) {
  scene.traverse(obj => {
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose());
      } else {
        obj.material.dispose();
      }
    }
  });
}
