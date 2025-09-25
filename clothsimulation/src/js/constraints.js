import { vec3 } from './utils.js';

export function makeConstraints(pos, nx, ny, stiffness = 1.0, shearStiffness = 0.5, bendStiffness = 0.1) {
  const constraints = [];

  function index(i, j) {
    return j * (nx + 1) + i;
  }

  function addConstraint(i0, i1, stiffness = 1) {
    const restLength = vec3.length(vec3.sub(pos[i1], pos[i0]));
    constraints.push({
      i0, i1, restLength, stiffness,
      
      project(p) {
        const p0 = p[i0], p1 = p[i1];
        const dir = vec3.sub(p1, p0);
        const len = vec3.length(dir);
        if (len === 0) return;
        const diff = (len - restLength) / len;
        const correction = vec3.scale(dir, 0.5 * diff*stiffness);
        p[i0]= vec3.add(p0, correction);
        p[i1] = vec3.sub(p1, correction);
      }
    });
  }

  for (let j = 0; j <= ny; j++) {
    for (let i = 0; i <= nx; i++) {
      // Stretch/ Structural constraints
      if (i < nx) addConstraint(index(i, j), index(i + 1, j), stiffness);
      if (j < ny) addConstraint(index(i, j), index(i, j + 1), stiffness);
      
      // Shearing constraints
      if (i < nx && j < ny) {
        addConstraint(index(i, j), index(i + 1, j + 1), shearStiffness);
        addConstraint(index(i + 1, j), index(i, j + 1), shearStiffness);
      }

      // Bending constraints (2 apart)
      if (i + 2 <= nx) addConstraint(index(i, j), index(i + 2, j), bendStiffness);
      if (j + 2 <= ny) addConstraint(index(i, j), index(i, j + 2), bendStiffness);
    }
  }

  return constraints;
}