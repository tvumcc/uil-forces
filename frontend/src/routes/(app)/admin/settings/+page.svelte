<script lang="ts">
    import { onMount } from "svelte";
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { csrfFetch, type Settings } from "$lib/utils"

    let settings: Settings | undefined = $state()
    let loading = $state(true)

    async function getData() {
        const response: Response = await fetch(`/api/admin/settings`)
        if (!response.ok) {
            await addErrorToast(response, "Failed to retrieve settings")
            goBack()
            return
        }
        const data = await response.json()
        settings = data.settings
        loading = false
    }

    async function editSettings(event: Event) {
        event.preventDefault()
        const response: Response = await csrfFetch("/api/admin/settings/update", "POST", {
            docker_grading: settings!.docker_grading
        })
        if (response.ok) {
            await getData()
            addToast("Updated settings", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to update settings")
        }
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    <header class="hero">
        <h1>Settings</h1>
    </header>

    {#if loading}
        <div class="panel skeleton"></div>
    {:else if settings !== undefined}
        <section class="panel">
            <h2 class="section-header">Grading</h2>
            <form class="stacked-form" onsubmit={editSettings}>
                <div class="checkbox-row">
                    <label class="checkbox-field">
                        <input name="docker-grading" type="checkbox" bind:checked={settings.docker_grading}>
                        Use Docker Grading
                    </label>
                    <p class="dim" style="margin: 0;padding-left: 30px;">Note: Docker grading is more secure but only works if the Docker daemon is installed, the correct images are installed, and the server computer has administrator/root privileges. For school computer usage, Docker grading should be DISABLED.</p>
                </div>
                <button type="submit" class="btn btn-primary">Update Settings</button>
            </form>
        </section>
    {/if}
</div>