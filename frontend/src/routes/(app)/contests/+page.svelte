<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { addErrorToast } from "$lib/toastStore.svelte";
    import { goto } from "$app/navigation";
    import type { Contest } from "$lib/utils"

    let pastContests: Contest[] = $state([])
    let ongoingContests: Contest[] = $state([])
    let upcomingContests: Contest[] = $state([])
    let loading = $state(true)
    let now = $state(Date.now())

    let clockInterval: ReturnType<typeof setInterval>;
    let refetchedOnExpiry = new Set<number>();

    async function getData() {
        const response: Response = await fetch("/api/contests")
        if (!response.ok) {
            await addErrorToast(response, "Failed to load contests")
            goto("/")
            return
        }
        const data = await response.json()
        pastContests = data.past
        ongoingContests = data.ongoing
        upcomingContests = data.upcoming
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

    function formatDate(iso: string): string {
        return new Date(iso).toLocaleDateString(undefined, {
            year: "numeric", month: "short", day: "numeric", hour: "numeric", minute: "numeric"
        })
    }

    function handleExpiry(contest: Contest) {
        if (refetchedOnExpiry.has(contest.id)) return
        refetchedOnExpiry.add(contest.id)
        getData()
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
        <h1>Contests</h1>
        <p class="subtitle">Live, upcoming, and past contests</p>
    </header>

    {#if loading}
        <div class="panel skeleton"></div>
    {:else if ongoingContests.length + upcomingContests.length + pastContests.length === 0}
        <div class="panel">
            <p class="empty-state">No contests have been created yet.</p>
        </div>
    {:else}
        {#if ongoingContests.length > 0}
            <section class="panel">
                <h2 class="section-header">Ongoing</h2>
                <ul class="contest-list">
                    {#each ongoingContests as contest}
                        {@const remaining = msRemaining(contest.endTime)}
                        {#if remaining <= 0}{handleExpiry(contest)}{/if}
                        <li>
                            <div class="contest-row">
                                <a href="/contest?id={contest.id}">{contest.name}</a>
                            </div>
                            <p class="meta">ends in <span class="mono-time">{formatDuration(remaining)}</span></p>
                        </li>
                    {/each}
                </ul>
            </section>
        {/if}

        {#if upcomingContests.length > 0}
            <section class="panel spaced">
                <h2 class="section-header">Upcoming</h2>
                <ul class="contest-list">
                    {#each upcomingContests as contest}
                        {@const remaining = msRemaining(contest.startTime)}
                        {#if remaining <= 0}{handleExpiry(contest)}{/if}
                        <li>
                            <div class="contest-row">
                                <a href="/contest?id={contest.id}">{contest.name}</a>
                            </div>
                            <p class="meta">starts in <span class="mono-time">{formatDuration(remaining)}</span></p>
                        </li>
                    {/each}
                </ul>
            </section>
        {/if}

        {#if pastContests.length > 0}
            <section class="panel spaced">
                <h2 class="section-header">Past</h2>
                <ul class="contest-list">
                    {#each pastContests as contest}
                        <li>
                            <div class="contest-row">
                                <a href="/contest?id={contest.id}">{contest.name}</a>
                            </div>
                            <p class="meta">{formatDate(contest.startTime)} – {formatDate(contest.endTime)}</p>
                        </li>
                    {/each}
                </ul>
            </section>
        {/if}
    {/if}
</div>

<style>
    .contest-list li {
        display: block;
    }
    .contest-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .meta {
        margin: 4px 0 0 0;
        font-size: 12px;
        color: #64748b;
    }
    .mono-time {
        color: #cbd5e1;
        font-variant-numeric: tabular-nums;
    }
</style>