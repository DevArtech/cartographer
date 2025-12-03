import { createRouter, createWebHistory } from 'vue-router';
import MainApp from './components/MainApp.vue';
import EmbedView from './components/EmbedView.vue';
import AcceptInvite from './components/AcceptInvite.vue';

const routes = [
	{
		path: '/',
		name: 'main',
		component: MainApp
	},
	{
		path: '/embed/:embedId',
		name: 'embed',
		component: EmbedView,
		props: true
	},
	{
		path: '/accept-invite',
		name: 'accept-invite',
		component: AcceptInvite
	}
];

const router = createRouter({
	history: createWebHistory(),
	routes
});

export default router;
