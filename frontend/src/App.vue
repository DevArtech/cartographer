<template>
	<router-view />
</template>

<script lang="ts" setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';

onMounted(() => {
	// Handle Discord OAuth callback in popup window
	const route = useRoute();
	const urlParams = new URLSearchParams(window.location.search);
	
	// Check if we're in a popup window and have Discord OAuth callback
	if (window.opener && urlParams.has('discord_oauth')) {
		const status = urlParams.get('discord_oauth');
		const username = urlParams.get('username');
		const message = urlParams.get('message');
		
		// Notify parent window via postMessage
		window.opener.postMessage({
			type: 'discord_oauth_callback',
			status: status,
			username: username,
			message: message
		}, window.location.origin);
		
		// Close the popup
		window.close();
	}
});

// Listen for messages from popup windows (if this is the parent)
if (typeof window !== 'undefined') {
	window.addEventListener('message', (event) => {
		// Verify message is from same origin
		if (event.origin !== window.location.origin) {
			return;
		}
		
		if (event.data && event.data.type === 'discord_oauth_callback') {
			// Trigger a custom event that components can listen to
			window.dispatchEvent(new CustomEvent('discord-oauth-complete', {
				detail: event.data
			}));
		}
	});
}
</script>
