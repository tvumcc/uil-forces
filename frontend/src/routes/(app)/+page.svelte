<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { addErrorToast } from "$lib/toastStore.svelte";
    import type { Contest, User } from "$lib/utils"

    let ongoingContests: Contest[] = $state([])
    let upcomingContests: Contest[] = $state([])
    let userLeaderboard: [User, number][] = $state([])
    let loading = $state(true)

    let now = $state(Date.now())
    let clockInterval: ReturnType<typeof setInterval>;
    let refetchedOnExpiry = new Set<number>();

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
        if (!leaderboardResponse.ok) {
            await addErrorToast(leaderboardResponse, "Failed to load leaderboard")
        } else {
            const leaderboardData = await leaderboardResponse.json()
            userLeaderboard = leaderboardData.map((entry: any) => [entry.user, entry.problemsSolved])
        }

        loading = false
    }

    function msRemaining(targetIso: string): number {
        return new Date(targetIso).getTime() - now
    }

    function formatDuration(ms: number): string {
        if (ms <= 0) return "00:00:00"
        const totalSeconds = Math.floor(ms / 1000)
        const days = Math.floor(totalSeconds / 86400)
        const hours = Math.floor((totalSeconds % 86400) / 3600)
        const minutes = Math.floor((totalSeconds % 3600) / 60)
        const seconds = totalSeconds % 60
        const clock = [hours, minutes, seconds].map(n => String(n).padStart(2, "0")).join(":")
        return days > 0 ? `${days}d ${clock}` : clock
    }

    function handleExpiry(contest: Contest) {
        if (refetchedOnExpiry.has(contest.id)) return
        refetchedOnExpiry.add(contest.id)
        getData() // pick up the real status transition (upcoming->ongoing, ongoing->ended) from the server
    }

    onMount(() => {
        getData()
        clockInterval = setInterval(() => { now = Date.now() }, 1000)
    })

    onDestroy(() => {
        if (clockInterval) clearInterval(clockInterval)
    })
</script>

<div class="main-container">
    <header class="hero">
        <h1>UIL Forces</h1>
        <p class="subtitle">A platform for UIL Computer Science programming contests</p>
        <p class="subtitle">
            <a href="https://github.com/tvumcc/uil-forces">GitHub</a>
            <span class="dim">— report bugs/issues or contribute to development</span>
        </p>
    </header>

    {#if loading}
        <div class="panel-grid">
            <section class="panel skeleton"></section>
            <section class="panel skeleton"></section>
        </div>
    {:else}
        <div class="panel-grid">
            <section class="panel">
                <h2 class="section-header">Ongoing Contests</h2>
                {#if ongoingContests.length === 0}
                    <p class="empty-state">Nothing running right now.</p>
                {:else}
                    <ul class="contest-list">
                        {#each ongoingContests as contest}
                            {@const remaining = msRemaining(contest.endTime)}
                            {#if remaining <= 0}{handleExpiry(contest)}{/if}
                            <li>
                                <div class="contest-row">
                                    <a href="/contest?id={contest.id}">{contest.name}</a>
                                </div>
                                <p class="countdown">ends in <span class="mono-time">{formatDuration(remaining)}</span></p>
                            </li>
                        {/each}
                    </ul>
                {/if}
                

                <h2 class="section-header spaced">Upcoming Contests</h2>
                {#if upcomingContests.length === 0}
                    <p class="empty-state">Nothing scheduled yet.</p>
                {:else}
                    <ul class="contest-list">
                        {#each upcomingContests as contest}
                            {@const remaining = msRemaining(contest.startTime)}
                            {#if remaining <= 0}{handleExpiry(contest)}{/if}
                            <li>
                                <div class="contest-row">
                                    <a href="/contest?id={contest.id}">{contest.name}</a>
                                </div>
                                <p class="countdown">starts in <span class="mono-time">{formatDuration(remaining)}</span></p>
                            </li>
                        {/each}
                    </ul>
                {/if}
            </section>

            <section class="panel">
                <h2 class="section-header">Leaderboard</h2>
                {#if userLeaderboard.length === 0}
                    <p class="empty-state">No submissions graded yet. Be the first.</p>
                {:else}
                    <table class="leaderboard">
                        <thead>
                            <tr>
                                <th class="rank-col"></th>
                                <th>User</th>
                                <th class="num-col">Solved</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#each userLeaderboard as [user, solved], i}
                                <tr class:top-three={i < 3}>
                                    <td class="rank-col">
                                        <span class="rank rank-{i}">{String(i + 1).padStart(2, "0")}</span>
                                    </td>
                                    <td>{user.username}</td>
                                    <td class="num-col">{solved}</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                {/if}
            </section>
        </div>
    {/if}
</div>

<style>
    .leaderboard {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }
    .leaderboard th {
        text-align: left;
        color: #64748b;
        font-weight: normal;
        font-size: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #1e293b;
        text-transform: uppercase;
    }
    .leaderboard td {
        padding: 7px 0;
        border-bottom: 1px solid #131d2e;
    }
    .num-col { text-align: right; }
    .rank-col { width: 40px; }
    .rank {
        color: #64748b;
    }
    .top-three .rank-0 { color: #f5c451; } /* gold */
    .top-three .rank-1 { color: #cbd5e1; } /* silver */
    .top-three .rank-2 { color: #d08a5a; } /* bronze */
    tr.top-three td:nth-child(2) {
        color: white;
        font-weight: bold;
    }
</style>