<script lang="ts">
    import { addErrorToast } from "$lib/toastStore.svelte";
    import type { Contest, User } from "$lib/utils"

    let ongoingContests: Contest[] = $state([])
    let upcomingContests: Contest[] = $state([])
    let userLeaderboard: [User, number][] = $state([])

    async function getData() {
        const response: Response = await fetch("/api/contests")

        if (!response.ok) {
            await addErrorToast(response, "Failed to load contests")
        } else {
            const data = await response.json()
            ongoingContests = data.ongoing
            upcomingContests = data.upcoming
        }


        const leaderboardResponse: Response = await fetch("/api/users/leaderboard")

        if (!response.ok) {
            await addErrorToast(response, "Failed to load leaderboard")
        } else {
            const leaderboardData = await leaderboardResponse.json()
            for (let i = 0; i < leaderboardData.length; i++)
                userLeaderboard.push([leaderboardData[i].user, leaderboardData[i].problemsSolved])
        }
    }
</script>

<div class="main-container">
    <h1>Home</h1>

    <p>Welcome to UIL Forces Beta!</p>
    <p>Visit the <a href="https://github.com/tvumcc/uil-forces">GitHub repository</a> to report bugs and contribute to development.</p>

    {#await getData()}
        <p>Loading...</p>
    {:then} 
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
    {/await}
</div>