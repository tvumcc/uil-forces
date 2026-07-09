<script lang="ts">
    import MenuBar from "$lib/menuBar.svelte"
    import type {Contest} from "$lib/utils"

    let validRequest = $state(true)
    let message = $state("")

    let pastContests: Contest[] = $state([])
    let ongoingContests: Contest[] = $state([])
    let upcomingContests: Contest[] = $state([])

    async function getData() {
        let response: Response = await fetch("/api/contests")
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        pastContests = json.past
        ongoingContests = json.ongoing
        upcomingContests = json.upcoming
    }
</script>

<MenuBar />
<div class="main-container">
    <h1>Contests</h1>

    {#await getData()}
        <p>Loading...</p>
    {:then}
        {#if validRequest}
            {#if ongoingContests.length + upcomingContests.length + pastContests.length === 0}
                <p>There are no contests to display</p>
            {/if}

            {#if ongoingContests.length > 0}
                <h2>Ongoing Contests</h2>
                {#each ongoingContests as contest}
                    <a href="/contest?id={contest.id}">{contest.name}</a><br>
                {/each}
            {/if}

            {#if upcomingContests.length > 0}
                <h2>Upcoming Contests</h2>
                {#each upcomingContests as contest}
                    <a href="/contest?id={contest.id}">{contest.name}</a><br>
                {/each}
            {/if}

            {#if pastContests.length > 0}
                <h2>Past Contests</h2>
                {#each pastContests as contest}
                    <a href="/contest?id={contest.id}">{contest.name}</a><br>
                {/each}
            {/if}
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>