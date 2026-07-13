<script lang="ts">
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import {csrfFetch, type ProblemSet} from "$lib/utils"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let pset: ProblemSet | undefined = $state()

    let problemName = $state("")

    let files: FileList = $state()!
    let fileData: ArrayBuffer = $state(new ArrayBuffer(0))

    async function getData() {
        const response: Response = await fetch(`/api/admin/pset/${ID}`)

        if (!response.ok) {
            await addErrorToast(response, "Failed to load problem set")
            goBack()
            return
        }

        const data = await response.json()
        pset = data.pset
    }

    async function editPset(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch("/api/admin/update/pset", "POST", JSON.stringify({
            id: ID,
            name: pset!.name,
            gradingTimeout: pset!.gradingTimeout
        }))

        if (response.ok) {
            await getData()
            addToast("Updated problem set", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to update problem set")
        }
    }

    async function addProblem(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch(`/api/admin/pset/add/problem`, "POST", JSON.stringify({
            psetID: pset!.id,
            problemName: problemName 
        }))

        if (response.ok) {
            await getData()
            addToast("Added new problem to problem set", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to add new problem")
        }
    }

    async function uploadPDF(event: Event) {
        event.preventDefault()

        let formData = new FormData()
        formData.append("pdf", new Blob([fileData], { type: "application/pdf" }), "pset.pdf")

        let response: Response = await csrfFetch(`/api/admin/pset/${ID}/uploadpdf`, "POST", formData)

        if (response.ok) {
            await getData()
            addToast("Uploaded PDF file", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to upload PDF file")
        }
    }

    async function deleteProblem(problemID: number) {
        let response: Response = await csrfFetch(`/api/admin/problem/${problemID}/delete`, "DELETE", JSON.stringify({}))
        if (response.ok) {
            await getData()
            addToast("Deleted problem", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to delete problem")
        }
    }

    $effect(() => {
        (async () => {
            if (files) {
                for (let file of files) {
                    fileData = await file.arrayBuffer()
                }
            }
        })()
    })
</script>

<div class="main-container">
    <h1>Edit Problem Set</h1>

    {#await getData()}
        <p>Loading...</p> 
    {:then} 
        {#if pset !== undefined} 
            <form onsubmit={editPset}>
                <label for="name">Name</label>
                <input name="name" type="text" bind:value={pset.name}>
                <br>
                <label for="timeout">Grading Timeout (seconds)</label>
                <input name="timeout" type="number" step="any" bind:value={pset.gradingTimeout}>
                <br>
                <input type="submit" value="Update Problem Set">
            </form>

            <h2>PDF</h2>
            <a href="/api/admin/pset/{ID}/pdf" target="_blank">Download Current PDF</a>
            <form onsubmit={uploadPDF}>
                <label for="pdf-upload">Upload New Pset PDF</label>
                <input name="pdf-upload" type="file" bind:files>
                <input type="submit" value="Upload PDF">
            </form>

            <h2>Problems</h2>
            <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
            {#each pset.problems as problem}
                <tr class="pb-row">
                    <td><a href="/admin/problem?id={problem.id}">{problem.name}</a></td>
                    <td><button onclick={() => deleteProblem(problem.id)}>Delete</button></td>
                </tr>
            {/each}
            </tbody>
            </table>

            <h2>Add Problem</h2>
            <form onsubmit={addProblem}>
                <label for="problem-name">Problem Name</label>
                <input name="problem-name" type="text" bind:value={problemName}>
                <input type="submit" value="Add Problem">
            </form>
        {/if}
    {/await}
</div>

<style>
    table {
        border-collapse: collapse;
    }

    .pb-row td {
        border: 1px gray solid;
        margin: 0;
        padding: 8px;
        text-align: left;
    }
</style>
