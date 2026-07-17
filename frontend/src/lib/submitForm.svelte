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

    // [Language Name, Language File Extension]
    const languages = new Map([
        ["Java", "java"],
        ["Python", "py"],
    ])

    let fileText = $state("")
    let submissionLanguage = $state("Java")

    let cleanup: (() => void) | null = null

    async function submitProblem(event: Event) {
        event.preventDefault()

        const response: Response = await csrfFetch(`/api/${submissionType}/submit`, "POST", JSON.stringify({
            contestID: ID,
            problemID: submissionProblemID,
            code: fileText,
            language: submissionLanguage 
        }))

        if (!response.ok) {
            await addErrorToast(response, "Failed to submit code")
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
            source.close()
        });

        source.addEventListener("error", (e) => {
            if (e instanceof MessageEvent && e.data) {
                addToast("Failed to retrieve verdict. Please refresh your page.", ToastType.Error)
            }
            source.close()
        })

        return () => source.close()
    }

    async function loadFileFromInput(event: Event) {
        let files = (event.currentTarget as HTMLInputElement).files
        if (files) {
            for (let file of files) {
                fileText = await file.text()
            }
        }
    }

    function clearFileInput(event: Event) {
        (event.currentTarget as HTMLInputElement).value = ""
    }

    onDestroy(() => {
        if (cleanup) cleanup()
    })
</script>

<form onsubmit={submitProblem}>
    <div>
        <label for="problem-select">Problem:</label>
        <select id="problem-select" bind:value={submissionProblemID}>
            {#each problems as problem, i}
                {#if "problem" in problem}
                    <option value="{problem.problem.id}">{i+1}. {problem.problem.name}</option>
                {:else}
                    <option value="{problem.id}">{i+1}. {problem.name}</option>
                {/if}
            {/each}
        </select>
        {#if submissionProblemID !== -1} 
            <input type="submit" value="Submit">
        {/if}
    </div>

    {#if submissionProblemID !== -1}
        <label for="language-select">Language:</label>
        <select id="language-select" bind:value={submissionLanguage}>
            {#each languages.entries() as [lang, ext]}
                {#if allowedLanguages.includes(lang)}
                    <option value="{lang}">{lang}</option>
                {/if}
            {/each}
        </select>
        <br>
        {#if submissionLanguage !== ""}
            <div>
                <input type="file" oninput={loadFileFromInput} onclick={clearFileInput}>
            </div>
        {/if}
    {/if}
</form>