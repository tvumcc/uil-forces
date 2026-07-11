<script lang="ts">
	import {onMount} from "svelte"
	import {goto} from "$app/navigation"
	import type { User } from "$lib/utils"

	import MenuBar from "$lib/menuBar.svelte"
	import Toast from "$lib/toast.svelte"

	let user: User | null = $state(null)
	let checked = $state(false)

	onMount(async () => {
		const response = await fetch("/api/user")
		if (response.status === 401) {
			goto(`/login?next=${encodeURIComponent(window.location.toString())}`)	
			return 
		}

		const data = await response.json()

		user = data.user
		checked = true
	})

	let { children } = $props();
</script>


<Toast />

<svelte:head>
	<link rel="icon"/>
</svelte:head>

{#if checked}
	<MenuBar user={user!}/>
	{@render children()}
{/if}

<style>
	@import "../../style.css";
</style>