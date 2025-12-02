<template>
	<div class="relative" ref="menuContainer">
		<!-- User Button -->
		<button
			@click="isOpen = !isOpen"
			class="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
		>
			<!-- Avatar -->
			<div class="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-medium">
				{{ userInitial }}
			</div>
			<span class="text-sm text-slate-700 dark:text-slate-200 max-w-24 truncate">
				{{ displayName }}
			</span>
			<!-- Role Badge -->
			<span :class="roleBadgeClass" class="text-xs px-1.5 py-0.5 rounded">
				{{ roleLabel }}
			</span>
			<!-- Dropdown Arrow -->
			<svg 
				xmlns="http://www.w3.org/2000/svg" 
				class="h-4 w-4 text-slate-400 transition-transform" 
				:class="{ 'rotate-180': isOpen }"
				fill="none" 
				viewBox="0 0 24 24" 
				stroke="currentColor"
			>
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
			</svg>
		</button>

		<!-- Dropdown Menu -->
		<Transition
			enter-active-class="transition ease-out duration-100"
			enter-from-class="transform opacity-0 scale-95"
			enter-to-class="transform opacity-100 scale-100"
			leave-active-class="transition ease-in duration-75"
			leave-from-class="transform opacity-100 scale-100"
			leave-to-class="transform opacity-0 scale-95"
		>
			<div 
				v-if="isOpen"
				class="absolute right-0 mt-2 w-56 rounded-lg shadow-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 py-1 z-50"
			>
				<!-- User Info -->
				<div class="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
					<p class="text-sm font-medium text-slate-900 dark:text-white truncate">
						{{ displayName }}
					</p>
					<p class="text-xs text-slate-500 dark:text-slate-400">
						@{{ user?.username }}
					</p>
				</div>

				<!-- Menu Items -->
				<div class="py-1">
					<!-- Manage Users (Owner only) -->
					<button
						v-if="isOwner"
						@click="onManageUsers"
						class="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
						</svg>
						Manage Users
					</button>

					<!-- Change Password -->
					<button
						@click="onChangePassword"
						class="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
						</svg>
						Change Password
					</button>
				</div>

				<!-- Logout -->
				<div class="border-t border-slate-200 dark:border-slate-700 py-1">
					<button
						@click="onLogout"
						class="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
						</svg>
						Sign Out
					</button>
				</div>
			</div>
		</Transition>

		<!-- Change Password Modal -->
		<Teleport to="body">
			<div v-if="showPasswordModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
				<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md p-6">
					<h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-4">Change Password</h3>
					
					<form @submit.prevent="onSubmitPassword" class="space-y-4">
						<div>
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
								Current Password
							</label>
							<input
								v-model="passwordForm.current"
								type="password"
								required
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							/>
						</div>
						
						<div>
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
								New Password
							</label>
							<input
								v-model="passwordForm.new"
								type="password"
								required
								minlength="8"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							/>
						</div>
						
						<div>
							<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
								Confirm New Password
							</label>
							<input
								v-model="passwordForm.confirm"
								type="password"
								required
								minlength="8"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
							/>
						</div>

						<div v-if="passwordError" class="p-3 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-500/50 rounded-lg">
							<p class="text-sm text-red-600 dark:text-red-400">{{ passwordError }}</p>
						</div>

						<div class="flex gap-3 pt-2">
							<button
								type="button"
								@click="showPasswordModal = false"
								class="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
							>
								Cancel
							</button>
							<button
								type="submit"
								:disabled="isSubmitting"
								class="flex-1 px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50"
							>
								{{ isSubmitting ? 'Saving...' : 'Update Password' }}
							</button>
						</div>
					</form>
				</div>
			</div>
		</Teleport>
	</div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useAuth } from "../composables/useAuth";
import { getRoleLabel } from "../types/auth";

const emit = defineEmits<{
	(e: "logout"): void;
	(e: "manageUsers"): void;
}>();

const { user, isOwner, logout, changePassword } = useAuth();

const menuContainer = ref<HTMLElement | null>(null);
const isOpen = ref(false);
const showPasswordModal = ref(false);
const isSubmitting = ref(false);
const passwordError = ref<string | null>(null);

const passwordForm = ref({
	current: "",
	new: "",
	confirm: "",
});

const displayName = computed(() => {
	return user.value?.display_name || user.value?.username || "User";
});

const userInitial = computed(() => {
	return displayName.value.charAt(0).toUpperCase();
});

const roleLabel = computed(() => {
	return user.value ? getRoleLabel(user.value.role) : "";
});

const roleBadgeClass = computed(() => {
	switch (user.value?.role) {
		case "owner":
			return "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400";
		case "readwrite":
			return "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400";
		case "readonly":
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
		default:
			return "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400";
	}
});

function closeOnClickOutside(e: MouseEvent) {
	if (menuContainer.value && !menuContainer.value.contains(e.target as Node)) {
		isOpen.value = false;
	}
}

onMounted(() => {
	document.addEventListener("click", closeOnClickOutside);
});

onUnmounted(() => {
	document.removeEventListener("click", closeOnClickOutside);
});

function onManageUsers() {
	isOpen.value = false;
	emit("manageUsers");
}

function onChangePassword() {
	isOpen.value = false;
	passwordForm.value = { current: "", new: "", confirm: "" };
	passwordError.value = null;
	showPasswordModal.value = true;
}

async function onSubmitPassword() {
	passwordError.value = null;

	if (passwordForm.value.new !== passwordForm.value.confirm) {
		passwordError.value = "New passwords do not match";
		return;
	}

	if (passwordForm.value.new.length < 8) {
		passwordError.value = "Password must be at least 8 characters";
		return;
	}

	isSubmitting.value = true;

	try {
		await changePassword({
			current_password: passwordForm.value.current,
			new_password: passwordForm.value.new,
		});
		showPasswordModal.value = false;
	} catch (e: any) {
		passwordError.value = e.message || "Failed to change password";
	} finally {
		isSubmitting.value = false;
	}
}

async function onLogout() {
	isOpen.value = false;
	await logout();
	emit("logout");
}
</script>
