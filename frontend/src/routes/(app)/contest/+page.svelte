<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/state";
    import { addErrorToast } from "$lib/toastStore.svelte";
    import { goBack } from "$lib/navigationHistory.svelte";
    import type { Contest } from "$lib/utils"
    import SubmitForm from "$lib/submitForm.svelte"
    import SubmissionTable from "$lib/submissionTable.svelte"
    import LeaderboardComponent from "$lib/leaderboard.svelte"

    let ID = page.url.searchParams.get("id")
    let contest: Contest | undefined = $state()
    let leaderboard: LeaderboardComponent | undefined = $state()
    let submissionProblemID = $state(-1)
    let loading = $state(true)

    async function reloadLeaderboard() {
        await leaderboard!.getData()
    }

    async function getData() {
        const response: Response = await fetch(`/api/contest/${ID}`)
        if (!response.ok) {
            await addErrorToast(response, "Failed to load contest page")
            goBack()
            return
        }
        const data = await response.json()
        contest = data.contest
        loading = false
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    {#if loading}
        <div class="panel skeleton"></div>
    {:else if contest !== undefined}
        <header class="hero">
            <div class="title-row">
                <h1>{contest.name}</h1>
            </div>
            <a class="download-link" href="/api/contest/{ID}/data" target="_blank">Download Student Data Files</a>
        </header>

        {#if contest.status === "upcoming"}
            <div class="panel">
                <p class="notice">This contest hasn't started yet — submissions open once it goes live.</p>
            </div>
        {:else}
            {#if contest.status === "past"}
                <div class="panel">
                    <p class="notice">This contest has ended. You can still review submissions and the leaderboard.</p>
                </div>
            {:else}
                <section class="panel spaced">
                    <h2 class="section-header">Submit</h2>
                    <SubmitForm
                        submissionType={"contest"}
                        ID={ID!}
                        problems={contest.problems!}
                        allowedLanguages={contest.allowedLanguages!.split(" ")}
                        reloadSubmissions={getData}
                        {reloadLeaderboard}
                        bind:submissionProblemID
                    />
                </section>
            {/if}

            {#if contest.showPdf && contest.status === "ongoing" && submissionProblemID !== -1}
                <section class="panel spaced pdf-panel">
                    <embed
                        type="application/pdf"
                        src={`/api/problem/${submissionProblemID}/pdf#toolbar=0&navpanes=0`}
                        class="pdf-embed"
                    >
                </section>
            {/if}

            {#if contest.showLeaderboard}
                <section class="panel spaced">
                    <h2 class="section-header">Leaderboard</h2>
                    <div class="scroll-x">
                        <LeaderboardComponent {ID} problems={contest.problems} bind:this={leaderboard} />
                    </div>
                </section>
            {/if}

            <section class="panel spaced">
                {#if contest.status === "past"}
                    <h2 class="section-header">All Submissions</h2>
                    <SubmissionTable submissions={contest.submissions} showUsers={true} />
                {:else}
                    <h2 class="section-header">Your Submissions</h2>
                    <SubmissionTable submissions={contest.submissions} showUsers={false} />
                {/if}
            </section>
        {/if}
    {/if}
</div>

<style>
    .title-row {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }
    .title-row h1 {
        font-size: 28px;
        letter-spacing: -0.5px;
    }
    .download-link {
        display: inline-block;
        margin-top: 8px;
        font-size: 13px;
    }

    .notice {
        color: #94a3b8;
        margin: 0;
        font-size: 14px;
    }

    .pdf-panel {
        padding: 0;
        overflow: hidden;
        height: 80vh;
    }
    .pdf-embed {
        width: 100%;
        height: 100%;
        display: block;
        border: none;
    }

    .scroll-x {
        width: 100%;
        overflow-x: scroll;
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    .scroll-x::-webkit-scrollbar {
        display: none;
    }
</style>