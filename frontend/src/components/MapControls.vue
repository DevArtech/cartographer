<template>
	<div class="flex items-center gap-2 p-3 border-b border-slate-200 bg-white">
		<button @click="runMapper" class="px-3 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-500 disabled:opacity-50" :disabled="loading">
			<span v-if="!loading">Run Mapper</span>
			<span v-else>Running…</span>
		</button>
		<button @click="saveLayout" class="px-3 py-2 rounded bg-emerald-600 text-white text-sm hover:bg-emerald-500">
			Save Map
		</button>
		<label class="px-3 py-2 rounded bg-slate-700 text-white text-sm hover:bg-slate-600 cursor-pointer">
			Load Map
			<input type="file" accept="application/json" class="hidden" @change="onLoadFile" />
		</label>
		<div class="ml-auto text-xs text-slate-500">
			<span v-if="message">{{ message }}</span>
		</div>
	</div>
</template>

<script lang="ts" setup>
import axios from "axios";
import { onBeforeUnmount, ref } from "vue";
import type { ParsedNetworkMap, TreeNode } from "../types/network";
import { useNetworkData } from "../composables/useNetworkData";
import { useMapLayout } from "../composables/useMapLayout";

const props = defineProps<{
	root: TreeNode;
}>();

const emit = defineEmits<{
	(e: "updateMap", parsed: ParsedNetworkMap): void;
	(e: "applyLayout", layout: any): void;
	(e: "log", line: string): void;
	(e: "running", isRunning: boolean): void;
	(e: "clearLogs"): void;
}>();

const loading = ref(false);
const message = ref("");
const { parseNetworkMap } = useNetworkData();
const { exportLayout, importLayout } = useMapLayout();
let es: EventSource | null = null;

async function runMapper() {
	message.value = "";
	emit("clearLogs");
	startSSE();
}

function saveLayout() {
	const layout = exportLayout(props.root);
	const blob = new Blob([JSON.stringify(layout, null, 2)], { type: "application/json" });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = "network_layout.json";
	document.body.appendChild(a);
	a.click();
	URL.revokeObjectURL(url);
	document.body.removeChild(a);
}

function onLoadFile(e: Event) {
	const input = e.target as HTMLInputElement;
	if (!input.files || !input.files.length) return;
	const file = input.files[0];
	const reader = new FileReader();
	reader.onload = () => {
		try {
			const text = String(reader.result || "");
			const layout = importLayout(text);
			emit("applyLayout", layout);
			message.value = "Layout loaded";
		} catch (err: any) {
			message.value = err?.message || "Failed to load layout";
		}
	};
	reader.readAsText(file);
}

function startSSE() {
	endSSE();
	loading.value = true;
	message.value = "Running mapper…";
	emit("running", true);
	try {
		es = new EventSource("/api/run-mapper/stream");
		es.addEventListener("log", (e: MessageEvent) => {
			emit("log", String(e.data || ""));
		});
		es.addEventListener("result", (e: MessageEvent) => {
			try {
				const payload = JSON.parse(String(e.data || "{}"));
				const content = String(payload?.content || "");
				if (content) {
					const parsed = parseNetworkMap(content);
					emit("updateMap", parsed);
				}
			} catch {
				/* ignore parse errors */
			}
		});
		es.addEventListener("done", (e: MessageEvent) => {
			message.value = "Mapper completed";
			loading.value = false;
			emit("running", false);
			endSSE();
		});
		es.onerror = () => {
			if (loading.value) {
				message.value = "Stream error";
				loading.value = false;
			}
			emit("running", false);
			endSSE();
		};
	} catch (err: any) {
		message.value = err?.message || "Failed to start log stream";
		loading.value = false;
		emit("running", false);
	}
}

function endSSE() {
	if (es) {
		es.close();
		es = null;
	}
}

onBeforeUnmount(() => endSSE());
</script>


