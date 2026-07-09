<script lang="ts">
    import MenuBar from "$lib/menuBar.svelte"
    import {getTzOffset, type Contest} from "$lib/utils"

    let validRequest = $state(true)
    let message = $state("")

    let contests: Contest[] = $state([]) 

    // state for add contest section
    let name = $state()
    let startTime: Date = $state(new Date())
    let endTime: Date = $state(new Date())

    async function getData() {
        let response: Response = await fetch("/api/admin/contests")
        let json = await response.json()
        
        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        contests = json.contests
    }

    async function addContest(event: Event) {
        event.preventDefault()

        let response = await fetch("/api/admin/add/contest", {
            method: "POST",
            body: JSON.stringify({
                name: name,
                startTime: new Date(startTime + getTzOffset()).toISOString(),
                endTime: new Date(endTime + getTzOffset()).toISOString() 
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }
</script>

<MenuBar />
<div class="main-container">
    <h1>Contests</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if validRequest}
            {#each contests as contest}
                <a href="/admin/contest?id={contest.id}">{contest.name}</a>
                <br>
            {/each}

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
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>
