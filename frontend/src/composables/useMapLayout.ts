/**
 * Map layout composable
 * 
 * Manages network map node positions and layout persistence.
 */

import type { TreeNode } from '../types/network';
import type { SavedLayout } from '../types/layout';

// Re-export type for backwards compatibility
export type { SavedLayout } from '../types/layout';

// Shared state across components
const positions: Map<string, { x: number; y: number }> = new Map();

export function useMapLayout() {
  function applySavedPositions(root: TreeNode, saved?: SavedLayout) {
    if (!saved) return;
    const walk = (n: TreeNode) => {
      const pos = saved.positions[n.id];
      if (pos) {
        n.fx = pos.x;
        n.fy = pos.y;
        positions.set(n.id, { x: pos.x, y: pos.y });
      }
      for (const c of n.children || []) walk(c);
    };
    walk(root);
  }

  function updatePosition(id: string, x: number, y: number) {
    positions.set(id, { x, y });
  }

  function exportLayout(root: TreeNode): SavedLayout {
    // Ensure we include all nodes, even those not dragged yet (use current fx/fy if set)
    const map: Record<string, { x: number; y: number }> = {};
    const walk = (n: TreeNode) => {
      const p =
        positions.get(n.id) ||
        (typeof n.fx === 'number' && typeof n.fy === 'number' ? { x: n.fx, y: n.fy } : undefined);
      if (p) map[n.id] = { x: p.x, y: p.y };
      for (const c of n.children || []) walk(c);
    };
    walk(root);
    return {
      version: 1,
      timestamp: new Date().toISOString(),
      positions: map,
      root: root,
    };
  }

  function importLayout(jsonText: string): SavedLayout {
    const parsed = JSON.parse(jsonText) as SavedLayout;
    return parsed;
  }

  function clearPositions() {
    positions.clear();
  }

  return {
    positions,
    applySavedPositions,
    updatePosition,
    exportLayout,
    importLayout,
    clearPositions,
  };
}
