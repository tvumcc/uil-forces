<script lang="ts">
    import * as ace from "ace-builds"
    import MenuBar from "../components/menuBar.svelte"
    import type {Problem} from "../../utils"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")
    let validRequest = $state(true)
    let message = $state("")

    let problem: Problem | undefined = $state()

    ace.config.set("basePath", "/ace-builds/src-noconflict")
    let studentInputEditor: ace.Editor
    let judgeInputEditor: ace.Editor
    let judgeOutputEditor: ace.Editor

    async function getData() {
        let response: Response = await fetch(`/api/admin/problem/${ID}`)
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description
        }

        problem = json.problem
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

    async function editProblem(event: Event) {
        event.preventDefault()

        let response: Response = await fetch("/api/admin/update/problem", {
            method: "POST",
            body: JSON.stringify(problem),
            headers: {"Content-Type": "application/json; charset=UTF-8"}
        })

        if (response.ok) {
            await getData()
        }
    }
</script>

<!-- svelte-ignore css_unused_selector -->
<style>
    @import "../../style.css";

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

<MenuBar />
<div class="main-container">
    <h1>Edit Problem</h1>

    {#await getData()}
        <p>Loading...</p>
    {:then} 
        {#if validRequest && problem !== undefined}
            <form onsubmit={editProblem}>
                <label for="name">Name</label>
                <input name="name" type="text" bind:value={problem.name}>
                <br>
                <label for="pages">PDF Pages</label>
                <input name="pages" type="text" bind:value={problem.pages}>
                <br>
                <label for="use-stdin">Use Standard Input</label>
                <input name="use-stdin" type="checkbox" bind:checked={problem.useStdin}>
                <br>
                <label for="input-file-name">Input File Name</label>
                <input name="input-file-name" type="text" bind:value={problem.inputFileName}>
                <br>

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
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>