<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/state";
    import { goBack } from "$lib/navigationHistory.svelte";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { csrfFetch, type ProblemSet } from "$lib/utils"

    let ID = page.url.searchParams.get("id")
    let pset: ProblemSet | undefined = $state()
    let loading = $state(true)

    let problemName = $state("")
    let confirmingDeleteID: number | null = $state(null)

    let files: FileList | undefined = $state()
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
        loading = false
    }

    async function editPset(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch("/api/admin/pset/update", "POST", {
            id: ID,
            name: pset!.name,
        })

        if (response.ok) {
            await getData()
            addToast("Updated problem set", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to update problem set")
        }
    }

    async function addProblem(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch(`/api/admin/pset/add/problem`, "POST", {
            psetID: pset!.id,
            problemName: problemName
        })

        if (response.ok) {
            await getData()
            addToast("Added new problem to problem set", ToastType.Success)
            problemName = ""
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
            files = undefined
        } else {
            await addErrorToast(response, "Failed to upload PDF file")
        }
    }

    async function deleteProblem(problemID: number) {
        let response: Response = await csrfFetch(`/api/admin/problem/${problemID}/delete`, "DELETE")
        confirmingDeleteID = null
        if (response.ok) {
            await getData()
            addToast("Deleted problem", ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to delete problem")
        }
    }

    $effect(() => {
        (async () => {
            if (files && files.length > 0) {
                fileData = await files[0].arrayBuffer()
            }
        })()
    })

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    {#if loading}
        <div class="panel skeleton"></div>
    {:else if pset !== undefined}
        <header class="hero">
            <h1>{pset.name}</h1>
        </header>

        <section class="panel">
            <h2 class="section-header">Edit Details</h2>
            <form class="stacked-form" onsubmit={editPset}>
                <div class="field">
                    <label for="name">Name</label>
                    <input name="name" type="text" bind:value={pset.name}>
                </div>
                <button type="submit" class="btn btn-primary">Update Problem Set</button>
            </form>
        </section>

        <section class="panel spaced">
            <h2 class="section-header">Edit PDF</h2>
            <a class="pdf-link" href="/api/admin/pset/{ID}/pdf" target="_blank">View PDF</a>
            <form class="stacked-form spaced-form" onsubmit={uploadPDF}>
                <div class="file-row">
                    <label class="file-button" for="pdf-upload">
                        {files && files.length > 0 ? files[0].name : "Choose PDF"}
                        <input id="pdf-upload" name="pdf-upload" type="file" accept="application/pdf" bind:files>
                    </label>
                    <button type="submit" class="submit-button" disabled={!files || files.length === 0}>Upload</button>
                </div>
            </form>
        </section>

        <section class="panel spaced">
            <h2 class="section-header">Edit Problems</h2>
            {#if pset.problems && pset.problems.length > 0}
                <table>
                    <thead>
                        <tr>
                            <th>name</th>
                            <th class="actions-col">action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each pset.problems as problem}
                            <tr>
                                <td><a href="/admin/problem?id={problem.id}">{problem.name}</a></td>
                                <td class="actions-cell">
                                    {#if confirmingDeleteID === problem.id}
                                        <span class="confirm-text">Delete?</span>
                                        <button class="btn btn-danger" onclick={() => deleteProblem(problem.id)}>Yes</button>
                                        <button class="btn" onclick={() => confirmingDeleteID = null}>No</button>
                                    {:else}
                                        <button class="btn btn-danger-outline" onclick={() => confirmingDeleteID = problem.id}>Delete</button>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            {:else}
                <p class="empty-state">No problems in this set yet.</p>
            {/if}
        </section>

        <section class="panel spaced">
            <h2 class="section-header">Create New Problem</h2>
            <form class="stacked-form" onsubmit={addProblem}>
                <div class="field">
                    <label for="problem-name">Problem Name</label>
                    <input name="problem-name" type="text" bind:value={problemName}>
                </div>
                <button type="submit" class="btn btn-primary">Create Problem</button>
            </form>
        </section>
    {/if}
</div>

<style>
    .pdf-link {
        display: inline-block;
        font-size: 13px;
        margin-bottom: 14px;
    }
    .spaced-form {
        flex-direction: row;
        align-items: center;
        max-width: none;
    }
</style>