<script lang="ts">
    import { onMount } from "svelte";

    import type { Contest, User } from "$lib/utils"

    let loading = $state(true)

    let validRequest = $state(true)
    let message = $state("")

    let ongoingContests: Contest[] = $state([])
    let upcomingContests: Contest[] = $state([])
    let userLeaderboard: [User, number][] = $state([])

    async function getData() {
        let response: Response = await fetch("/api/contests")
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        ongoingContests = json.ongoing
        upcomingContests = json.upcoming

        let leaderboardResponse: Response = await fetch("/api/users/leaderboard")
        let leaderboardJson = await leaderboardResponse.json()

        for (let i = 0; i < leaderboardJson.length; i++) {
            userLeaderboard.push([leaderboardJson[i].user, leaderboardJson[i].problemsSolved])
        }

        loading = false
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    <h1>Home</h1>

    <p>Welcome to UIL Forces Beta!</p>
    <p>Visit the <a href="https://github.com/tvumcc/uil-forces">GitHub repository</a> to report bugs and contribute to development.</p>

    {#if loading}
        <p>Loading...</p>
    {:else if validRequest} 
        <h2>Leaderboard</h2>
        <table>
            <thead>
                <tr>
                    <th></th>
                    <th>User</th>
                    <th>Problems Solved</th>
                </tr>
            </thead>
            <tbody>
                {#each userLeaderboard as leaderboardEntry, i}
                    <tr>
                        <td>{i+1}.</td>
                        <td>{leaderboardEntry[0].username}</td>
                        <td>{leaderboardEntry[1]}</td>
                    </tr>
                {/each}
            </tbody>

        </table>

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
    {:else}
        <p>{message}</p>
    {/if}
</div>