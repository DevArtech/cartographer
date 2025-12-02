import { ref, computed, readonly } from "vue";
import axios from "axios";
import type {
	User,
	UserRole,
	SetupStatus,
	LoginRequest,
	LoginResponse,
	OwnerSetupRequest,
	UserCreateRequest,
	UserUpdateRequest,
	SessionInfo,
	ChangePasswordRequest,
	AuthState,
} from "../types/auth";

const AUTH_STORAGE_KEY = "cartographer_auth";

// Reactive state
const user = ref<User | null>(null);
const token = ref<string | null>(null);
const permissions = ref<string[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const setupStatus = ref<SetupStatus | null>(null);

// Computed properties
const isAuthenticated = computed(() => !!token.value && !!user.value);
const isOwner = computed(() => user.value?.role === "owner");
const canWrite = computed(() => user.value?.role === "owner" || user.value?.role === "readwrite");
const isReadOnly = computed(() => user.value?.role === "readonly");

// Initialize from localStorage
function initFromStorage(): void {
	try {
		const stored = localStorage.getItem(AUTH_STORAGE_KEY);
		if (stored) {
			const state: AuthState = JSON.parse(stored);
			
			// Check if token is expired
			if (state.expiresAt > Date.now()) {
				token.value = state.token;
				user.value = state.user;
				
				// Set axios default header
				axios.defaults.headers.common["Authorization"] = `Bearer ${state.token}`;
				
				console.log("[Auth] Restored session for:", state.user.username);
			} else {
				console.log("[Auth] Stored session expired, clearing");
				clearAuth();
			}
		}
	} catch (e) {
		console.error("[Auth] Failed to restore session:", e);
		clearAuth();
	}
}

// Save to localStorage
function saveToStorage(authToken: string, authUser: User, expiresIn: number): void {
	const state: AuthState = {
		token: authToken,
		user: authUser,
		expiresAt: Date.now() + expiresIn * 1000,
	};
	localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(state));
}

// Clear auth state
function clearAuth(): void {
	token.value = null;
	user.value = null;
	permissions.value = [];
	localStorage.removeItem(AUTH_STORAGE_KEY);
	delete axios.defaults.headers.common["Authorization"];
}

// Check setup status
async function checkSetupStatus(): Promise<SetupStatus> {
	try {
		const response = await axios.get<SetupStatus>("/api/auth/setup/status");
		setupStatus.value = response.data;
		return response.data;
	} catch (e: any) {
		console.error("[Auth] Failed to check setup status:", e);
		throw new Error(e.response?.data?.detail || "Failed to check setup status");
	}
}

// Setup owner account (first run)
async function setupOwner(request: OwnerSetupRequest): Promise<User> {
	isLoading.value = true;
	error.value = null;
	
	try {
		const response = await axios.post<User>("/api/auth/setup/owner", request);
		console.log("[Auth] Owner account created:", response.data.username);
		return response.data;
	} catch (e: any) {
		const message = e.response?.data?.detail || "Failed to create owner account";
		error.value = message;
		throw new Error(message);
	} finally {
		isLoading.value = false;
	}
}

// Login
async function login(request: LoginRequest): Promise<User> {
	isLoading.value = true;
	error.value = null;
	
	try {
		const response = await axios.post<LoginResponse>("/api/auth/login", request);
		const { access_token, expires_in, user: authUser } = response.data;
		
		// Update state
		token.value = access_token;
		user.value = authUser;
		
		// Set axios default header
		axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
		
		// Save to storage
		saveToStorage(access_token, authUser, expires_in);
		
		console.log("[Auth] Login successful:", authUser.username);
		return authUser;
	} catch (e: any) {
		const message = e.response?.data?.detail || "Login failed";
		error.value = message;
		throw new Error(message);
	} finally {
		isLoading.value = false;
	}
}

// Logout
async function logout(): Promise<void> {
	try {
		await axios.post("/api/auth/logout");
	} catch (e) {
		// Ignore logout errors - we'll clear local state anyway
		console.warn("[Auth] Logout request failed:", e);
	} finally {
		clearAuth();
		console.log("[Auth] Logged out");
	}
}

// Verify current session
async function verifySession(): Promise<boolean> {
	if (!token.value) {
		return false;
	}
	
	try {
		const response = await axios.post<{ valid: boolean }>("/api/auth/verify");
		if (!response.data.valid) {
			clearAuth();
			return false;
		}
		return true;
	} catch (e) {
		console.warn("[Auth] Session verification failed:", e);
		clearAuth();
		return false;
	}
}

// Refresh session info
async function refreshSession(): Promise<SessionInfo | null> {
	if (!token.value) {
		return null;
	}
	
	try {
		const response = await axios.get<SessionInfo>("/api/auth/session");
		user.value = response.data.user;
		permissions.value = response.data.permissions;
		return response.data;
	} catch (e: any) {
		if (e.response?.status === 401) {
			clearAuth();
		}
		return null;
	}
}

// ==================== User Management ====================

// List users (owner only)
async function listUsers(): Promise<User[]> {
	try {
		const response = await axios.get<User[]>("/api/auth/users");
		return response.data;
	} catch (e: any) {
		throw new Error(e.response?.data?.detail || "Failed to list users");
	}
}

// Create user (owner only)
async function createUser(request: UserCreateRequest): Promise<User> {
	try {
		const response = await axios.post<User>("/api/auth/users", request);
		console.log("[Auth] User created:", response.data.username);
		return response.data;
	} catch (e: any) {
		throw new Error(e.response?.data?.detail || "Failed to create user");
	}
}

// Update user
async function updateUser(userId: string, request: UserUpdateRequest): Promise<User> {
	try {
		const response = await axios.patch<User>(`/api/auth/users/${userId}`, request);
		
		// Update local user if it's the current user
		if (user.value && user.value.id === userId) {
			user.value = response.data;
		}
		
		return response.data;
	} catch (e: any) {
		throw new Error(e.response?.data?.detail || "Failed to update user");
	}
}

// Delete user (owner only)
async function deleteUser(userId: string): Promise<void> {
	try {
		await axios.delete(`/api/auth/users/${userId}`);
		console.log("[Auth] User deleted:", userId);
	} catch (e: any) {
		throw new Error(e.response?.data?.detail || "Failed to delete user");
	}
}

// Change password
async function changePassword(request: ChangePasswordRequest): Promise<void> {
	try {
		await axios.post("/api/auth/me/change-password", request);
		console.log("[Auth] Password changed");
	} catch (e: any) {
		throw new Error(e.response?.data?.detail || "Failed to change password");
	}
}

// Main composable export
export function useAuth() {
	// Initialize from storage on first use
	if (!token.value) {
		initFromStorage();
	}
	
	return {
		// State (readonly)
		user: readonly(user),
		token: readonly(token),
		permissions: readonly(permissions),
		isLoading: readonly(isLoading),
		error: readonly(error),
		setupStatus: readonly(setupStatus),
		
		// Computed
		isAuthenticated,
		isOwner,
		canWrite,
		isReadOnly,
		
		// Actions
		checkSetupStatus,
		setupOwner,
		login,
		logout,
		verifySession,
		refreshSession,
		
		// User management
		listUsers,
		createUser,
		updateUser,
		deleteUser,
		changePassword,
	};
}
