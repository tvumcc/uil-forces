<script lang="ts">
    import SubmitForm from "../components/submitForm.svelte"
    import MenuBar from "../components/menuBar.svelte"
    import SubmissionTable from "../components/submissionTable.svelte"
    import Leaderboard from "../components/leaderboard.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let contestStatus = $state("")
    let contestName = $state("")
    let problems = $state([])
    let submissions = $state([])

    let leaderboard: Leaderboard

    let submissionProblemID = $state(-1)

    $effect(() => {
        if (submissionProblemID !== -1) {
            document.getElementById("pdf-viewer")!.style.display = "flex"
        } else {
            document.getElementById("pdf-viewer")!.style.display = "none"
        }
    })

    async function reloadSubmissions() {
        let response = await fetch(`/api/contest/${ID}`)
        let json = await response.json()
        submissions = json.submissions
    }

    async function reloadLeaderboard() {
        await leaderboard.getData()
    }

    async function getData() {
        let response = await fetch(`/api/contest/${ID}`)
        let json = await response.json()

        contestStatus = json.status
        contestName = json.name
        problems = json.problems
        submissions = json.submissions
    }
</script>

<style>
    @import "../../style.css";

    .horizontal-split {
        display: flex;
        /* grid-template-columns: 1fr 1fr; */
        width: 100%;
        height: 100%;

        overflow: hidden;
    }

    .submit-panel {
        margin: 0;
        display: flex;
        align-items: center;
        flex-direction: column;
        height: 100vh;
        overflow-y: auto;
        flex: 1;

        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    .submit-panel::-webkit-scrollbar {display: none;}
    
    #pdf-viewer {
        background-color: #101828;
        height: 100vh;
        display: flex;
        flex: 1;
        justify-content: center;
        align-items: center;
        text-align: center;
    }

    #editor {
        position: relative;
        display: none;
        width: 100%;
        min-height: 100px;
    }

    .lb::-webkit-scrollbar {
        display: none;
    }
    .lb {
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
</style>

<div class="horizontal-split">
    <div id="pdf-viewer">
        {#if submissionProblemID !== -1}
            <embed type="application/pdf" src={`/api/problem/${submissionProblemID}/pdf#toolbar=0&navpanes=0`} width="100%" height="100%">
        {:else}
            <p>No Problem Selected</p>
        {/if}
    </div>
    <div class="submit-panel">
        <MenuBar />
        <div class="main-container" style="flex: 0 0 auto;">
            {#await getData()}
                <p>Loading...</p>
            {:then}
                <h1>{contestName}</h1>
                {#if contestStatus === "upcoming"}
                    <p>The contest has not started yet. You cannot submit solutions.</p>
                {:else}
                    {#if contestStatus === "past"}
                        <p>The contest has ended. You can still view submissions and the leaderboard, but you cannot submit solutions.</p>
                    {:else}
                        <h2>Submit Code</h2>
                        <SubmitForm submissionType={"contest"} {ID} {problems} {reloadSubmissions} {reloadLeaderboard} bind:submissionProblemID/>
                    {/if}

                    <h2>Leaderboard</h2>
                    <div class="lb" style="width: 100%; overflow-x: scroll;">
                        <Leaderboard {ID} {problems} bind:this={leaderboard}/>            
                    </div>
                    <br>

                    {#if contestStatus === "past"}
                        <h2>All Submissions</h2>
                        <SubmissionTable submissions={submissions} showUsers={true}/>
                    {:else}
                        <h2>Your Submissions</h2>
                        <SubmissionTable submissions={submissions} showUsers={false}/>
                    {/if}
                {/if}
            {:catch error}
                <p>Error loading contest data: {error.message}</p>
            {/await}
        </div>
    </div>
</div>