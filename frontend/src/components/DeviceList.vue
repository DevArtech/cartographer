<template>
	<div class="h-full flex flex-col">
		<div class="p-3 border-b border-slate-200">
			<input
				v-model="query"
				type="text"
				placeholder="Search by IP, hostname, role..."
				class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
			/>
		</div>
		<div class="flex-1 overflow-auto">
			<ul>
				<li
					v-for="d in filtered"
					:key="d.id"
					@click="$emit('select', d.id)"
					class="px-3 py-2 border-b border-slate-100 hover:bg-slate-50 cursor-pointer flex items-center gap-2"
					:class="{'bg-amber-50': d.id === selectedId }"
				>
					<span class="w-2 h-2 rounded-full" :class="roleDot(d.role)"></span>
					<span class="text-xs text-slate-500">{{ d.role }}</span>
					<span class="text-sm text-slate-800">{{ d.name }}</span>
				</li>
			</ul>
		</div>
	</div>
</template>

<script lang="ts" setup>
import { computed, ref } from "vue";
import type { TreeNode } from "../types/network";

const props = defineProps<{
	root: TreeNode;
	selectedId?: string;
}>();

defineEmits<{
	(e: "select", id: string): void;
}>();

const query = ref("");

function flatten(root: TreeNode): TreeNode[] {
	const res: TreeNode[] = [];
	const walk = (n: TreeNode) => {
		res.push(n);
		for (const c of n.children || []) walk(c);
	};
	walk(root);
	return res.filter(n => n.role !== "group");
}

const all = computed(() => flatten(props.root));
const filtered = computed(() => {
	const q = query.value.trim().toLowerCase();
	if (!q) return all.value;
	return all.value.filter(n =>
		(n.name?.toLowerCase()?.includes(q)) ||
		(n.role || "").toLowerCase().includes(q) ||
		(n.ip || "").toLowerCase().includes(q) ||
		(n.hostname || "").toLowerCase().includes(q),
	);
});

function roleDot(role?: string) {
	switch (role) {
		case "gateway/router": return "bg-red-500";
		case "switch/ap": return "bg-blue-500";
		case "firewall": return "bg-orange-500";
		case "server": return "bg-green-500";
		case "service": return "bg-emerald-500";
		case "nas": return "bg-purple-500";
		case "client": return "bg-cyan-500";
		default: return "bg-gray-400";
	}
}
</script>


