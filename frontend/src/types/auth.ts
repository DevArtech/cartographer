// User permission levels
export type UserRole = "owner" | "readwrite" | "readonly";

// User data returned from API (no password)
export interface User {
	id: string;
	username: string;
	first_name: string;
	last_name: string;
	email: string;
	role: UserRole;
	created_at: string;
	updated_at: string;
	last_login?: string;
	is_active: boolean;
}

// Request to create the initial owner account
export interface OwnerSetupRequest {
	username: string;
	first_name: string;
	last_name: string;
	email: string;
	password: string;
}

// Request to create a new user
export interface UserCreateRequest {
	username: string;
	first_name: string;
	last_name: string;
	email: string;
	password: string;
	role: UserRole;
}

// Request to update a user
export interface UserUpdateRequest {
	first_name?: string;
	last_name?: string;
	email?: string;
	role?: UserRole;
	password?: string;
}

// Helper to get full name
export function getFullName(user: User): string {
	return `${user.first_name} ${user.last_name}`;
}

// Login credentials
export interface LoginRequest {
	username: string;
	password: string;
}

// Successful login response
export interface LoginResponse {
	access_token: string;
	token_type: string;
	expires_in: number;
	user: User;
}

// Setup status response
export interface SetupStatus {
	is_setup_complete: boolean;
	owner_exists: boolean;
	total_users: number;
}

// Current session information
export interface SessionInfo {
	user: User;
	permissions: string[];
}

// Change password request
export interface ChangePasswordRequest {
	current_password: string;
	new_password: string;
}

// Auth state stored in localStorage
export interface AuthState {
	token: string;
	user: User;
	expiresAt: number; // timestamp
}

// Permission helpers
export function canWrite(role: UserRole): boolean {
	return role === "owner" || role === "readwrite";
}

export function canManageUsers(role: UserRole): boolean {
	return role === "owner";
}

export function getRoleLabel(role: UserRole): string {
	switch (role) {
		case "owner":
			return "Owner";
		case "readwrite":
			return "Read/Write";
		case "readonly":
			return "Read Only";
		default:
			return role;
	}
}

export function getRoleDescription(role: UserRole): string {
	switch (role) {
		case "owner":
			return "Full access - can manage users and modify the network map";
		case "readwrite":
			return "Can view and modify the network map";
		case "readonly":
			return "Can only view the network map";
		default:
			return "";
	}
}

// ==================== Invitation Types ====================

export type InviteStatus = "pending" | "accepted" | "expired" | "revoked";

// Invitation data from API
export interface Invite {
	id: string;
	email: string;
	role: UserRole;
	status: InviteStatus;
	invited_by: string;
	invited_by_name: string;
	created_at: string;
	expires_at: string;
	accepted_at?: string;
}

// Request to create an invitation
export interface InviteCreateRequest {
	email: string;
	role: UserRole;
}

// Public info about an invite token
export interface InviteTokenInfo {
	email: string;
	role: UserRole;
	invited_by_name: string;
	expires_at: string;
	is_valid: boolean;
}

// Request to accept an invitation
export interface AcceptInviteRequest {
	token: string;
	username: string;
	first_name: string;
	last_name: string;
	password: string;
}

// Helper to get invite status label
export function getInviteStatusLabel(status: InviteStatus): string {
	switch (status) {
		case "pending":
			return "Pending";
		case "accepted":
			return "Accepted";
		case "expired":
			return "Expired";
		case "revoked":
			return "Revoked";
		default:
			return status;
	}
}

// Helper to get invite status color class
export function getInviteStatusClass(status: InviteStatus): string {
	switch (status) {
		case "pending":
			return "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400";
		case "accepted":
			return "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400";
		case "expired":
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
		case "revoked":
			return "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400";
		default:
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
	}
}
