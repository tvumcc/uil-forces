<script lang="ts">
    import { onMount } from "svelte";
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { csrfFetch, getTzOffset, toTzIsoString, type Contest } from "$lib/utils"

    let contests: Contest[] | undefined = $state([])
    let loading = $state(true)

    let name = $state("")
    let startTime: string = $state(toTzIsoString(new Date()))
    let endTime: string = $state(toTzIsoString(new Date()))

    async function getData() {
        const response: Response = await fetch("/api/admin/contests")

        if (!response.ok) {
            await addErrorToast(response, "Failed to load contest list")
            goBack()
            return
        }
        const data = await response.json()
        contests = data.contests
        loading = false
    }

    async function addContest(event: Event) {
        event.preventDefault()

        let newStartTime
        let newEndTime
        try {
            newStartTime = new Date(startTime + getTzOffset()).toISOString()
            newEndTime = new Date(endTime + getTzOffset()).toISOString()
        } catch {
            addToast("Failed to create contest: invalid date(s)", ToastType.Error)
            return
        }

        const response: Response = await csrfFetch("/api/admin/contest/add", "POST", {
            name: name,
            startTime: newStartTime,
            endTime: newEndTime
        })

        if (response.ok) {
            await getData()
            addToast(`Created contest ${name}`, ToastType.Success)
            name = ""
        } else {
            await addErrorToast(response, `Failed to create contest ${name}`)
        }
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    <header class="hero">
        <h1>Contests</h1>
    </header>

    {#if loading}
        <div class="panel skeleton"></div>
    {:else}
        <section class="panel">
            <h2 class="section-header">All Contests</h2>
            {#if contests !== undefined && contests.length > 0}
                <ul class="contest-list">
                    {#each contests as contest}
                        <li>
                            <a href="/admin/contest?id={contest.id}">{contest.name}</a>
                            <span class="badge badge-{contest.status}">{contest.status}</span>
                        </li>
                    {/each}
                </ul>
            {:else}
                <p class="empty-state">No contests created yet.</p>
            {/if}
        </section>

        <section class="panel spaced">
            <h2 class="section-header">Create New Contest</h2>
            <form class="stacked-form" onsubmit={addContest}>
                <div class="field">
                    <label for="name">Name</label>
                    <input name="name" type="text" bind:value={name}>
                </div>
                <div class="field">
                    <label for="start-time">Start Time</label>
                    <input name="start-time" type="datetime-local" bind:value={startTime}>
                </div>
                <div class="field">
                    <label for="end-time">End Time</label>
                    <input name="end-time" type="datetime-local" bind:value={endTime}>
                </div>
                <button type="submit" class="btn btn-primary">Create Contest</button>
            </form>
        </section>
    {/if}
</div>

<style>
    .badge {
        font-size: 11px;
        padding: 2px 10px;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-ongoing {
        background-color: rgba(0, 212, 146, 0.15);
        color: #00d492;
    }
    .badge-upcoming {
        background-color: rgba(245, 196, 81, 0.15);
        color: #f5c451;
    }
    .badge-past {
        background-color: rgba(100, 116, 139, 0.15);
        color: #64748b;
    }
</style>