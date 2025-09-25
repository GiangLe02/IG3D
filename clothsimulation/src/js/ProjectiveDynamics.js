import * as THREE from 'three';
import { makeConstraints } from './constraints.js';
import { vec3, zeros } from './utils.js';

let positions = [], velocities = [], invMass = [];
let constraints = [];
let mesh, geometry;
const gravity = [0, -9.8, 0];
const dt = 1 / 120;
const frictionCoefficient = 0.05;
const dampingCoef = 0.9;

export function initCloth(nx, ny, size) {
    positions = [];
    velocities = [];
    invMass = [];
  
    for (let j = 0; j <= ny; j++) {
      for (let i = 0; i <= nx; i++) {
        const x = (i / nx - 0.5) * size;
        const y = (j / ny - 0.5) * size;
        const z = 0;
        positions.push([x, y, z]);
        velocities.push([0, 0, 0]);
        invMass.push(j === ny ? 0 : 1); // pin top row
        }
    }
    constraints = makeConstraints(positions, nx, ny);

    const planeGeo = new THREE.PlaneGeometry(size, size, nx, ny);
    geometry = planeGeo;
    const mat = new THREE.MeshStandardMaterial({ color: 0x7777ff, side: THREE.DoubleSide, wireframe: false });
    mesh = new THREE.Mesh(geometry, mat);

    return { mesh, geometry };
}

export function stepSimulation(spherePos=null, sphereRadius=0) {
  const internalForces = computeInternalForces();
  const nextPos = positions.map((p, i) => {
    const externalForce = vec3.scale(gravity, invMass[i]);
    const internalForce = internalForces[i] || vec3Zero();
    const totalForce = vec3.add(externalForce, internalForce);
    return vec3.add(p, vec3.add(vec3.scale(velocities[i], dt), vec3.scale(totalForce, dt * dt)));
  });

  for (let iter = 0; iter < 10; iter++) {
    for (const c of constraints) {
      c.project(nextPos); // regular distance/ spring constraints
    }
  }

  // Collision handling with frictional contact
  if (spherePos) {
    for (let i = 0; i < nextPos.length; i++) {
      const p = nextPos[i];
      const delta = vec3.sub(p, spherePos);
      const d = vec3.length(delta);
      if (d < sphereRadius + 0.02) {
        // apply contact force
        // const correction = vec3.scale(delta, (sphereRadius - d) / d);
        // nextPos[i] = vec3.add(p, correction);

        // Calculate normal and tangential velocity
        const v = velocities[i];
        const n = vec3.normalize(delta);  // Normal of the surface (from sphere center)

        const uN = vec3.dot(v, n); // normal velocity
        const uT = vec3.sub(v, vec3.scale(n, uN));  // Tangential velocity
        const uT_mag = vec3.length(uT);

        let rN = Math.max(0, 1.0 * (sphereRadius - d + 0.02)); // Hard normal contact
        let uNew = v.slice(); // Start with original velocity
        
        // Apply Signorini-Coulomb contact logic
        if (uN > 0 && rN === 0) {
          // Take off: No contact force
          continue;
        } else if (uT_mag < frictionCoefficient * rN && uN === 0) {
          // Stick: Zero tangential velocity and friction is static
          velocities[i] = vec3.sub(v, uT);  // Cancel tangential velocity
        } else if (uN === 0 && Math.abs(uT_mag) > 1e-6) {
          // Slip: Apply dynamic friction opposing tangential velocity
          const tDir = vec3.normalize(uT);
          const rT = vec3.scale(tDir, -frictionCoefficient * rN);
          const frictionImpulse = vec3.scale(rT, dt * invMass[i]);
          velocities[i] = vec3.add(v, frictionImpulse);
        }

        // Recompute new position based on updated velocity
        nextPos[i] = vec3.add(positions[i], vec3.scale(velocities[i], dt));  
        // Apply normal correction to resolve interpenetration
        const correction = vec3.scale(n, rN);
        nextPos[i] = vec3.add(p, correction);
      }
    }
  }

  // Update positions and velocities
  for (let i = 0; i < positions.length; i++) {
    if (invMass[i] > 0) {
      velocities[i] = vec3.scale(vec3.sub(nextPos[i], positions[i]), 1 / dt);
      positions[i] = nextPos[i];
    }
  }
}

export function getPositions() {
  return positions.flat();
}

function computeInternalForces() {
  const forces = Array(positions.length).fill(null).map(() => [0, 0, 0]);

  for (const c of constraints) {
    const { i0, i1, restLength, stiffness } = c;

    const pi = positions[i0];
    const pj = positions[i1];

    const dir = vec3.sub(pj, pi); // This is where it previously failed
    const len = vec3.length(dir);
    if (len === 0) continue;

    // Spring forces
    //Fs = ks.(p1-p0)/len.(len-resLen)
    const normDir = vec3.scale(dir, 1 / len);
    const magnitude = stiffness * (len - restLength);
    const springForce = vec3.scale(normDir, magnitude);

    // Damping forces
    // Fd = kd.(v1-v0).(p1-p0)/len
    const difVel = vec3.sub(velocities[i1], velocities[i0]);
    const dampingMag = dampingCoef * vec3.dot(difVel, normDir);
    const dampingForce = vec3.scale(normDir ,dampingMag);

    // Apply forces
    forces[i0] = vec3.add(springForce, dampingForce);
    forces[i1] = vec3.sub(forces[i1], vec3.add(springForce, dampingForce));
  }

  return forces;
}

export function vec3Zero() {
    return [0, 0, 0];
}
