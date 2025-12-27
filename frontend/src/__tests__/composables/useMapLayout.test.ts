/**
 * Tests for composables/useMapLayout.ts
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useMapLayout } from '../../composables/useMapLayout';
import type { TreeNode } from '../../types/network';
import type { SavedLayout } from '../../types/layout';

describe('useMapLayout', () => {
  // Get fresh composable for each test to reset internal state
  let applySavedPositions: ReturnType<typeof useMapLayout>['applySavedPositions'];
  let clearPositions: ReturnType<typeof useMapLayout>['clearPositions'];
  let exportLayout: ReturnType<typeof useMapLayout>['exportLayout'];
  let updatePosition: ReturnType<typeof useMapLayout>['updatePosition'];
  let positions: ReturnType<typeof useMapLayout>['positions'];

  beforeEach(() => {
    const layout = useMapLayout();
    applySavedPositions = layout.applySavedPositions;
    clearPositions = layout.clearPositions;
    exportLayout = layout.exportLayout;
    updatePosition = layout.updatePosition;
    positions = layout.positions;
    // Clear any shared state
    clearPositions();
  });

  describe('applySavedPositions', () => {
    it('applies saved fx/fy positions to matching nodes', () => {
      const root: TreeNode = {
        id: 'root',
        name: 'Network',
        children: [
          { id: '192.168.1.1', name: 'Router', role: 'gateway/router' },
          { id: '192.168.1.2', name: 'Server', role: 'server' },
        ],
      };

      const saved: SavedLayout = {
        version: 1,
        timestamp: new Date().toISOString(),
        positions: {
          '192.168.1.1': { x: 100, y: 200 },
          '192.168.1.2': { x: 300, y: 400 },
        },
        root: root,
      };

      applySavedPositions(root, saved);

      expect(root.children![0].fx).toBe(100);
      expect(root.children![0].fy).toBe(200);
      expect(root.children![1].fx).toBe(300);
      expect(root.children![1].fy).toBe(400);
    });

    it('does not modify nodes without saved positions', () => {
      const root: TreeNode = {
        id: 'root',
        name: 'Network',
        children: [{ id: '192.168.1.1', name: 'Router', role: 'gateway/router' }],
      };

      const saved: SavedLayout = {
        version: 1,
        timestamp: new Date().toISOString(),
        positions: {
          '192.168.1.2': { x: 100, y: 200 }, // Different ID
        },
        root: root,
      };

      applySavedPositions(root, saved);

      expect(root.children![0].fx).toBeUndefined();
      expect(root.children![0].fy).toBeUndefined();
    });

    it('handles undefined saved layout', () => {
      const root: TreeNode = {
        id: 'root',
        name: 'Network',
        children: [{ id: '192.168.1.1', name: 'Router', role: 'gateway/router' }],
      };

      // Should not throw
      applySavedPositions(root, undefined);
      expect(root.children![0].fx).toBeUndefined();
    });
  });

  describe('clearPositions', () => {
    it('clears the internal positions map', () => {
      // Add some positions
      updatePosition('node1', 100, 200);
      updatePosition('node2', 300, 400);

      expect(positions.size).toBe(2);

      clearPositions();

      expect(positions.size).toBe(0);
    });
  });

  describe('exportLayout', () => {
    it('exports all node positions from fx/fy', () => {
      const root: TreeNode = {
        id: 'root',
        name: 'Network',
        fx: 0,
        fy: 0,
        children: [
          { id: '192.168.1.1', name: 'Router', fx: 100, fy: 200 },
          { id: '192.168.1.2', name: 'Server', fx: 300, fy: 400 },
        ],
      };

      const layout = exportLayout(root);

      expect(layout.positions['root']).toEqual({ x: 0, y: 0 });
      expect(layout.positions['192.168.1.1']).toEqual({ x: 100, y: 200 });
      expect(layout.positions['192.168.1.2']).toEqual({ x: 300, y: 400 });
    });

    it('skips nodes without positions', () => {
      const root: TreeNode = {
        id: 'root',
        name: 'Network',
        fx: 0,
        fy: 0,
        children: [
          { id: '192.168.1.1', name: 'Router', fx: 100, fy: 200 },
          { id: '192.168.1.2', name: 'Server' }, // No fx/fy
        ],
      };

      const layout = exportLayout(root);

      expect(layout.positions['192.168.1.1']).toBeDefined();
      expect(layout.positions['192.168.1.2']).toBeUndefined();
    });

    it('includes positions from internal map', () => {
      const root: TreeNode = {
        id: 'root',
        name: 'Network',
        children: [
          { id: '192.168.1.1', name: 'Router' },
        ],
      };

      // Add position via updatePosition
      updatePosition('192.168.1.1', 500, 600);

      const layout = exportLayout(root);

      expect(layout.positions['192.168.1.1']).toEqual({ x: 500, y: 600 });
    });

    it('includes version and timestamp', () => {
      const root: TreeNode = { id: 'root', name: 'Network' };
      const layout = exportLayout(root);

      expect(layout.version).toBe(1);
      expect(layout.timestamp).toBeDefined();
    });
  });

  describe('updatePosition', () => {
    it('stores position in internal map', () => {
      updatePosition('node1', 100, 200);

      expect(positions.get('node1')).toEqual({ x: 100, y: 200 });
    });

    it('overwrites existing position', () => {
      updatePosition('node1', 100, 200);
      updatePosition('node1', 300, 400);

      expect(positions.get('node1')).toEqual({ x: 300, y: 400 });
    });
  });
});

