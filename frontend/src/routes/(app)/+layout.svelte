<script lang="ts">
	import {onMount} from "svelte"
	import {goto} from "$app/navigation"

	import Toast from "$lib/toast.svelte"

	let user = $state(null)
	let checked = $state(false)

	onMount(async () => {
		const response = await fetch("/api/user")
		if (response.status === 401) {
			goto(`/login?next=${encodeURIComponent(window.location.pathname)}`)	
			return 
		}

		user = await response.json()
		checked = true
	})

	let { children } = $props();
</script>


<Toast />

<svelte:head>
	<link rel="icon"/>
</svelte:head>

{#if checked}
	{@render children()}
{/if}

<style>
	@import "../../style.css";
</style>