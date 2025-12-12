<template>
	<Teleport to="body">
		<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="$emit('close')">
			<div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-2xl flex flex-col">
				<!-- Header -->
				<div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 rounded-t-xl">
					<div class="flex items-center gap-3">
						<div class="w-9 h-9 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-violet-600 dark:text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
							</svg>
						</div>
						<div>
							<h2 class="text-lg font-semibold text-slate-900 dark:text-white">Send Network Notification</h2>
							<p class="text-xs text-slate-500 dark:text-slate-400">Send a notification to all users in this network</p>
						</div>
					</div>
					<button
						@click="$emit('close')"
						class="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
					>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Content -->
				<div class="flex-1 overflow-auto p-6 space-y-6">
					<!-- Type -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
							Notification Type
						</label>
						<select
							v-model="form.type"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
						>
							<option value="scheduled_maintenance">Maintenance</option>
							<option value="system_status">System Status</option>
							<option value="security_alert">Security Alert</option>
							<option value="isp_issue">ISP Issue</option>
							<option value="device_offline">Device Offline</option>
							<option value="device_online">Device Online</option>
							<option value="device_degraded">Device Degraded</option>
							<option value="anomaly_detected">Anomaly Detected</option>
							<option value="high_latency">High Latency</option>
							<option value="packet_loss">Packet Loss</option>
						</select>
					</div>

					<!-- Priority -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
							Priority
						</label>
						<select
							v-model="form.priority"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
						>
							<option value="low">Low</option>
							<option value="medium">Medium</option>
							<option value="high">High</option>
							<option value="critical">Critical</option>
						</select>
					</div>

					<!-- Title -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
							Title
						</label>
						<input
							v-model="form.title"
							type="text"
							placeholder="Notification title"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
						/>
					</div>

					<!-- Message -->
					<div>
						<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
							Message
						</label>
						<textarea
							v-model="form.message"
							rows="4"
							placeholder="Notification message"
							class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
						></textarea>
					</div>

					<!-- Schedule -->
					<div class="space-y-3">
						<div class="flex items-center gap-3">
							<input
								type="radio"
								id="send-now"
								value="now"
								v-model="scheduleMode"
								class="w-4 h-4 text-violet-600"
							/>
							<label for="send-now" class="text-sm font-medium text-slate-700 dark:text-slate-300">
								Send immediately
							</label>
						</div>
						<div class="flex items-center gap-3">
							<input
								type="radio"
								id="schedule"
								value="schedule"
								v-model="scheduleMode"
								class="w-4 h-4 text-violet-600"
							/>
							<label for="schedule" class="text-sm font-medium text-slate-700 dark:text-slate-300">
								Schedule for later
							</label>
						</div>
						<div v-if="scheduleMode === 'schedule'" class="ml-7">
							<input
								v-model="scheduledDateTime"
								type="datetime-local"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
							/>
						</div>
					</div>

					<!-- Error Message -->
					<div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
						<p class="text-sm text-red-700 dark:text-red-400">{{ error }}</p>
					</div>
				</div>

				<!-- Footer -->
				<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 rounded-b-xl">
					<button
						@click="$emit('close')"
						class="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
					>
						Cancel
					</button>
					<button
						@click="handleSend"
						:disabled="!isValid || isSending"
						class="px-4 py-2 text-sm font-medium text-white bg-violet-600 hover:bg-violet-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{{ isSending ? 'Sending...' : scheduleMode === 'schedule' ? 'Schedule Notification' : 'Send Notification' }}
					</button>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import axios from 'axios';

const props = defineProps<{
	networkId: number;
}>();

const emit = defineEmits<{
	close: [];
	sent: [];
}>();

const form = ref({
	type: 'scheduled_maintenance',
	priority: 'medium',
	title: '',
	message: '',
});

const scheduleMode = ref<'now' | 'schedule'>('now');
const scheduledDateTime = ref('');
const error = ref<string | null>(null);
const isSending = ref(false);

const isValid = computed(() => {
	return form.value.title.trim().length > 0 && form.value.message.trim().length > 0;
});

async function handleSend() {
	if (!isValid.value) return;
	
	error.value = null;
	isSending.value = true;
	
	try {
		const payload: any = {
			type: form.value.type,
			priority: form.value.priority,
			title: form.value.title,
			message: form.value.message,
		};
		
		if (scheduleMode.value === 'schedule' && scheduledDateTime.value) {
			// Convert local datetime to ISO string
			const date = new Date(scheduledDateTime.value);
			payload.scheduled_at = date.toISOString();
		}
		
		await axios.post(`/api/notifications/networks/${props.networkId}/send`, payload);
		
		emit('sent');
		emit('close');
	} catch (e: any) {
		error.value = e.response?.data?.detail || e.message || 'Failed to send notification';
	} finally {
		isSending.value = false;
	}
}
</script>
