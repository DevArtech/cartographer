export type DeviceRole =
	| "gateway/router"
	| "switch/ap"
	| "firewall"
	| "server"
	| "service"
	| "nas"
	| "client"
	| "unknown";

export interface DeviceEntry {
	ip: string;
	hostname: string;
	role: DeviceRole;
	depth: number;
}

export interface GatewayInfo {
	ip: string;
	hostname: string;
	lanInterface?: string;
	subnet?: string;
}

export interface TreeNode {
	id: string; // typically ip or synthetic group id
	name: string;
	role?: DeviceRole | "group";
	ip?: string;
	hostname?: string;
	children?: TreeNode[];
	// Freeform layout positions (persisted)
	fx?: number;
	fy?: number;
}

export interface ParsedNetworkMap {
	raw: string;
	gateway?: GatewayInfo;
	devices: DeviceEntry[];
	root: TreeNode;
}


