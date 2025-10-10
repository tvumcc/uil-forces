<script lang="ts">
    import SubmitForm from "../components/submitForm.svelte"
    import MenuBar from "../components/menuBar.svelte"
    import SubmissionTable from "../components/submissionTable.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let hide = $state()
    let psetName = $state("")
    let problems = $state([])
    let submissions: any[] = $state([])

    let submissionProblemID = $state(-1)

    $effect(() => {
        if (submissionProblemID !== -1) {
            document.getElementById("pdf-viewer")!.style.display = "flex"
        } else {
            document.getElementById("pdf-viewer")!.style.display = "none"
        }
    })

    async function reloadSubmissions() {
        let response = await fetch(`/api/pset/${ID}`)
        let json = await response.json()
        submissions = json.submissions
    }

    async function getData() {
        let response = await fetch(`/api/pset/${ID}`)
        let json = await response.json()

        hide = json.hide
        psetName = json.name
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
                {#if hide !== undefined && !hide}
                    <h1>{psetName}</h1>
                    <h2>Submit Code</h2>
                    <SubmitForm submissionType={"pset"} {ID} {problems} {reloadSubmissions} bind:submissionProblemID/>

                    <h2>Your Submissions</h2>
                    <SubmissionTable {submissions} showUsers={false}/>
                {:else}
                    <p>This problem set is not available for practice.</p>
                {/if}
            {:catch error}
                <p>Error loading contest data: {error.message}</p>
            {/await}
        </div>
    </div>
</div>