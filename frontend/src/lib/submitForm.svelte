<script lang="ts">
    import {type Problem, type ContestProblem, csrfFetch, statusStr} from "$lib/utils"
    import { onDestroy, onMount } from "svelte";
    import { addErrorToast, addToast, ToastType } from "./toastStore.svelte";

    interface SubmitFormProps {
        submissionType: string
        ID: string 
        problems: Problem[] | ContestProblem[]
        submissionProblemID: number
        allowedLanguages?: string[]
        reloadSubmissions: Function
        reloadLeaderboard?: Function
    }

    let { 
        submissionType, 
        ID,
        problems,
        submissionProblemID = $bindable(-1),
        allowedLanguages = ["Java", "Python"],
        reloadSubmissions = () => {},
        reloadLeaderboard = () => {},
    }: SubmitFormProps = $props()

    const languages = new Map([
        ["Java", "java"],
        ["Python", "py"],
    ])

    let fileText = $state("")
    let submissionLanguage = $state("Java")
    let fileName = $state("")
    let submitting = $state(false)

    let cleanup: (() => void) | null = null

    async function submitProblem(event: Event) {
        event.preventDefault()
        submitting = true

        const response: Response = await csrfFetch(`/api/${submissionType}/submit`, "POST", {
            contestID: ID,
            problemID: submissionProblemID,
            code: fileText,
            language: submissionLanguage 
        })

        if (!response.ok) {
            await addErrorToast(response, "Failed to submit code")
            submitting = false
            return
        }

        let data = await response.json()

        addToast(`Your submission for ${data.submission.problem.name} is in the judge queue`, ToastType.Info)

        reloadSubmissions()
        reloadLeaderboard()

        cleanup = watchSubmission(data.submission.id)
    }

    function watchSubmission(submissionID: number) {
        const source = new EventSource(`/api/submission/${submissionID}/stream`)

        source.addEventListener("done", (e) => {
            let data = JSON.parse(e.data)
            addToast(`Judge verdict for ${data.problemName}: ${statusStr[data.status]}`, ToastType.Info)
            reloadSubmissions()
            reloadLeaderboard()
            submitting = false
            source.close()
        });

        source.addEventListener("error", (e) => {
            if (e instanceof MessageEvent && e.data) {
                addToast("Failed to retrieve verdict. Please refresh your page.", ToastType.Error)
            }
            submitting = false
            source.close()
        })

        return () => source.close()
    }

    async function loadFileFromInput(event: Event) {
        let files = (event.currentTarget as HTMLInputElement).files
        if (files && files.length > 0) {
            fileText = await files[0].text()
            fileName = files[0].name
        }
    }

    function clearFileInput(event: Event) {
        (event.currentTarget as HTMLInputElement).value = ""
        fileName = ""
    }

    onDestroy(() => {
        if (cleanup) cleanup()
    })
</script>

<form class="submit-form" onsubmit={submitProblem}>
    <div class="field-row">
        <div class="field">
            <label for="problem-select">Problem</label>
            <select id="problem-select" bind:value={submissionProblemID}>
                <option value={-1} disabled selected>Select problem</option>
                {#each problems as problem, i}
                    {#if "problem" in problem}
                        <option value="{problem.problem.id}">{i+1}. {problem.problem.name}</option>
                    {:else}
                        <option value="{problem.id}">{i+1}. {problem.name}</option>
                    {/if}
                {/each}
            </select>
        </div>

        {#if submissionProblemID !== -1}
            <div class="field">
                <label for="language-select">Language</label>
                <select id="language-select" bind:value={submissionLanguage}>
                    {#each languages.entries() as [lang, ext]}
                        {#if allowedLanguages.includes(lang)}
                            <option value="{lang}">{lang}</option>
                        {/if}
                    {/each}
                </select>
            </div>
        {/if}
    </div>

    {#if submissionProblemID !== -1}
        <div class="file-row">
            <label class="file-button" for="file-input">
                {fileName || "Choose File"}
                <input id="file-input" type="file" oninput={loadFileFromInput} onclick={clearFileInput}>
            </label>
            <button type="submit" class="submit-button" disabled={!fileName || submitting}>
                {submitting ? "Judging…" : "Submit"}
            </button>
        </div>
    {/if}
</form>

<style>
    .submit-form {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }

    select {
        background-color: #0f1a2e;
        color: white;
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 8px 10px;
        font-family: inherit;
        font-size: 14px;
        min-width: 220px;
    }
    select:focus {
        outline: none;
        border-color: #00d492;
    }
</style>