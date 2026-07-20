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

    .field-row {
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
    }

    .field {
        display: flex;
        flex-direction: column;
        gap: 5px;
    }

    label {
        font-size: 12px;
        letter-spacing: 0.5px;
        color: #64748b;
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

    .file-row {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }

    .file-button {
        position: relative;
        display: inline-flex;
        align-items: center;
        background-color: #0f1a2e;
        border: 1px dashed #334155;
        border-radius: 6px;
        padding: 9px 14px;
        font-size: 14px;
        color: #94a3b8;
        cursor: pointer;
        transition: border-color 0.15s ease, color 0.15s ease;
    }
    .file-button:hover {
        border-color: #00d492;
        color: #e2e8f0;
    }
    @media (prefers-reduced-motion: reduce) {
        .file-button { transition: none; }
    }
    .file-button input[type="file"] {
        position: absolute;
        inset: 0;
        opacity: 0;
        cursor: pointer;
    }

    .submit-button {
        background-color: #00d492;
        color: #030712;
        border: none;
        border-radius: 6px;
        padding: 9px 20px;
        font-family: inherit;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        transition: opacity 0.15s ease;
    }
    .submit-button:hover:not(:disabled) {
        opacity: 0.85;
    }
    .submit-button:disabled {
        background-color: #1e293b;
        color: #64748b;
        cursor: not-allowed;
    }
    @media (prefers-reduced-motion: reduce) {
        .submit-button { transition: none; }
    }
</style>