<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "./components/menubar.svelte"

    let pastContests = $state([])
    let ongoingContests = $state([])
    let upcomingContests = $state([])

    async function getData() {
        let response: Response = await fetch("/api/contests")
        let json = await response.json()
        pastContests = json["past"]
        ongoingContests = json["ongoing"]
        upcomingContests = json["upcoming"]
    }

    onMount(getData)
</script>

<style>
    @import "../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Contests</h1>

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

    {#if pastContests.length > 0}
        <h2>Past Contests</h2>
        {#each pastContests as contest}
            <a href="/contest?id={contest["id"]}">{contest["name"]}</a><br>
        {/each}
    {/if}
</div>