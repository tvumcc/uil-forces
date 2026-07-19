<script lang="ts">
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";

    import {csrfFetch, getTzOffset, type Contest} from "$lib/utils"

    let contests: Contest[] | undefined = $state([]) 

    let name = $state()
    let startTime: Date = $state(new Date())
    let endTime: Date = $state(new Date())

    async function getData() {
        const response: Response = await fetch("/api/admin/contests")
        
        if (!response.ok) {
            await addErrorToast(response, "Failed to load contest list")
            goBack()
            return
        }

        const data = await response.json()
        contests = data.contests
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
        } else {
            await addErrorToast(response, `Failed to create contest ${name}`)
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