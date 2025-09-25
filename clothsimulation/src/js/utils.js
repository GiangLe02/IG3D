export const vec3 = {
    add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
    sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
    scale: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
    length: (a) => Math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2),
    normalize: (a) => {
        const len = Math.sqrt(a[0]**2 + a[1]**2 + a[2]**2);
        return len > 0 ? [a[0] / len, a[1] / len, a[2] / len] : [0, 0, 0];
    },
    dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],  // Dot product
};

export const zeros = (n) => Array(n).fill([0, 0, 0]);
  