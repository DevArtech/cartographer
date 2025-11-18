<template>
	<div class="h-screen flex flex-col">
		<MapControls
			:root="parsed?.root || emptyRoot"
			@updateMap="onUpdateMap"
			@applyLayout="onApplyLayout"
			@log="onLog"
			@running="onRunning"
			@clearLogs="onClearLogs"
		/>
		<div class="flex flex-1 min-h-0">
			<aside class="w-80 border-r border-slate-200 bg-white">
				<DeviceList
					v-if="parsed"
					:root="parsed.root"
					:selectedId="selectedId"
					@select="id => selectedId = id"
				/>
				<div v-else class="p-4 text-sm text-slate-600">
					Run the mapper to generate a network map, or load a saved layout.
				</div>
			</aside>
			<main class="flex-1 p-3">
				<div class="w-full h-full">
					<NetworkMap
						v-if="parsed"
						:data="parsed.root"
						:selectedId="selectedId"
						@nodeSelected="id => selectedId = id"
					/>
					<div v-else class="h-full rounded border border-dashed border-slate-300 flex items-center justify-center text-slate-500">
						No map loaded yet.
					</div>
				</div>
			</main>
		</div>
		<div v-if="logs.length" class="h-48 overflow-auto border-t border-slate-200 bg-slate-50 font-mono text-xs px-3 py-2">
			<div v-for="(line, idx) in logs" :key="idx" class="whitespace-pre-wrap text-slate-700">{{ line }}</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { ref } from "vue";
import MapControls from "./components/MapControls.vue";
import DeviceList from "./components/DeviceList.vue";
import NetworkMap from "./components/NetworkMap.vue";
import type { ParsedNetworkMap, TreeNode } from "./types/network";
import { useMapLayout } from "./composables/useMapLayout";
import { useNetworkData } from "./composables/useNetworkData";

const parsed = ref<ParsedNetworkMap | null>(null);
const selectedId = ref<string | undefined>(undefined);
const emptyRoot: TreeNode = { id: "root", name: "Network", role: "group", children: [] };
const logs = ref<string[]>([]);
const running = ref(false);

const { applySavedPositions } = useMapLayout();
const { parseNetworkMap } = useNetworkData();

function onUpdateMap(p: ParsedNetworkMap) {
	parsed.value = p;
	selectedId.value = undefined;
}

function onApplyLayout(layout: any) {
	if (!parsed.value) return;
	applySavedPositions(parsed.value.root, layout);
	// Trigger reactivity with shallow replacement
	parsed.value = parseNetworkMap(parsed.value.raw);
	applySavedPositions(parsed.value.root, layout);
}

function onLog(line: string) {
	logs.value.push(line);
	if (logs.value.length > 2000) logs.value.splice(0, logs.value.length - 2000);
}
function onRunning(isRunning: boolean) {
	running.value = isRunning;
}
function onClearLogs() {
	logs.value = [];
}
</script>

<style scoped>
</style>


