<script lang="ts">
    import MenuBar from "../components/menuBar.svelte"

    let ongoingContests = $state([])
    let upcomingContests = $state([])

    async function getData() {
        let response: Response = await fetch("/api/contests")
        let json = await response.json()
        ongoingContests = json.ongoing
        upcomingContests = json.upcoming
    }
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Home</h1>

    {#await getData()}
        <p>Loading...</p>
    {:then} 
        {#if ongoingContests.length > 0}
            <h2>Ongoing Contests</h2>
            {#each ongoingContests as contest}
                <a href="/contest?id={contest["id"]}">{contest["name"]}</a><br>
            {/each}
        {/if}

        {#if upcomingContests.length > 0}
            <h2>Upcoming Contests</h2>
            {#each upcomingContests as contest}
                <a href="/contest?id={contest["id"]}">{contest["name"]}</a><br>
            {/each}
        {/if}
    {/await}
</div>