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
