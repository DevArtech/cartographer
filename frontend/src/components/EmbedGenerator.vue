<template>
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @click.self="$emit('close')">
		<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
			<!-- Header -->
			<div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-indigo-500 to-purple-600">
				<div class="flex items-center gap-3">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
					</svg>
					<h2 class="text-lg font-semibold text-white">Generate Embed</h2>
				</div>
				<button 
					@click="$emit('close')" 
					class="p-1 rounded hover:bg-white/20 text-white/80 hover:text-white transition-colors"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>

			<!-- Content -->
			<div class="p-6">
				<p class="text-sm text-slate-600 dark:text-slate-400 mb-6">
					Create a read-only embed of your network topology map. The embed supports panning and zooming but does not allow editing.
				</p>

				<!-- Loading state -->
				<div v-if="loading" class="flex items-center justify-center py-8">
					<svg class="animate-spin h-8 w-8 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
					</svg>
				</div>

				<template v-else>
					<!-- Sensitive Mode Toggle -->
					<div class="mb-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-3">
								<div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
									<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
									</svg>
								</div>
								<div>
									<div class="font-medium text-slate-800 dark:text-slate-200">Sensitive Mode</div>
									<div class="text-xs text-slate-500 dark:text-slate-400">Hide IP addresses and sensitive details</div>
								</div>
							</div>
							<button 
								@click="toggleSensitiveMode"
								:disabled="saving"
								class="relative w-12 h-7 rounded-full transition-colors duration-200 disabled:opacity-50"
								:class="sensitiveMode ? 'bg-amber-500' : 'bg-slate-300 dark:bg-slate-600'"
							>
								<span 
									class="absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform duration-200"
									:class="sensitiveMode ? 'translate-x-5' : 'translate-x-0'"
								></span>
							</button>
						</div>
					</div>

					<!-- Show Owner Toggle -->
					<div class="mb-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-3">
								<div class="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
									<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600 dark:text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
									</svg>
								</div>
								<div>
									<div class="font-medium text-slate-800 dark:text-slate-200">Show Owner</div>
									<div class="text-xs text-slate-500 dark:text-slate-400">Display your name on the embed</div>
								</div>
							</div>
							<button 
								@click="toggleShowOwner"
								:disabled="saving"
								class="relative w-12 h-7 rounded-full transition-colors duration-200 disabled:opacity-50"
								:class="showOwner ? 'bg-indigo-500' : 'bg-slate-300 dark:bg-slate-600'"
							>
								<span 
									class="absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform duration-200"
									:class="showOwner ? 'translate-x-5' : 'translate-x-0'"
								></span>
							</button>
						</div>

						<!-- Owner Name Display Options (when enabled) -->
						<div v-if="showOwner" class="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
							<label class="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">Display as:</label>
							<div class="space-y-2">
								<label class="flex items-center gap-2 cursor-pointer">
									<input 
										type="radio" 
										v-model="ownerDisplayType" 
										value="fullName"
										@change="updateOwnerDisplay"
										class="text-indigo-600 focus:ring-indigo-500"
									/>
									<span class="text-sm text-slate-700 dark:text-slate-300">Full Name</span>
									<span class="text-xs text-slate-500 dark:text-slate-400">({{ currentUser?.first_name }} {{ currentUser?.last_name }})</span>
								</label>
								<label class="flex items-center gap-2 cursor-pointer">
									<input 
										type="radio" 
										v-model="ownerDisplayType" 
										value="username"
										@change="updateOwnerDisplay"
										class="text-indigo-600 focus:ring-indigo-500"
									/>
									<span class="text-sm text-slate-700 dark:text-slate-300">Username</span>
									<span class="text-xs text-slate-500 dark:text-slate-400">({{ currentUser?.username }})</span>
								</label>
							</div>
						</div>
					</div>

					<!-- Saving indicator -->
					<div v-if="saving" class="mb-4 text-xs text-slate-500 dark:text-slate-400 flex items-center justify-center gap-1">
						<svg class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						Saving settings...
					</div>

					<!-- Generated URL -->
					<div class="mb-4">
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Embed URL</label>
						<div class="flex gap-2">
							<input 
								type="text" 
								:value="embedUrl" 
								readonly
								class="flex-1 px-3 py-2 text-sm bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-800 dark:text-slate-200 font-mono"
							/>
							<button 
								@click="copyUrl"
								class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-500 transition-colors flex items-center gap-2"
							>
								<svg v-if="!copied" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
								</svg>
								<svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
								</svg>
								{{ copied ? 'Copied!' : 'Copy' }}
							</button>
						</div>
					</div>

					<!-- iframe Code -->
					<div class="mb-6">
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Embed Code (iframe)</label>
						<div class="relative">
							<textarea 
								:value="iframeCode" 
								readonly
								rows="3"
								class="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-emerald-400 font-mono resize-none"
							></textarea>
							<button 
								@click="copyIframe"
								class="absolute top-2 right-2 px-2 py-1 bg-slate-700 text-slate-300 text-xs rounded hover:bg-slate-600 transition-colors"
							>
								{{ copiedIframe ? '✓' : 'Copy' }}
							</button>
						</div>
					</div>

					<!-- Open in new tab button -->
					<div class="flex justify-end gap-3">
						<button 
							@click="$emit('close')" 
							class="px-4 py-2 text-sm text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
						>
							Close
						</button>
						<a 
							:href="embedUrl"
							target="_blank"
							rel="noopener noreferrer"
							class="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-500 transition-colors flex items-center gap-2"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
							</svg>
							Open Preview
						</a>
					</div>
				</template>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useAuth } from '../composables/useAuth';
import type { User } from '../types/auth';

const emit = defineEmits<{
	(e: 'close'): void;
}>();

const { user } = useAuth();
const currentUser = computed(() => user.value);

const loading = ref(true);
const saving = ref(false);
const sensitiveMode = ref(false);
const showOwner = ref(false);
const ownerDisplayType = ref<'fullName' | 'username'>('fullName');
const copied = ref(false);
const copiedIframe = ref(false);

const embedUrl = computed(() => {
	const baseUrl = window.location.origin;
	return `${baseUrl}/embed`;
});

const iframeCode = computed(() => {
	return `<iframe src="${embedUrl.value}" width="100%" height="600" frameborder="0" style="border-radius: 8px;"></iframe>`;
});

function getOwnerDisplayName(): string {
	if (!currentUser.value) return '';
	if (ownerDisplayType.value === 'username') {
		return currentUser.value.username;
	}
	return `${currentUser.value.first_name} ${currentUser.value.last_name}`.trim();
}

async function loadConfig() {
	loading.value = true;
	try {
		const response = await axios.get('/api/embed-config');
		sensitiveMode.value = response.data.sensitiveMode || false;
		showOwner.value = response.data.showOwner || false;
		ownerDisplayType.value = response.data.ownerDisplayType || 'fullName';
	} catch (err) {
		console.error('Failed to load embed config:', err);
	} finally {
		loading.value = false;
	}
}

async function saveConfig() {
	saving.value = true;
	try {
		await axios.post('/api/embed-config', {
			sensitiveMode: sensitiveMode.value,
			showOwner: showOwner.value,
			ownerDisplayType: ownerDisplayType.value,
			ownerDisplayName: showOwner.value ? getOwnerDisplayName() : null
		});
	} catch (err) {
		console.error('Failed to save embed config:', err);
	} finally {
		saving.value = false;
	}
}

async function toggleSensitiveMode() {
	sensitiveMode.value = !sensitiveMode.value;
	await saveConfig();
}

async function toggleShowOwner() {
	showOwner.value = !showOwner.value;
	await saveConfig();
}

async function updateOwnerDisplay() {
	await saveConfig();
}

function copyUrl() {
	navigator.clipboard.writeText(embedUrl.value);
	copied.value = true;
	setTimeout(() => { copied.value = false; }, 2000);
}

function copyIframe() {
	navigator.clipboard.writeText(iframeCode.value);
	copiedIframe.value = true;
	setTimeout(() => { copiedIframe.value = false; }, 2000);
}

onMounted(() => {
	loadConfig();
});
</script>
