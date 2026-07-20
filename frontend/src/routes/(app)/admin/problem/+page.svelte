<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/state";
    import * as ace from "ace-builds"
    import { csrfFetch, type Problem } from "$lib/utils"
    import { addToast, addErrorToast, ToastType } from "$lib/toastStore.svelte";
    import { goBack } from "$lib/navigationHistory.svelte";

    let ID = page.url.searchParams.get("id")
    let problem: Problem | undefined = $state()
    let psetName: string | undefined = $state()
    let psetID: number | undefined = $state()
    let loading = $state(true)

    ace.config.set("basePath", "ace-builds/src-noconflict")
    let studentInputEditor: ace.Editor
    let judgeInputEditor: ace.Editor
    let judgeOutputEditor: ace.Editor

    async function getData() {
        const response: Response = await fetch(`/api/admin/problem/${ID}`)

        if (!response.ok) {
            await addErrorToast(response, "Failed to load problem")
            goBack()
            return
        }

        const data = await response.json()
        problem = data.problem
        psetName = data.pset.name
        psetID = data.pset.id
        loading = false
    }

    function fillEditors(node: Node) {
        studentInputEditor = ace.edit("student-input")
        judgeInputEditor = ace.edit("judge-input")
        judgeOutputEditor = ace.edit("judge-output")

        loadEditor(studentInputEditor, problem!.studentInput!)
        loadEditor(judgeInputEditor, problem!.judgeInput!)
        loadEditor(judgeOutputEditor, problem!.judgeOutput!)
    }

    function loadEditor(editor: ace.Editor, text: string) {
        editor.setOption("minLines", 5)
        editor.setOption("maxLines", 30)
        editor.setShowPrintMargin(false)
        editor.setTheme("ace/theme/monokai")
        editor.setValue(text)
        editor.clearSelection()
        editor.gotoLine(1)
        editor.getSession().setScrollTop(1)
        editor.blur()
        editor.focus()
    }

    async function updateProblem(event: Event) {
        event.preventDefault()

        problem!.studentInput = studentInputEditor.getValue()
        problem!.judgeInput = judgeInputEditor.getValue()
        problem!.judgeOutput = judgeOutputEditor.getValue()

        const response: Response = await csrfFetch("/api/admin/problem/update", "POST", problem)

        if (response.ok) {
            await getData()
            addToast(`Updated problem`, ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to update problem")
        }
    }

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    {#if loading}
        <div class="panel skeleton"></div>
    {:else if problem !== undefined}
        <header class="hero">
            <h1><a href="/admin/pset?id={psetID}">{psetName}</a>: {problem.name}</h1>
        </header>

        <form onsubmit={updateProblem}>
            <section class="panel">
                <h2 class="section-header">Details</h2>
                <div class="stacked-form">
                    <div class="field">
                        <label for="name">Name</label>
                        <input name="name" type="text" bind:value={problem.name}>
                    </div>
                    <div class="field">
                        <label for="pages">PDF Pages</label>
                        <input name="pages" type="text" bind:value={problem.pages}>
                    </div>
                    <div class="field">
                        <label for="input-file-name">Input File Name</label>
                        <input name="input-file-name" type="text" bind:value={problem.inputFileName}>
                    </div>
                    <div class="checkbox-row">
                        <label class="checkbox-field">
                            <input name="use-stdin" type="checkbox" bind:checked={problem.useStdin}>
                            Use Standard Input
                        </label>
                    </div>
                </div>
            </section>

            <section class="panel spaced" use:fillEditors>
                <h2 class="section-header">Student Input</h2>
                <div id="student-input" class="editor"></div>

                <h2 class="section-header spaced">Judge Input</h2>
                <div id="judge-input" class="editor"></div>

                <h2 class="section-header spaced">Judge Output</h2>
                <div id="judge-output" class="editor"></div>
            </section>

            <button type="submit" class="btn btn-primary spaced-btn">Update Problem</button>
        </form>
    {/if}
</div>

<style>
    .editor {
        border: 1px solid #1e293b;
        border-radius: 6px;
        overflow: hidden;
    }
</style>