<script lang="ts">
    import { onMount } from "svelte";
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { csrfFetch, type ProblemSet } from "$lib/utils"

    let psets: ProblemSet[] = $state([])
    let loading = $state(true)
    let name: string = $state("")

    async function getData() {
        const response: Response = await fetch("/api/admin/psets")
        if (!response.ok) {
            await addErrorToast(response, "Failed to load problem set list")
            goBack()
            return
        }
        const data = await response.json()
        psets = data.psets
        loading = false
    }

    async function addPset(event: Event) {
        event.preventDefault()
        const response: Response = await csrfFetch("/api/admin/pset/add", "POST", {
            name: name
        })
        if (response.ok) {
            await getData()
            addToast(`Created new problem set ${name}`, ToastType.Success)
            name = ""
        } else {
            await addErrorToast(response, `Failed to create problem set ${name}`)
        }
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    <header class="hero">
        <h1>Problem Sets</h1>
    </header>

    {#if loading}
        <div class="panel skeleton"></div>
    {:else}
        <section class="panel">
            <h2 class="section-header">All Problem Sets</h2>
            {#if psets.length > 0}
                <ul class="pset-list">
                    {#each psets as pset}
                        <li>
                            <a href="/admin/pset?id={pset.id}">{pset.name}</a>
                            {#if pset.problems}
                                <span class="count">{pset.problems.length} problem{pset.problems.length === 1 ? "" : "s"}</span>
                            {/if}
                        </li>
                    {/each}
                </ul>
            {:else}
                <p class="empty-state">No problem sets created yet.</p>
            {/if}
        </section>

        <section class="panel spaced">
            <h2 class="section-header">Create New Problem Set</h2>
            <form class="stacked-form" onsubmit={addPset}>
                <div class="field">
                    <label for="name">Name</label>
                    <input name="name" type="text" bind:value={name}>
                </div>
                <button type="submit" class="btn btn-primary">Create Problem Set</button>
            </form>
        </section>
    {/if}
</div>

<style>
    .pset-list {
        list-style: none;
        margin: 0;
        padding: 0;
    }
    .pset-list li {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 9px 0;
        border-bottom: 1px solid #131d2e;
    }
    .pset-list li:last-child {
        border-bottom: none;
    }
    .count {
        font-size: 12px;
        color: #64748b;
    }
</style>