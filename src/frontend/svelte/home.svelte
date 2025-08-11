<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "./components/menubar.svelte"

    let ongoing_contests = $state([])
    let upcoming_contests = $state([])

    async function getData() {
        let response: Response = await fetch("/api/contests")
        let json = await response.json()
        ongoing_contests = json["ongoing"]
        upcoming_contests = json["upcoming"]
    }

    onMount(getData)
</script>

<style>
    @import "../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Home Page</h1>

    <a href="/contests">All Contests</a><br>

    {#if ongoing_contests.length > 0}
        <h2>Ongoing Contests</h2>
        {#each ongoing_contests as contest}
            <a href="/contest?id={contest["id"]}">{contest["name"]}</a>
        {/each}
    {/if}

    {#if upcoming_contests.length > 0}
        <h2>Upcoming Contests</h2>
        {#each upcoming_contests as contest}
            <a href="/contest?id={contest["id"]}">{contest["name"]}</a>
        {/each}
    {/if}
</div>