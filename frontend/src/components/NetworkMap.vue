<template>
	<div class="w-full h-full">
		<svg ref="svgRef" class="w-full h-full bg-white rounded border border-slate-200"></svg>
	</div>
</template>

<script lang="ts" setup>
import * as d3 from "d3";
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import type { TreeNode } from "../types/network";
import { useMapLayout } from "../composables/useMapLayout";

const props = defineProps<{
	data: TreeNode;
	selectedId?: string;
}>();

const emit = defineEmits<{
	(e: "nodeSelected", id: string | undefined): void;
}>();

const svgRef = ref<SVGSVGElement | null>(null);
const { updatePosition } = useMapLayout();

let cleanup: (() => void) | null = null;

function roleClass(role?: string): string {
	if (!role) return "role-unknown";
	const map: Record<string, string> = {
		"gateway/router": "role-gateway",
		"switch/ap": "role-switch",
		"firewall": "role-firewall",
		"server": "role-server",
		"service": "role-service",
		"nas": "role-nas",
		"client": "role-client",
		"group": "role-unknown",
		"unknown": "role-unknown",
	};
	return map[role] || "role-unknown";
}

function render() {
	const svg = d3.select(svgRef.value!);
	svg.selectAll("*").remove();

	const width = (svgRef.value?.clientWidth || 800);
	const height = (svgRef.value?.clientHeight || 600);

	const g = svg.attr("viewBox", [0, 0, width, height].join(" ")).append("g").attr("transform", "translate(24,24)");

	const layout = d3.tree<TreeNode>().nodeSize([40, 160]);
	const root = d3.hierarchy<TreeNode>(props.data);
	layout(root);

	// Links
	g.append("g")
		.selectAll("path")
		.data(root.links())
		.join("path")
		.attr("fill", "none")
		.attr("stroke", "#94a3b8")
		.attr("stroke-width", 1.5)
		.attr("d", d3.linkHorizontal()
			.x((d: any) => d.y)
			.y((d: any) => d.x) as any
		);

	// Nodes group
	const node = g.append("g")
		.selectAll("g")
		.data(root.descendants())
		.join("g")
		.attr("transform", (d: any) => `translate(${d.y},${d.x})`)
		.style("cursor", "pointer")
		.on("click", (_, d: any) => {
			emit("nodeSelected", d.data.id);
		});

	// Node visual
	node.append("circle")
		.attr("r", 10)
		.attr("class", (d: any) => {
			const rc = roleClass(d.data.role);
			const selected = d.data.id === props.selectedId ? " ring-2 ring-amber-400" : "";
			return `${rc}${selected}`;
		})
		.attr("stroke", "#1f2937")
		.attr("stroke-width", 1);

	// Labels
	node.append("text")
		.attr("dy", "0.32em")
		.attr("x", 14)
		.attr("class", "node-label fill-slate-700")
		.text((d: any) => d.data.name);

	// Drag behavior to freeform adjust y/x (store as fx/fy)
	const drag = d3.drag<SVGGElement, any>()
		.on("start", function (event, d) {
			d3.select(this).raise();
		})
		.on("drag", function (event, d) {
			const nx = event.y;
			const ny = event.x;
			d.x = nx;
			d.y = ny;
			d.data.fx = ny;
			d.data.fy = nx;
			updatePosition(d.data.id, ny, nx);
			d3.select(this).attr("transform", `translate(${d.y},${d.x})`);
			// Update links connected to this node
			g.selectAll("path")
				.attr("d", d3.linkHorizontal()
					.x((l: any) => {
						if (l.source === d) return d.y;
						if (l.target === d) return d.y;
						return l.y;
					})
					.y((l: any) => {
						if (l.source === d) return d.x;
						if (l.target === d) return d.x;
						return l.x;
					}) as any
				);
		});

	node.call(drag as any);

	// Apply saved positions if present
	node.attr("transform", (d: any) => {
		if (typeof d.data.fx === "number" && typeof d.data.fy === "number") {
			d.x = d.data.fy;
			d.y = d.data.fx;
			return `translate(${d.y},${d.x})`;
		}
		return `translate(${d.y},${d.x})`;
	});

	// Cleanup
	cleanup = () => {
		svg.selectAll("*").remove();
	};
}

onMounted(() => render());
onBeforeUnmount(() => {
	if (cleanup) cleanup();
});

watch(() => [props.data, props.selectedId], () => {
	render();
}, { deep: true });
</script>

<style scoped>
</style>


