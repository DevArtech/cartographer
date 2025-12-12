<template>
	<div class="space-y-6">
		<!-- Delivery Channels -->
		<div class="space-y-4">
			<h3 class="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
				</svg>
				Delivery Channels
			</h3>
			
			<!-- Email -->
			<div class="p-4 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
				<div class="flex items-center justify-between mb-3">
					<div>
						<p class="font-medium text-slate-900 dark:text-white">Email</p>
						<p class="text-sm text-slate-500 dark:text-slate-400">
							{{ serviceStatus?.email_configured ? 'Using your account email' : 'Email service not configured' }}
						</p>
					</div>
					<button
						@click="toggleEmail"
						:disabled="!serviceStatus?.email_configured"
						class="relative w-12 h-7 rounded-full transition-colors disabled:opacity-50"
						:class="preferences?.email_enabled && serviceStatus?.email_configured ? 'bg-blue-500' : 'bg-slate-300 dark:bg-slate-600'"
					>
						<span
							class="absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform"
							:class="preferences?.email_enabled && serviceStatus?.email_configured ? 'translate-x-5' : ''"
						></span>
					</button>
				</div>
				<button
					v-if="preferences?.email_enabled"
					@click="$emit('test-email')"
					class="px-4 py-2 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
				>
					Send Test Email
				</button>
			</div>
			
			<!-- Discord -->
			<div class="p-4 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
				<div class="flex items-center justify-between mb-3">
					<div>
						<p class="font-medium text-slate-900 dark:text-white">Discord</p>
						<p class="text-sm text-slate-500 dark:text-slate-400">
							{{ discordLink?.linked ? `Linked: @${discordLink.discord_username}` : 'Link your Discord account' }}
						</p>
					</div>
					<button
						@click="toggleDiscord"
						:disabled="!discordLink?.linked"
						class="relative w-12 h-7 rounded-full transition-colors disabled:opacity-50"
						:class="preferences?.discord_enabled && discordLink?.linked ? 'bg-indigo-500' : 'bg-slate-300 dark:bg-slate-600'"
					>
						<span
							class="absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform"
							:class="preferences?.discord_enabled && discordLink?.linked ? 'translate-x-5' : ''"
						></span>
					</button>
				</div>
				<div class="flex gap-2">
					<button
						v-if="!discordLink?.linked"
						@click="$emit('link-discord')"
						class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
					>
						Link Discord Account
					</button>
					<button
						v-else
						@click="$emit('unlink-discord')"
						class="px-4 py-2 text-sm bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
					>
						Unlink
					</button>
					<button
						v-if="preferences?.discord_enabled && discordLink?.linked"
						@click="$emit('test-discord')"
						class="px-4 py-2 text-sm bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-colors"
					>
						Send Test
					</button>
				</div>
			</div>
		</div>
		
		<!-- Notification Types -->
		<div class="space-y-4">
			<h3 class="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
				Notification Types
			</h3>
			<div class="p-4 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 space-y-3">
				<div class="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-700">
					<div class="flex-1">
						<div class="flex items-center gap-2">
							<span class="text-lg">✅</span>
							<span class="font-medium text-slate-900 dark:text-white">Cartographer Up</span>
						</div>
						<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">When Cartographer service comes back online</p>
					</div>
					<button
						@click="toggleCartographerUp"
						class="relative w-11 h-6 rounded-full transition-colors"
						:class="preferences?.cartographer_up_enabled ? 'bg-violet-500' : 'bg-slate-300 dark:bg-slate-600'"
					>
						<span
							class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform"
							:class="preferences?.cartographer_up_enabled ? 'translate-x-5' : ''"
						></span>
					</button>
				</div>
				<div class="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-700">
					<div class="flex-1">
						<div class="flex items-center gap-2">
							<span class="text-lg">🚨</span>
							<span class="font-medium text-slate-900 dark:text-white">Cartographer Down</span>
						</div>
						<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">When Cartographer service goes offline</p>
					</div>
					<button
						@click="toggleCartographerDown"
						class="relative w-11 h-6 rounded-full transition-colors"
						:class="preferences?.cartographer_down_enabled ? 'bg-violet-500' : 'bg-slate-300 dark:bg-slate-600'"
					>
						<span
							class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform"
							:class="preferences?.cartographer_down_enabled ? 'translate-x-5' : ''"
						></span>
					</button>
				</div>
			</div>
		</div>
		
		<!-- Filters -->
		<div class="space-y-4">
			<h3 class="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
				Filters & Limits
			</h3>
			<div class="p-4 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 space-y-4">
				<!-- Minimum Priority -->
				<div>
					<label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
						Minimum Priority
					</label>
					<select
						:value="preferences?.minimum_priority || 'medium'"
						@change="updateMinimumPriority(($event.target as HTMLSelectElement).value)"
						class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
					>
						<option value="low">Low</option>
						<option value="medium">Medium</option>
						<option value="high">High</option>
						<option value="critical">Critical</option>
					</select>
				</div>
				
				<!-- Quiet Hours -->
				<div class="space-y-3">
					<div class="flex items-center justify-between">
						<label class="text-sm font-medium text-slate-700 dark:text-slate-300">
							Quiet Hours
						</label>
						<button
							@click="toggleQuietHours"
							class="relative w-11 h-6 rounded-full transition-colors"
							:class="preferences?.quiet_hours_enabled ? 'bg-violet-500' : 'bg-slate-300 dark:bg-slate-600'"
						>
							<span
								class="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform"
								:class="preferences?.quiet_hours_enabled ? 'translate-x-5' : ''"
							></span>
						</button>
					</div>
					
					<template v-if="preferences?.quiet_hours_enabled">
						<div class="grid grid-cols-2 gap-3">
							<div>
								<label class="block text-xs text-slate-500 dark:text-slate-400 mb-1">Start</label>
								<input
									type="time"
									:value="preferences?.quiet_hours_start || '22:00'"
									@change="updateQuietHoursStart(($event.target as HTMLInputElement).value)"
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
								/>
							</div>
							<div>
								<label class="block text-xs text-slate-500 dark:text-slate-400 mb-1">End</label>
								<input
									type="time"
									:value="preferences?.quiet_hours_end || '08:00'"
									@change="updateQuietHoursEnd(($event.target as HTMLInputElement).value)"
									class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
								/>
							</div>
						</div>
						<div>
							<label class="block text-xs text-slate-500 dark:text-slate-400 mb-1">Timezone</label>
							<select
								:value="preferences?.quiet_hours_timezone || 'UTC'"
								@change="updateQuietHoursTimezone(($event.target as HTMLSelectElement).value)"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
							>
								<option value="UTC">UTC</option>
								<option value="America/New_York">Eastern Time</option>
								<option value="America/Chicago">Central Time</option>
								<option value="America/Denver">Mountain Time</option>
								<option value="America/Los_Angeles">Pacific Time</option>
								<option value="Europe/London">London</option>
								<option value="Europe/Paris">Paris</option>
								<option value="Asia/Tokyo">Tokyo</option>
							</select>
						</div>
						<div>
							<label class="block text-xs text-slate-500 dark:text-slate-400 mb-1">Pass-through Alerts</label>
							<select
								:value="preferences?.quiet_hours_bypass_priority || ''"
								@change="updateQuietHoursBypass(($event.target as HTMLSelectElement).value || null)"
								class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
							>
								<option value="">None</option>
								<option value="low">Low and higher</option>
								<option value="medium">Medium and higher</option>
								<option value="high">High and higher</option>
								<option value="critical">Critical only</option>
							</select>
						</div>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
const props = defineProps<{
	preferences: any;
	serviceStatus: any;
	discordLink: any;
}>();

const emit = defineEmits<{
	update: [update: any];
	'test-email': [];
	'test-discord': [];
	'link-discord': [];
	'unlink-discord': [];
}>();

function toggleEmail() {
	emit('update', { email_enabled: !props.preferences?.email_enabled });
}

function toggleDiscord() {
	if (!props.discordLink?.linked) return;
	emit('update', { discord_enabled: !props.preferences?.discord_enabled });
}

function toggleCartographerUp() {
	emit('update', { cartographer_up_enabled: !props.preferences?.cartographer_up_enabled });
}

function toggleCartographerDown() {
	emit('update', { cartographer_down_enabled: !props.preferences?.cartographer_down_enabled });
}

function updateMinimumPriority(priority: string) {
	emit('update', { minimum_priority: priority });
}

function toggleQuietHours() {
	emit('update', { quiet_hours_enabled: !props.preferences?.quiet_hours_enabled });
}

function updateQuietHoursStart(start: string) {
	emit('update', { quiet_hours_start: start });
}

function updateQuietHoursEnd(end: string) {
	emit('update', { quiet_hours_end: end });
}

function updateQuietHoursTimezone(timezone: string) {
	emit('update', { quiet_hours_timezone: timezone });
}

function updateQuietHoursBypass(priority: string | null) {
	emit('update', { quiet_hours_bypass_priority: priority });
}
</script>
