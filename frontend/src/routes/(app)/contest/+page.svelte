<script lang="ts">
    import { addToast, ToastType } from "$lib/toastStore.svelte";
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

    $effect(() => {
        if (submissionProblemID !== -1 && contest!.showPdf) {
            document.getElementById("pdf-viewer")!.style.display = "flex"
        } else {
            document.getElementById("pdf-viewer")!.style.display = "none"
        }
    })

    async function reloadLeaderboard() {
        await leaderboard!.getData()
    }

    async function getData() {
        let response = await fetch(`/api/contest/${ID}`)
        let data = await response.json()

        if (!response.ok) {
            let error_message
            if (data.error === "not_found") {
                error_message = "Contest does not exist"
            } else {
                error_message = "Failed to load contest page"
            }

            addToast(error_message, ToastType.Error)
            goBack()
            return
        }

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
                <div id="pdf-viewer">
                    {#if submissionProblemID !== -1}
                        <embed type="application/pdf" src={`/api/problem/${submissionProblemID}/pdf#toolbar=0&navpanes=0`} width="100%" height="100%">
                    {:else}
                        <p>No Problem Selected</p>
                    {/if}
                </div>

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