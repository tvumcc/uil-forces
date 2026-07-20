<script lang="ts">
    import { onMount } from "svelte"
    import type {LeaderboardEntry} from "$lib/utils"
    import { addErrorToast } from "./toastStore.svelte";

    let {ID, problems} = $props()
    let leaderboard: LeaderboardEntry[] = $state([])
    let loading = $state(true)

    export async function getData() {
        const response: Response = await fetch(`/api/contest/${ID}/leaderboard`)
        if (!response.ok) {
            await addErrorToast(response, "Failed to load contest leaderboard")
            return
        }
        const data = await response.json()
        leaderboard = data.leaderboard
        loading = false
    }

    onMount(getData)
</script>

{#if loading}
    <div class="skeleton"></div>
{:else if leaderboard.length === 0}
    <p class="empty-state">No scores to show yet.</p>
{:else}
    <table class="scoreboard">
        <thead>
            <tr>
                <th class="rank-col sticky">rank</th>
                <th class="user-col sticky">user</th>
                <th class="score-col sticky">score</th>
                {#each problems as problem, i}
                    <th class="problem-col" title="{problem.name}">{String.fromCharCode(65 + i)}</th>
                {/each}
            </tr>
        </thead>
        <tbody>
            {#each leaderboard as entry, i}
                <tr class:top-three={i < 3}>
                    <td class="rank-col sticky">
                        <span class="rank rank-{i}">{String(i + 1).padStart(2, "0")}</span>
                    </td>
                    <td class="user-col sticky">{entry.user.username}</td>
                    <td class="score-col sticky mono">{entry.score}</td>
                    {#each entry.problemsSolved as problemStatus}
                        {#if problemStatus[1] > 0}
                            <td class="cell cell-solved mono">
                                {Math.min(1, problemStatus[1]) * (problemStatus[3] - problemStatus[2] * problemStatus[4])}
                            </td>
                        {:else if problemStatus[2] > 0}
                            <td class="cell cell-wrong mono">-{problemStatus[2]}</td>
                        {:else}
                            <td class="cell cell-empty">–</td>
                        {/if}
                    {/each}
                </tr>
            {/each}
        </tbody>
    </table>
{/if}

<style>
    .scoreboard {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        white-space: nowrap;
    }

    th {
        color: #64748b;
        font-weight: normal;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-align: center;
        padding: 8px 10px;
        border-bottom: 1px solid #1e293b;
    }

    td {
        padding: 8px 10px;
        text-align: center;
        border-bottom: 1px solid #131d2e;
    }

    .rank-col { width: 44px; }
    .user-col { text-align: left; min-width: 120px; }
    .score-col { width: 60px; }

    /* Sticky rank/user/score so they stay visible while scrolling through problem columns */
    .sticky {
        position: sticky;
        background-color: #0b1220;
        z-index: 1;
    }
    .rank-col.sticky { left: 0; }
    .user-col.sticky { left: 44px; }
    .score-col.sticky { left: 164px; box-shadow: 2px 0 0 #1e293b; }

    tr.top-three .sticky {
        background-color: #101c30;
    }

    .rank {
        color: #64748b;
    }
    .top-three .rank-0 { color: #f5c451; }
    .top-three .rank-1 { color: #cbd5e1; }
    .top-three .rank-2 { color: #d08a5a; }
    tr.top-three .user-col {
        color: white;
        font-weight: bold;
    }


    .cell {
        min-width: 44px;
    }
    .cell-solved {
        background-color: rgba(0, 212, 146, 0.15);
        color: #00d492;
        font-weight: bold;
    }
    .cell-wrong {
        background-color: rgba(248, 113, 113, 0.12);
        color: #f87171;
    }
    .cell-empty {
        color: #334155;
    }

    .empty-state {
        color: #64748b;
        font-size: 14px;
        margin: 0;
        padding: 10px 0;
    }

    .skeleton {
        min-height: 100px;
        border-radius: 6px;
        background: linear-gradient(90deg, #0b1220 0%, #131d2e 50%, #0b1220 100%);
        background-size: 200% 100%;
        animation: shimmer 1.4s ease-in-out infinite;
    }
    @media (prefers-reduced-motion: reduce) {
        .skeleton { animation: none; }
    }
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
</style>