import type { Grid, AffinityLink, AffinityColor } from "./types";

export function findAffinityLinks(grid: Grid): AffinityLink[] {
  const links: AffinityLink[] = [];

  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const cell = grid[row][col];
      if (!cell) continue;

      // Check right neighbor (horizontal link)
      if (col < 2) {
        const right = grid[row][col + 1];
        if (right && cell.affinity_right && right.affinity_left) {
          if (cell.affinity_right === right.affinity_left) {
            links.push({
              from: [row, col],
              to: [row, col + 1],
              color: cell.affinity_right as AffinityColor,
              direction: "horizontal",
            });
          }
        }
      }

      // Check bottom neighbor (vertical link)
      if (row < 2) {
        const below = grid[row + 1][col];
        if (below && cell.affinity_bottom && below.affinity_top) {
          if (cell.affinity_bottom === below.affinity_top) {
            links.push({
              from: [row, col],
              to: [row + 1, col],
              color: cell.affinity_bottom as AffinityColor,
              direction: "vertical",
            });
          }
        }
      }
    }
  }

  return links;
}
