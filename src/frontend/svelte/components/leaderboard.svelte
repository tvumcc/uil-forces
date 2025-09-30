<script lang="ts">
    import { onMount } from "svelte";

    let {ID, problems} = $props()
    let leaderboard = $state([])

    export async function getData() {
        let response: Response = await fetch(`/api/contest/${ID}/leaderboard`)
        let json = await response.json()
        leaderboard = json["leaderboard"]
        console.log("hello")
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
</style>

<table>
    <thead>
        <tr>
            <th>User</th>
            <th>Score</th>
            {#each problems as problem, i}
                <th title="{problem.name}">{i+1}</th>
            {/each}
        </tr>
    </thead>
    <tbody>
        {#each leaderboard as leaderboardEntry, i}
            <tr>
                <td>{leaderboardEntry["user"]["username"]}</td>
                <td>{leaderboardEntry["score"]}</td>
                {#each (leaderboardEntry["problems_solved"] as Array<Number>) as problem_status}
                    {#if problem_status === 1}
                        <td style="background:green;">AC</td>
                    {:else if problem_status === 2}
                        <td style="background:red;">WA</td>
                    {:else}
                        <td></td>
                    {/if}
                {/each}
            </tr>
        {/each}
    </tbody>
</table>