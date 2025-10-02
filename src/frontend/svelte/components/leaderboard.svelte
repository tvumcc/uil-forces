<script lang="ts">
    import { onMount } from "svelte";

    let {ID, problems} = $props()
    let leaderboard = $state([])

    export async function getData() {
        let response: Response = await fetch(`/api/contest/${ID}/leaderboard`)
        let json = await response.json()
        leaderboard = json["leaderboard"]
    }

    onMount(() => {
        getData()
    })
</script>

<style>
    @import "../../style.css";

    table {
        width: 100%;
        margin: 0;
        border-collapse: collapse;
    }

    td {
        border: 1px gray solid;
        margin: 0;
        padding: 8px;
        text-align: center;
    }

    .answerbox {
        min-width: 0.5em;
    }
</style>

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
                <td>{leaderboardEntry["user"]["username"]}</td>
                <td>{leaderboardEntry["score"]}</td>
                {#each (leaderboardEntry["problems_solved"] as Array<Array<number>>) as problem_status}
                    {#if problem_status[1] > 0}
                        <td class="answerbox " style="background:green;">{Math.min(1, problem_status[1]) * (problem_status[3] - problem_status[2] * problem_status[4])}</td>
                    {:else if problem_status[2] > 0}
                        <td class="answerbox " style="background:red;">-{problem_status[2]}</td>
                    {:else}
                        <td class="answerbox " style="color: transparent;">--</td>
                    {/if}
                {/each}
            </tr>
        {/each}
    </tbody>
</table>