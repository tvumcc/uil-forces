<script lang="ts">
    import * as ace from "ace-builds"
    import {csrfFetch, type Problem} from "$lib/utils"
    import { addToast, addErrorToast, ToastType } from "$lib/toastStore.svelte";
    import { goBack } from "$lib/navigationHistory.svelte";

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let problem: Problem | undefined = $state()

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

        const response: Response = await csrfFetch("/api/admin/update/problem", "POST", JSON.stringify(problem))

        if (response.ok) {
            await getData()
            addToast(`Updated problem`, ToastType.Success)
        } else {
            await addErrorToast(response, "Failed to update problem")
        }
    }
</script>

<div class="main-container">
    <h1>Edit Problem</h1>

    {#await getData()}
        <p>Loading...</p>
    {:then} 
        {#if problem !== undefined}
            <form onsubmit={updateProblem}>
                <table>
                    <tbody>
                        <tr>
                            <td><label for="name">Name</label></td>
                            <td><input name="name" type="text" bind:value={problem.name}></td>
                        </tr>
                        <tr>
                            <td><label for="pages">PDF Pages</label></td>
                            <td><input name="pages" type="text" bind:value={problem.pages}></td>
                        </tr>
                        <tr>
                            <td><label for="use-stdin">Use Standard Input</label></td>
                            <td><input name="use-stdin" type="checkbox" bind:checked={problem.useStdin}></td>
                        </tr>
                        <tr>
                            <td><label for="input-file-name">Input File Name</label></td>
                            <td><input name="input-file-name" type="text" bind:value={problem.inputFileName}></td>
                        </tr>
                    </tbody>
                </table>

                <div use:fillEditors>
                    <h3>Student Input</h3>
                    <div id="student-input"></div>  
                    <h3>Judge Input</h3>
                    <div id="judge-input"></div>
                    <h3>Judge Output</h3>
                    <div id="judge-output"></div>
                </div>

                <input type="submit" value="Update Problem">
            </form>
        {/if}
    {/await}
</div>

<style>
    table {
        border-collapse: collapse;
    }

    td {
        border: 1px gray solid;
        margin: 0;
        padding: 8px;
        text-align: left;
    }
</style>