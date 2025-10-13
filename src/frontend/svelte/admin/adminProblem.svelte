<script lang="ts">
    import { onMount } from "svelte"
    import * as ace from "ace-builds"
    import MenuBar from "../components/menuBar.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    let problem = $state()

    let name = $state("")
    let pages = $state("")
    let useStdin = $state(false)
    let inputFileName = $state("")
    let studentInput = $state("")
    let judgeInput = $state("")
    let judgeOutput = $state("")

    ace.config.set("basePath", "/ace-builds/src-noconflict")
    let studentInputEditor: ace.Editor
    let judgeInputEditor: ace.Editor
    let judgeOutputEditor: ace.Editor

    async function getData() {
        let response: Response = await fetch(`/api/admin/problem/${ID}`)
        let json = await response.json()
        name = json["problem"]["name"]
        pages = json["problem"]["pages"] 
        useStdin = json["problem"]["use_stdin"]
        inputFileName = json["problem"]["input_file_name"]
        studentInput = json["problem"]["student_input"] 
        judgeInput = json["problem"]["judge_input"]
        judgeOutput = json["problem"]["judge_output"]

        studentInputEditor = ace.edit("student-input")
        judgeInputEditor = ace.edit("judge-input")
        judgeOutputEditor = ace.edit("judge-output")

        loadEditor(studentInputEditor, studentInput)
        loadEditor(judgeInputEditor, judgeInput)
        loadEditor(judgeOutputEditor, judgeOutput)
    }

    function loadEditor(editor: ace.Editor, text: string) {
        editor.setOption("minLines", 5)
        editor.setOption("maxLines", 30)
        editor.setTheme("ace/theme/monokai")
        editor.setValue(text)
        editor.clearSelection();
        editor.gotoLine(1);
        editor.getSession().setScrollTop(1);
        editor.blur();
        editor.focus();
    }

    async function editProblem(event: Event) {
        event.preventDefault()

        let response: Response = await fetch("/api/admin/update/problem", {
            method: "POST",
            body: JSON.stringify({
                id: ID,
                name: name,
                pages: pages,
                use_stdin: useStdin,
                input_file_name: inputFileName,
                student_input: studentInputEditor.getValue(),
                judge_input: judgeInputEditor.getValue(),
                judge_output: judgeOutputEditor.getValue(),
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })

        if (response.ok) {
            await getData()
        }
    }

    onMount(getData)
</script>

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

    <form onsubmit={editProblem}>
        <label for="name">Name</label>
        <input name="name" type="text" bind:value={name}>
        <br>
        <label for="pages">PDF Pages</label>
        <input name="pages" type="text" bind:value={pages}>
        <br>
        <label for="use-stdin">Use Standard Input</label>
        <input name="use-stdin" type="checkbox" bind:checked={useStdin}>
        <br>
        <label for="input-file-name">Input File Name</label>
        <input name="input-file-name" type="text" bind:value={inputFileName}>
        <br>

        <h3>Student Input</h3>
        <div id="student-input"></div>  
        <h3>Judge Input</h3>
        <div id="judge-input"></div>
        <h3>Judge Output</h3>
        <div id="judge-output"></div>

        <input type="submit" value="Update Problem">
    </form>
</div>