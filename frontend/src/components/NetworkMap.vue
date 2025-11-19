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
	mode?: 'pan' | 'edit';
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

function roleIcon(role?: string): string {
	const r = role || "unknown";
	switch (r) {
		case "gateway/router": return "📡";
		case "firewall": return "🧱";
		case "switch/ap": return "🔀";
		case "server": return "🖥️";
		case "service": return "⚙️";
		case "nas": return "🗄️";
		case "client": return "💻";
		default: return "❓";
	}
}

	function render() {
	const svg = d3.select(svgRef.value!);
	svg.selectAll("*").remove();

	const width = (svgRef.value?.clientWidth || 800);
	const height = (svgRef.value?.clientHeight || 600);

	const g = svg.attr("viewBox", [0, 0, width, height].join(" ")).append("g").attr("class", "zoom-layer").attr("transform", "translate(24,24)");

	const zoom = d3.zoom<SVGSVGElement, unknown>()
		.scaleExtent([0.1, 4])
		.on("zoom", (event) => {
			g.attr("transform", event.transform);
		});
	
	svg.call(zoom).call(zoom.transform, d3.zoomIdentity.translate(24, 24));

	// Stop zoom propagation on nodes so dragging works
	svg.on("dblclick.zoom", null);

	// ─────────────────────────────────────────────────────────────────────────────
	// Custom layered device-only layout (top → down)
	// Rows: [Gateway] ↓ [Infrastructure] ↓ [Servers/Services/NAS] ↓ [Clients/Unknown]
	// Links: gateway → each infra; primaryInfra → servers/services/nas; primaryInfra → clients
	// ─────────────────────────────────────────────────────────────────────────────
	const data = props.data;
	const children = data.children || [];
	const findGroup = (prefix: string) => children.find(c => c.name.toLowerCase().startsWith(prefix));
	const infraGroup = findGroup("infrastructure");
	const serversGroup = findGroup("servers");
	const clientsGroup = findGroup("clients");

	type DrawNode = { id: string; name: string; role?: string; x: number; y: number; ref?: TreeNode; };
	type DrawLink = { source: DrawNode; target: DrawNode; };

	const marginX = 40;
	const marginY = 60;
	const rowHeight = 120;
	const nodeGapX = 90;

	// Helpers for horizontal centering within a row
	const rowY = (row: number) => marginY + row * rowHeight;
	const centerRowX = (count: number) => {
		const total = Math.max(0, (count - 1) * nodeGapX);
		return (width - marginX * 2 - total) / 2 + marginX;
	};

	const nodes: DrawNode[] = [];
	const links: DrawLink[] = [];

	// Router (root)
	const router: DrawNode = {
		id: data.id,
		name: data.name,
		role: data.role,
		x: typeof (data as any).fx === "number" ? (data as any).fx : (width / 2),
		y: typeof (data as any).fy === "number" ? (data as any).fy : rowY(0),
		ref: data,
	};
	if (typeof (data as any).fx !== "number" || typeof (data as any).fy !== "number") {
		(data as any).fx = router.x; (data as any).fy = router.y; updatePosition(router.id, router.x, router.y);
	}
	nodes.push(router);

	// Collect devices by tier (no group anchor nodes)
	const infraDevices = (infraGroup?.children || []).slice();
	const serverDevices = (serversGroup?.children || []).slice();
	const clientDevices = (clientsGroup?.children || []).slice();

	// Primary infra (prefer firewall)
	const primaryInfra = infraDevices.find(d => d.role === "firewall") || infraDevices[0] || data;

	// Place infra devices (row 1)
	{
		const startX = centerRowX(Math.max(1, infraDevices.length));
		infraDevices.forEach((c, idx) => {
			const dev: DrawNode = {
				id: c.id, name: c.name, role: c.role,
				x: typeof (c as any).fx === "number" ? (c as any).fx : startX + idx * nodeGapX,
				y: typeof (c as any).fy === "number" ? (c as any).fy : rowY(1),
				ref: c,
			};
			if (typeof (c as any).fx !== "number" || typeof (c as any).fy !== "number") {
				(c as any).fx = dev.x; (c as any).fy = dev.y; updatePosition(c.id, dev.x, dev.y);
			}
			nodes.push(dev);
			links.push({ source: router, target: dev });
		});
	}

	// Place servers/services/nas (row 2) – connect to primary infra
	{
		const startX = centerRowX(Math.max(1, serverDevices.length));
		serverDevices.forEach((c, idx) => {
			const dev: DrawNode = {
				id: c.id, name: c.name, role: c.role,
				x: typeof (c as any).fx === "number" ? (c as any).fx : startX + idx * nodeGapX,
				y: typeof (c as any).fy === "number" ? (c as any).fy : rowY(2),
				ref: c,
			};
			if (typeof (c as any).fx !== "number" || typeof (c as any).fy !== "number") {
				(c as any).fx = dev.x; (c as any).fy = dev.y; updatePosition(c.id, dev.x, dev.y);
			}
			nodes.push(dev);
			links.push({
				source: nodes.find(n => n.id === (primaryInfra as any).id) || router,
				target: dev
			});
		});
	}

	// Place clients/unknown (row 3) – connect to primary infra
	{
		const startX = centerRowX(Math.max(1, clientDevices.length));
		clientDevices.forEach((c, idx) => {
			const dev: DrawNode = {
				id: c.id, name: c.name, role: c.role,
				x: typeof (c as any).fx === "number" ? (c as any).fx : startX + idx * nodeGapX,
				y: typeof (c as any).fy === "number" ? (c as any).fy : rowY(3),
				ref: c,
			};
			if (typeof (c as any).fx !== "number" || typeof (c as any).fy !== "number") {
				(c as any).fx = dev.x; (c as any).fy = dev.y; updatePosition(c.id, dev.x, dev.y);
			}
			nodes.push(dev);
			links.push({
				source: nodes.find(n => n.id === (primaryInfra as any).id) || router,
				target: dev
			});
		});
	}

	// Build id → DrawNode map
	const idToNode = new Map<string, DrawNode>();
	nodes.forEach(n => idToNode.set(n.id, n));

	// Build links honoring explicit parentId when present
	const makeDefaultParent = (node: DrawNode): DrawNode => {
		if (node.id === router.id) return router;
		if (node.role === 'firewall' || node.role === 'switch/ap') return router;
		// default others to primary infra if available; else router
		const p = idToNode.get((primaryInfra as any)?.id) || router;
		return p;
	};
	links.length = 0;
	for (const n of nodes) {
		if (n.id === router.id) continue;
		const ref = n.ref as any;
		const parentId = ref?.parentId as string | undefined;
		const parent = (parentId && idToNode.get(parentId)) || makeDefaultParent(n);
		if (parent) links.push({ source: parent, target: n });
	}

	// Draw links (curved, dotted, vertical routing)
	const linkPath = (s: DrawNode, t: DrawNode) => {
		const my = (s.y + t.y) / 2;
		return `M${s.x},${s.y} C ${s.x},${my} ${t.x},${my} ${t.x},${t.y}`;
	};
	g.append("g")
		.selectAll("path.link")
		.data(links)
		.join("path")
		.attr("class", "link")
		.attr("fill", "none")
		.attr("stroke", "#94a3b8")
		.attr("stroke-width", 1.5)
		.attr("stroke-dasharray", "2,4")
		.attr("d", (d: any) => linkPath(d.source, d.target));

	// Draw nodes
	const node = g.append("g")
		.selectAll("g.node")
		.data(nodes)
		.join("g")
		.attr("class", "node")
		.attr("transform", (d: any) => `translate(${d.x},${d.y})`)
		.style("cursor", "pointer")
		.on("click", (_, d: any) => emit("nodeSelected", d.id));

	// Selection halo (visible only when selected)
	node.append("circle")
		.attr("r", 12)
		.attr("fill", "white")
		.attr("stroke", (d: any) => d.id === props.selectedId ? "#f59e0b" : "none")
		.attr("stroke-width", 2);

	// Icon
	node.append("text")
		.attr("dy", "0.35em")
		.attr("text-anchor", "middle")
		.attr("font-size", 16)
		.text((d: any) => roleIcon(d.role));

	node.append("text")
		.attr("dy", "1.9em")
		.attr("text-anchor", "middle")
		.attr("class", "node-label fill-slate-700")
		.text((d: any) => d.name);

	// Drag behavior (persist fx/fy) - only when in 'move' mode
	if (props.mode === 'edit') {
		const drag = d3.drag<SVGGElement, any>()
			.on("start", function () {
				d3.select(this).raise();
			})
			.on("drag", function (event, d: any) {
				// Convert pointer to content coordinates accounting for zoom/pan
				const svgEl = svgRef.value as SVGSVGElement;
				const t = d3.zoomTransform(svgEl);
				const [sx, sy] = d3.pointer(event, svgEl);
				const [cx, cy] = t.invert([sx, sy]);
				d.x = cx; d.y = cy;
				d3.select(this).attr("transform", `translate(${d.x},${d.y})`);
				if (d.ref) { (d.ref as any).fx = d.x; (d.ref as any).fy = d.y; updatePosition(d.id, d.x, d.y); }
				// Update connected links
				g.selectAll("path.link").attr("d", (l: any) => linkPath(l.source, l.target));
			});
		node.call(drag as any);
	}

	// Cleanup
	cleanup = () => {
		svg.selectAll("*").remove();
	};
}

onMounted(() => render());
onBeforeUnmount(() => {
	if (cleanup) cleanup();
});

watch(() => [props.data, props.selectedId, props.mode], () => {
	render();
}, { deep: true });
</script>

<style scoped>
</style>


