<script lang="ts">
	import Toast from "$lib/toast.svelte"

	let { children } = $props();
</script>

<Toast />

<svelte:head>
	<link rel="icon"/>
</svelte:head>

{@render children()}

<style>
	@import "../../style.css";
</style>