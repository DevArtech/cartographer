/**
 * Networks API module
 * 
 * All network management API calls.
 */

import client from './client';
import type { SavedLayout } from '../types/layout';

// ==================== Types ====================

export interface Network {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_sync_at: string | null;
  owner_id: string | null;
  is_owner: boolean;
  permission: 'viewer' | 'editor' | 'admin' | null;
}

export interface NetworkLayoutResponse {
  id: string;
  name: string;
  layout_data: SavedLayout | null;
  updated_at: string;
}

export interface CreateNetworkData {
  name: string;
  description?: string;
}

export interface UpdateNetworkData {
  name?: string;
  description?: string;
}

export type NetworkPermissionRole = 'viewer' | 'editor';

export interface NetworkPermission {
  id: number;
  network_id: string;
  user_id: string;
  role: NetworkPermissionRole;
  created_at: string;
  username?: string;
}

export interface CreateNetworkPermission {
  user_id: string;
  role: NetworkPermissionRole;
}

// ==================== Network CRUD ====================

export async function fetchNetworks(): Promise<Network[]> {
  const response = await client.get<Network[]>('/api/networks', {
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      Pragma: 'no-cache',
    },
    params: {
      _t: Date.now(),
    },
  });
  return response.data;
}

export async function getNetwork(id: string): Promise<Network> {
  const response = await client.get<Network>(`/api/networks/${id}`);
  return response.data;
}

export async function createNetwork(data: CreateNetworkData): Promise<Network> {
  const response = await client.post<Network>('/api/networks', data);
  return response.data;
}

export async function updateNetwork(id: string, data: UpdateNetworkData): Promise<Network> {
  const response = await client.patch<Network>(`/api/networks/${id}`, data);
  return response.data;
}

export async function deleteNetwork(id: string): Promise<void> {
  await client.delete(`/api/networks/${id}`);
}

// ==================== Layout ====================

export async function getNetworkLayout(id: string): Promise<NetworkLayoutResponse> {
  const response = await client.get<NetworkLayoutResponse>(`/api/networks/${id}/layout`);
  return response.data;
}

export async function saveNetworkLayout(id: string, layoutData: SavedLayout): Promise<NetworkLayoutResponse> {
  const response = await client.post<NetworkLayoutResponse>(`/api/networks/${id}/layout`, {
    layout_data: layoutData,
  });
  return response.data;
}

// ==================== Permissions ====================

export async function listNetworkPermissions(networkId: string): Promise<NetworkPermission[]> {
  const response = await client.get<NetworkPermission[]>(`/api/networks/${networkId}/permissions`);
  return response.data;
}

export async function addNetworkPermission(
  networkId: string,
  data: CreateNetworkPermission
): Promise<NetworkPermission> {
  const response = await client.post<NetworkPermission>(`/api/networks/${networkId}/permissions`, data);
  return response.data;
}

export async function removeNetworkPermission(networkId: string, userId: string): Promise<void> {
  await client.delete(`/api/networks/${networkId}/permissions/${userId}`);
}

