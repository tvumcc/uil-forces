<script lang="ts">
    import SubmitForm from "../components/submitForm.svelte"
    import MenuBar from "../components/menuBar.svelte"
    import SubmissionTable from "../components/submissionTable.svelte"
    import type {ProblemSet} from "../../utils"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")
    let validRequest = $state(true)
    let message = $state("")

    let pset: ProblemSet | undefined = $state(undefined)
    let submissionProblemID = $state(-1)

    $effect(() => {
        if (submissionProblemID !== -1) {
            document.getElementById("pdf-viewer")!.style.display = "flex"
        } else {
            document.getElementById("pdf-viewer")!.style.display = "none"
        }
    })

    async function getData() {
        let response = await fetch(`/api/pset/${ID}`)
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        pset = json.pset
    }
</script>

<!-- svelte-ignore css_unused_selector -->
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
                {#if validRequest && pset !== undefined}
                    {#if pset.hide !== null && !pset.hide}
                        <h1>{pset.name}</h1>
                        <a href="/api/pset/{ID}/data" target="_blank">Download Student Data</a>
                        <h2>Submit Code</h2>
                        <SubmitForm submissionType={"pset"} ID={ID!} problems={pset.problems!} reloadSubmissions={getData} bind:submissionProblemID/>

                        <h2>Your Submissions</h2>
                        <SubmissionTable submissions={pset.submissions} showUsers={false}/>
                    {:else}
                        <p>This problem set is not available for practice.</p>
                    {/if}
                {:else} 
                    <p>{message}</p>
                {/if}
            {/await}
        </div>
    </div>
</div>