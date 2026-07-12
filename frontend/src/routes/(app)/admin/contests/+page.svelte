<script lang="ts">
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addToast, ToastType } from "$lib/toastStore.svelte";

    import {csrfFetch, getTzOffset, type Contest} from "$lib/utils"

    let contests: Contest[] | undefined = $state([]) 

    // state for add contest section
    let name = $state()
    let startTime: Date = $state(new Date())
    let endTime: Date = $state(new Date())

    async function getData() {
        const response: Response = await fetch("/api/admin/contests")
        const data = await response.json()
        
        if (!response.ok) {
            addToast("Failed to load contest list", ToastType.Error)
            return
        }

        contests = data.contests
    }

    async function addContest(event: Event) {
        event.preventDefault()

        const response = await csrfFetch("/api/admin/add/contest", "POST", JSON.stringify({
            name: name,
            startTime: new Date(startTime + getTzOffset()).toISOString(),
            endTime: new Date(endTime + getTzOffset()).toISOString() 
        }))

        if (response.ok) {
            await getData()
            addToast(`Created contest ${name}`, ToastType.Success)
        } else {
            addToast(`Failed to create contest ${name}`, ToastType.Error)
        }
    }
</script>

<div class="main-container">
    <h1>Contests</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if contests !== undefined}
            {#each contests as contest}
                <a href="/admin/contest?id={contest.id}">{contest.name}</a>
                <br>
            {/each}
        {/if}
        
        <h2>Add Contest</h2>
        <form onsubmit={addContest}>
            <label for="name">Name</label>
            <input name="name" type="text" bind:value={name}>
            <label for="start-time">Start Time</label>
            <input name="start-time" type="datetime-local" bind:value={startTime}>
            <label for="end-time">End Time</label>
            <input name="end-time" type="datetime-local" bind:value={endTime}>
            <input type="submit" value="Add Contest">
        </form>
    {/await}
</div>