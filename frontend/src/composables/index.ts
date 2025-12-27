/**
 * Composables module exports
 * 
 * Centralized exports for all composables.
 */

export { useAuth } from './useAuth';
export { useNetworks } from './useNetworks';
export { useNotifications } from './useNotifications';
export { useUserNotifications } from './useUserNotifications';
export { useHealthMonitoring } from './useHealthMonitoring';
export { useVersionCheck } from './useVersionCheck';
export { useNetworkData } from './useNetworkData';
export { useMapLayout } from './useMapLayout';

// Re-export types from composables for backwards compatibility
export type {
  Network,
  NetworkLayoutResponse,
  CreateNetworkData,
  UpdateNetworkData,
  NetworkPermissionRole,
  NetworkPermission,
  CreateNetworkPermission,
} from './useNetworks';

export type { MonitoringConfig, MonitoringStatus } from './useHealthMonitoring';

export type { SavedLayout } from './useMapLayout';

export type { VersionType, VersionPreferences, VersionInfo } from './useVersionCheck';

