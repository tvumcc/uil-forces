<script lang="ts">
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { goBack } from "$lib/navigationHistory.svelte";

    import type {Contest} from "$lib/utils"

    import SubmitForm from "$lib/submitForm.svelte"
    import SubmissionTable from "$lib/submissionTable.svelte"
    import Leaderboard from "$lib/leaderboard.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let contest: Contest | undefined = $state()
    let leaderboard: Leaderboard | undefined = $state()
    let submissionProblemID = $state(-1)


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
    }
</script>

<div class="main-container" style="flex: 0 0 auto;">
    {#await getData()}
            <p>Loading...</p>
    {:then}
        {#if contest !== undefined}
            <h1>{contest.name}</h1>
            <a href="/api/contest/{ID}/data" target="_blank">Download Student Data</a>
            {#if contest.status === "upcoming"}
                <p>The contest has not started yet. You cannot submit solutions.</p>
            {:else}
                {#if contest.status === "past"}
                    <p>The contest has ended. You can still view submissions and the leaderboard, but you cannot submit solutions.</p>
                {:else}
                    <h2>Submit Code</h2>
                    <SubmitForm submissionType={"contest"} ID={ID!} problems={contest.problems!} allowedLanguages={contest.allowedLanguages!.split(" ")} reloadSubmissions={getData} {reloadLeaderboard} bind:submissionProblemID/>
                {/if}

                {#if contest!.showPdf && contest!.status === "ongoing" && submissionProblemID !== -1}
                    <div id="pdf-viewer">
                        <embed type="application/pdf" src={`/api/problem/${submissionProblemID}/pdf#toolbar=0&navpanes=0`} width="100%" height="100%">
                    </div>
                {/if}

                {#if contest.showLeaderboard}
                    <h2>Leaderboard</h2>
                    <div class="lb" style="width: 100%; overflow-x: scroll;">
                        <Leaderboard {ID} problems={contest.problems} bind:this={leaderboard}/>            
                    </div>
                    <br>
                {/if}

                {#if contest.status === "past"}
                    <h2>All Submissions</h2>
                    <SubmissionTable submissions={contest.submissions} showUsers={true}/>
                {:else}
                    <h2>Your Submissions</h2>
                    <SubmissionTable submissions={contest.submissions} showUsers={false}/>
                {/if}
            {/if}
        {/if}
    {/await}
</div>

<style>
    #pdf-viewer {
        background-color: #101828;
        height: 100vh;
        display: flex;
        flex: 1;
        justify-content: center;
        align-items: center;
        text-align: center;
    }

    .lb::-webkit-scrollbar {
        display: none;
    }
    .lb {
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
</style>