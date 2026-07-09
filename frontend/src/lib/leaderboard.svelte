<script lang="ts">
    import { onMount } from "svelte"
    import type {LeaderboardEntry} from "$lib/utils"

    let {ID, problems} = $props()
    let leaderboard: LeaderboardEntry[] = $state([])

    export async function getData() {
        let response: Response = await fetch(`/api/contest/${ID}/leaderboard`)
        let json = await response.json()
        leaderboard = json.leaderboard
    }

    onMount(getData)
</script>

<table style="width: 100%;">
    <thead>
        <tr>
            <th>User</th>
            <th>Score</th>
            {#each problems as problem, i}
                <th title="{problem.name}">{i+1}</th>
            {/each}
        </tr>
    </thead>
    <tbody style="width: 100%; overflow-x: scroll;">
        {#each leaderboard as leaderboardEntry, i}
            <tr class="lb-row">
                <td>{leaderboardEntry.user.username}</td>
                <td>{leaderboardEntry.score}</td>
                {#each leaderboardEntry.problemsSolved as problemStatus}
                    {#if problemStatus[1] > 0}
                        <td class="answerbox " style="background:green;">{Math.min(1, problemStatus[1]) * (problemStatus[3] - problemStatus[2] * problemStatus[4])}</td>
                    {:else if problemStatus[2] > 0}
                        <td class="answerbox " style="background:red;">-{problemStatus[2]}</td>
                    {:else}
                        <td class="answerbox " style="color: transparent;">--</td>
                    {/if}
                {/each}
            </tr>
        {/each}
    </tbody>
</table>

<style>
    table {
        width: 100%;
        margin: 0;
        border-collapse: collapse;
    }

    td {
        border: 0px gray solid;
        margin: 0;
        padding: 8px;
        text-align: center;
    }

    .answerbox {
        min-width: 0.5em;
    }
</style>
