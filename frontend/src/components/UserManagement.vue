<template>
	<Teleport to="body">
		<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
				<!-- Header -->
				<div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
					<h2 class="text-xl font-semibold text-slate-900 dark:text-white">User Management</h2>
					<button
						@click="$emit('close')"
						class="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Content -->
				<div class="flex-1 overflow-auto p-6">
					<!-- Add User Button -->
					<div class="mb-6">
						<button
							@click="showAddUser = true"
							class="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
							</svg>
							Add User
						</button>
					</div>

					<!-- Loading State -->
					<div v-if="isLoading" class="flex items-center justify-center py-12">
						<svg class="animate-spin h-8 w-8 text-cyan-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
					</div>

					<!-- Users List -->
					<div v-else class="space-y-3">
						<div
							v-for="u in users"
							:key="u.id"
							class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700"
						>
							<div class="flex items-center gap-4">
								<!-- Avatar -->
								<div 
									class="w-10 h-10 rounded-full flex items-center justify-center text-white font-medium"
									:class="u.role === 'owner' ? 'bg-gradient-to-br from-amber-500 to-orange-600' : 'bg-gradient-to-br from-cyan-500 to-blue-600'"
								>
									{{ (u.display_name || u.username).charAt(0).toUpperCase() }}
								</div>
								
								<div>
									<div class="flex items-center gap-2">
										<span class="font-medium text-slate-900 dark:text-white">
											{{ u.display_name || u.username }}
										</span>
										<span :class="getRoleBadgeClass(u.role)" class="text-xs px-2 py-0.5 rounded-full">
											{{ getRoleLabel(u.role) }}
										</span>
									</div>
									<div class="text-sm text-slate-500 dark:text-slate-400">
										@{{ u.username }}
										<span v-if="u.last_login" class="ml-2">
											• Last login: {{ formatDate(u.last_login) }}
										</span>
									</div>
								</div>
							</div>

							<!-- Actions -->
							<div v-if="u.role !== 'owner'" class="flex items-center gap-2">
								<button
									@click="editUser(u)"
									class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700"
									title="Edit user"
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
								</button>
								<button
									@click="confirmDelete(u)"
									class="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30"
									title="Delete user"
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							</div>
							<div v-else class="text-xs text-slate-400 italic">
								Cannot modify owner
							</div>
						</div>

						<div v-if="users.length === 0" class="text-center py-12 text-slate-500">
							No users found
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Add/Edit User Modal -->
		<div v-if="showAddUser || editingUser" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">
					{{ editingUser ? 'Edit User' : 'Add New User' }}
				</h3>
				
				<form @submit.prevent="onSubmitUser" class="space-y-4">
					<div v-if="!editingUser">
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Username
						</label>
						<input
							v-model="userForm.username"
							type="text"
							required
							pattern="^[a-zA-Z][a-zA-Z0-9_-]*$"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							placeholder="username"
						/>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Display Name
						</label>
						<input
							v-model="userForm.displayName"
							type="text"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							placeholder="John Doe"
						/>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Role
						</label>
						<select
							v-model="userForm.role"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
						>
							<option value="readonly">Read Only - Can only view the network map</option>
							<option value="readwrite">Read/Write - Can view and modify the network map</option>
						</select>
					</div>
					
					<div v-if="!editingUser">
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							Password
						</label>
						<input
							v-model="userForm.password"
							type="password"
							:required="!editingUser"
							minlength="8"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							placeholder="••••••••"
						/>
						<p class="mt-1 text-xs text-slate-500">Minimum 8 characters</p>
					</div>

					<div v-if="editingUser">
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
							New Password <span class="text-slate-400">(leave blank to keep current)</span>
						</label>
						<input
							v-model="userForm.password"
							type="password"
							minlength="8"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							placeholder="••••••••"
						/>
					</div>

					<div v-if="formError" class="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-500/50 rounded-lg">
						<p class="text-sm text-red-600 dark:text-red-400">{{ formError }}</p>
					</div>

					<div class="flex gap-3 pt-2">
						<button
							type="button"
							@click="closeUserForm"
							class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
						>
							Cancel
						</button>
						<button
							type="submit"
							:disabled="isSubmitting"
							class="flex-1 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50"
						>
							{{ isSubmitting ? 'Saving...' : (editingUser ? 'Update User' : 'Create User') }}
						</button>
					</div>
				</form>
			</div>
		</div>

		<!-- Delete Confirmation Modal -->
		<div v-if="deletingUser" class="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
				<h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">Delete User</h3>
				<p class="text-slate-600 dark:text-slate-400 mb-6">
					Are you sure you want to delete <strong>{{ deletingUser.display_name || deletingUser.username }}</strong>? 
					This action cannot be undone.
				</p>
				
				<div class="flex gap-3">
					<button
						@click="deletingUser = null"
						class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
					>
						Cancel
					</button>
					<button
						@click="onDeleteUser"
						:disabled="isSubmitting"
						class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
					>
						{{ isSubmitting ? 'Deleting...' : 'Delete User' }}
					</button>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script lang="ts" setup>
import { ref, onMounted } from "vue";
import { useAuth } from "../composables/useAuth";
import type { User, UserRole } from "../types/auth";
import { getRoleLabel } from "../types/auth";

defineEmits<{
	(e: "close"): void;
}>();

const { listUsers, createUser, updateUser, deleteUser } = useAuth();

const users = ref<User[]>([]);
const isLoading = ref(true);
const isSubmitting = ref(false);
const formError = ref<string | null>(null);

const showAddUser = ref(false);
const editingUser = ref<User | null>(null);
const deletingUser = ref<User | null>(null);

const userForm = ref({
	username: "",
	displayName: "",
	role: "readonly" as UserRole,
	password: "",
});

async function loadUsers() {
	isLoading.value = true;
	try {
		users.value = await listUsers();
	} catch (e) {
		console.error("Failed to load users:", e);
	} finally {
		isLoading.value = false;
	}
}

onMounted(() => {
	loadUsers();
});

function getRoleBadgeClass(role: UserRole): string {
	switch (role) {
		case "owner":
			return "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400";
		case "readwrite":
			return "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400";
		case "readonly":
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
		default:
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
	}
}

function formatDate(dateStr: string): string {
	const date = new Date(dateStr);
	return date.toLocaleDateString(undefined, { 
		month: "short", 
		day: "numeric",
		hour: "2-digit",
		minute: "2-digit"
	});
}

function editUser(user: User) {
	editingUser.value = user;
	userForm.value = {
		username: user.username,
		displayName: user.display_name || "",
		role: user.role,
		password: "",
	};
	formError.value = null;
}

function confirmDelete(user: User) {
	deletingUser.value = user;
}

function closeUserForm() {
	showAddUser.value = false;
	editingUser.value = null;
	userForm.value = {
		username: "",
		displayName: "",
		role: "readonly",
		password: "",
	};
	formError.value = null;
}

async function onSubmitUser() {
	formError.value = null;
	isSubmitting.value = true;

	try {
		if (editingUser.value) {
			// Update existing user
			await updateUser(editingUser.value.id, {
				display_name: userForm.value.displayName || undefined,
				role: userForm.value.role,
				password: userForm.value.password || undefined,
			});
		} else {
			// Create new user
			await createUser({
				username: userForm.value.username,
				password: userForm.value.password,
				display_name: userForm.value.displayName || undefined,
				role: userForm.value.role,
			});
		}
		
		closeUserForm();
		await loadUsers();
	} catch (e: any) {
		formError.value = e.message || "Failed to save user";
	} finally {
		isSubmitting.value = false;
	}
}

async function onDeleteUser() {
	if (!deletingUser.value) return;
	
	isSubmitting.value = true;
	try {
		await deleteUser(deletingUser.value.id);
		deletingUser.value = null;
		await loadUsers();
	} catch (e: any) {
		alert(e.message || "Failed to delete user");
	} finally {
		isSubmitting.value = false;
	}
}
</script>
