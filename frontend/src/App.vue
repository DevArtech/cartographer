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
			<main class="flex-1 p-3 relative">
				<!-- Interaction mode toggle (top-right) -->
				<div class="absolute top-2 right-3 z-10">
					<div class="rounded border border-slate-300 bg-white shadow-sm overflow-hidden flex items-center">
						<button
							class="px-3 py-1 text-xs"
							:class="mode === 'pan' ? 'bg-blue-600 text-white' : 'text-slate-700 hover:bg-slate-100'"
							@click="mode = 'pan'"
							title="Pan mode (default)"
						>
							Pan
						</button>
						<button
							class="px-3 py-1 text-xs border-l border-slate-300"
							:class="mode === 'edit' ? 'bg-blue-600 text-white' : 'text-slate-700 hover:bg-slate-100'"
							@click="mode = 'edit'"
							title="Edit nodes (drag + type) + Pan"
						>
							Edit
						</button>
					</div>
				</div>
				<!-- Node configuration panel (bottom-right) -->
				<div class="absolute bottom-2 right-3 z-10">
					<div v-if="mode === 'edit' && selectedNode" class="flex items-center gap-2 bg-white border border-slate-300 rounded px-2 py-1 shadow-sm">
						<span class="text-xs text-slate-600">Type:</span>
						<select class="text-xs border border-slate-300 rounded px-1 py-0.5"
							v-model="editRole"
							@change="onChangeRole"
						>
							<option value="gateway/router">Gateway / Router</option>
							<option value="firewall">Firewall</option>
							<option value="switch/ap">Switch / AP</option>
							<option value="server">Server</option>
							<option value="service">Service</option>
							<option value="nas">NAS</option>
							<option value="client">Client</option>
							<option value="unknown">Unknown</option>
						</select>
						<span class="text-xs text-slate-600 ml-3">IP:</span>
						<input class="text-xs border border-slate-300 rounded px-1 py-0.5 w-36"
							v-model="editIp"
							@change="onChangeIp"
							placeholder="192.168.1.10"
						/>
						<span class="text-xs text-slate-600">Name:</span>
						<input class="text-xs border border-slate-300 rounded px-1 py-0.5 w-44"
							v-model="editHostname"
							@change="onChangeHostname"
							placeholder="device.local"
						/>
						<span class="text-xs text-slate-600 ml-3">Connect to:</span>
						<select class="text-xs border border-slate-300 rounded px-1 py-0.5"
							v-model="connectParent"
							@change="onChangeParent"
						>
							<option v-for="opt in connectOptions" :key="opt.id" :value="opt.id">
								{{ opt.name }}
							</option>
						</select>
					</div>
				</div>
				<div class="w-full h-full">
					<NetworkMap
						v-if="parsed"
						:data="parsed.root"
						:mode="mode"
						:selectedId="selectedId"
						@nodeSelected="id => selectedId = id"
					/>
					<div v-else class="h-full rounded border border-dashed border-slate-300 flex items-center justify-center text-slate-500">
						No map loaded yet.
					</div>
				</div>
			</main>
		</div>
		<!-- Terminal / Logs Panel -->
		<div 
			v-if="logs.length" 
			class="flex flex-col border-t border-slate-200 bg-slate-50 transition-all ease-linear duration-75"
			:style="{ height: logsHeight + 'px' }"
		>
			<!-- Resize Handle -->
			<div 
				class="h-1 bg-slate-200 cursor-row-resize hover:bg-blue-400 active:bg-blue-600 flex justify-center"
				@mousedown.prevent="startResize"
			>
				<div class="w-12 h-0.5 bg-slate-400 rounded my-auto"></div>
			</div>

			<!-- Logs Content -->
			<div 
				ref="logContainer" 
				class="flex-1 overflow-auto font-mono text-xs px-3 py-2"
			>
				<div v-for="(line, idx) in logs" :key="idx" class="whitespace-pre-wrap text-slate-700">
					<template v-if="downloadHref(line)">
						<a :href="downloadHref(line)!" class="text-blue-600 underline" target="_blank" rel="noopener">
							Download network_map.txt
						</a>
					</template>
					<template v-else>
						{{ line }}
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount, computed } from "vue";
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
const mode = ref<'pan' | 'edit'>('pan'); // interaction mode
const editRole = ref<string>('unknown');
const connectParent = ref<string>('');
const editIp = ref<string>('');
const editHostname = ref<string>('');

// Terminal Resize Logic
const logsHeight = ref(192); // Default 12rem (48 * 4px)
const logContainer = ref<HTMLDivElement | null>(null);
let isResizing = false;

function startResize(e: MouseEvent) {
	isResizing = true;
	document.addEventListener('mousemove', handleResize);
	document.addEventListener('mouseup', stopResize);
	document.body.style.userSelect = 'none';
}

function handleResize(e: MouseEvent) {
	if (!isResizing) return;
	// Calculate new height based on window height - mouse Y
	// But capped between 100px and 80% of screen
	const newHeight = window.innerHeight - e.clientY;
	if (newHeight > 100 && newHeight < window.innerHeight * 0.8) {
		logsHeight.value = newHeight;
	}
}

function stopResize() {
	isResizing = false;
	document.removeEventListener('mousemove', handleResize);
	document.removeEventListener('mouseup', stopResize);
	document.body.style.userSelect = '';
}

const { applySavedPositions } = useMapLayout();
const { parseNetworkMap } = useNetworkData();

function onUpdateMap(p: ParsedNetworkMap) {
	parsed.value = p;
	selectedId.value = undefined;
}

function findNodeById(n: TreeNode, id?: string): TreeNode | undefined {
	if (!id) return undefined;
	if (n.id === id) return n;
	for (const c of (n.children || [])) {
		const f = findNodeById(c, id);
		if (f) return f;
	}
	return undefined;
}

function flattenDevices(root: TreeNode): TreeNode[] {
	const list: TreeNode[] = [root]; // include router
	for (const g of (root.children || [])) {
		for (const c of (g.children || [])) list.push(c);
	}
	return list;
}

function findGroupByPrefix(root: TreeNode, prefix: string): TreeNode | undefined {
	return (root.children || []).find(c => c.name.toLowerCase().startsWith(prefix));
}

function removeFromAllGroups(root: TreeNode, id: string): TreeNode | undefined {
	for (const g of (root.children || [])) {
		const idx = (g.children || []).findIndex(c => c.id === id);
		if (idx !== -1) {
			const [node] = g.children!.splice(idx, 1);
			return node;
		}
	}
	return undefined;
}

function walkAll(root: TreeNode, fn: (n: TreeNode, parent?: TreeNode) => void) {
	fn(root, undefined);
	for (const g of (root.children || [])) {
		for (const c of (g.children || [])) {
			fn(c, g);
		}
	}
}

function onChangeRole() {
	if (!parsed.value || !selectedId.value) return;
	const root = parsed.value.root;
	const node = findNodeById(root, selectedId.value);
	if (!node) return;
	node.role = editRole.value as any;
	// Move across tiers if needed
	const role = node.role || 'unknown';
	let targetPrefix = '';
	if (role === 'firewall' || role === 'switch/ap') targetPrefix = 'infrastructure';
	else if (role === 'server' || role === 'service' || role === 'nas') targetPrefix = 'servers';
	else if (role === 'client' || role === 'unknown') targetPrefix = 'clients';
	// gateway/router remains at root (no move)
	if (targetPrefix) {
		const existingParent = removeFromAllGroups(root, node.id);
		const targetGroup = findGroupByPrefix(root, targetPrefix);
		if (existingParent && targetGroup) {
			targetGroup.children = targetGroup.children || [];
			targetGroup.children.push(existingParent);
		}
	}
	// Refresh view
	parsed.value = { ...parsed.value };
}

const selectedNode = computed(() => {
	if (!parsed.value) return undefined;
	return findNodeById(parsed.value.root, selectedId.value);
});

const connectOptions = computed(() => {
	if (!parsed.value) return [];
	const root = parsed.value.root;
	const all = flattenDevices(root);
	const current = selectedNode.value;
	if (!current) return [];
	// Allow connecting to ANY device (including router) except itself
	const allowed = all.filter(d => d.id !== current.id);
	return allowed.map(d => ({ id: d.id, name: d.name }));
});

watch(selectedNode, (n) => {
	// Keep the editor UI in sync with the selected node
	editRole.value = (n as any)?.role || 'unknown';
	connectParent.value = (n as any)?.parentId || (parsed.value?.root.id || '');
	editIp.value = (n as any)?.ip || (n as any)?.id || '';
	editHostname.value = (n as any)?.hostname || '';
});

function onChangeParent() {
	if (!parsed.value || !selectedId.value) return;
	const node = findNodeById(parsed.value.root, selectedId.value);
	if (!node) return;
	(node as any).parentId = connectParent.value || undefined;
	parsed.value = { ...parsed.value };
}

function refreshNodeLabel(n: TreeNode) {
	const ip = (n as any)?.ip || n.id;
	const hn = (n as any)?.hostname || 'Unknown';
	n.name = `${ip} (${hn})`;
}

function onChangeIp() {
	if (!parsed.value || !selectedId.value) return;
	const root = parsed.value.root;
	const node = findNodeById(root, selectedId.value);
	if (!node) return;
	const oldId = node.id;
	(node as any).ip = editIp.value.trim();
	if ((node as any).ip) node.id = (node as any).ip;
	// Update any child referencing this as parent
	walkAll(root, (n) => {
		if ((n as any).parentId === oldId) (n as any).parentId = node.id;
	});
	refreshNodeLabel(node);
	selectedId.value = node.id;
	parsed.value = { ...parsed.value };
}

function onChangeHostname() {
	if (!parsed.value || !selectedId.value) return;
	const node = findNodeById(parsed.value.root, selectedId.value);
	if (!node) return;
	(node as any).hostname = editHostname.value.trim();
	refreshNodeLabel(node);
	parsed.value = { ...parsed.value };
}

function onApplyLayout(layout: any) {
	if (layout.root) {
		// Full project load
		parsed.value = {
			raw: "", // Not available when loading from JSON, but we have the root
			root: layout.root
		};
	}
	
	if (!parsed.value) return;
	
	applySavedPositions(parsed.value.root, layout);
	
	// Trigger reactivity with shallow replacement (if we have raw source)
	if (parsed.value.raw) {
		parsed.value = parseNetworkMap(parsed.value.raw);
		applySavedPositions(parsed.value.root, layout);
	} else {
		// Force refresh if we just loaded the tree
		parsed.value = { ...parsed.value };
	}
}

function onLog(line: string) {
	logs.value.push(line);
	if (logs.value.length > 2000) logs.value.splice(0, logs.value.length - 2000);
	
	// Auto-scroll to bottom
	nextTick(() => {
		if (logContainer.value) {
			logContainer.value.scrollTop = logContainer.value.scrollHeight;
		}
	});
}
function onRunning(isRunning: boolean) {
	running.value = isRunning;
}
function onClearLogs() {
	logs.value = [];
}

function downloadHref(line: string): string | null {
	const m = /^DOWNLOAD:\s+(https?:\/\/[^\s]+)$/i.exec(line.trim());
	return m ? m[1] : null;
}
</script>

<style scoped>
</style>


