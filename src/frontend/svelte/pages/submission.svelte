<script lang="ts">
    import { onMount } from "svelte"
    import * as ace from "ace-builds"
    import Status from "../components/status.svelte"
    import MenuBar from "../components/menuBar.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")

    ace.config.set("basePath", "/ace-builds/src-noconflict")
    let submissionCodeEditor: ace.Editor
    let submissionOutputEditor: ace.Editor
    let judgeInputEditor: ace.Editor
    let judgeOutputEditor: ace.Editor

    let username = $state("")
    let submitTime = $state("")
    let submissionStatus = $state(0)
    let language = $state("")

    let submissionCode = $state("")
    let submissionOutput = $state("")
    let judgeInput = $state("")
    let judgeOutput = $state("")

    let contestProfile: any = $state()

    async function getData() {
        let response: Response = await fetch(`/api/submission/${ID}`)
        let json = await response.json()

        username = json["user"]["username"]
        submitTime = json["submit_time"]
        submissionStatus = json["status"]
        language = json["language"]

        submissionCode = json["code"]
        submissionOutput = json["output"]
        judgeInput = json["judge_input"]
        judgeOutput = json["judge_output"]

        contestProfile = json["contest_profile"]

        submissionCodeEditor = ace.edit("submission-code")
        submissionOutputEditor = ace.edit("submission-output")
        judgeInputEditor = ace.edit("judge-input")
        judgeOutputEditor = ace.edit("judge-output")

        loadEditor(submissionCodeEditor, submissionCode, true)
        loadEditor(submissionOutputEditor, submissionOutput)
        loadEditor(judgeInputEditor, judgeInput)
        loadEditor(judgeOutputEditor, judgeOutput)
    }

    function loadEditor(editor: ace.Editor, text: string, code = false) {
        if (code) {
            switch (language) {
                case "Java":
                    editor.session.setMode("ace/mode/java")
                    break
                case "Python":
                    editor.session.setMode("ace/mode/python")
                    break
                case "C++":
                    editor.session.setMode("ace/mode/c_cpp")
                    break
            }
        }

        editor.setOption("minLines", 5)
        editor.setOption("maxLines", 30)
        editor.setOption("readOnly", true)
        editor.setShowPrintMargin(false)
        editor.setTheme("ace/theme/monokai")
        editor.setValue(text)
        editor.clearSelection();
        editor.gotoLine(1);
        editor.getSession().setScrollTop(1);
        editor.blur();
        editor.focus();
    }

    onMount(getData)
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Submission</h1>

    <p>User: {username}</p>
    <p>Submit Time: {new Date(submitTime).toLocaleString()}</p>
    <p>Status: <Status statusCode={submissionStatus} fitText={true}/></p>
    {#if contestProfile}
        <p>Contest: <a href="/contest?id={contestProfile.contest.id}">{contestProfile.contest.name}</a></p>
    {/if}

    {#if submissionCode !== undefined}
        <h2>Submitted Code</h2>
    {/if}
    <div id="submission-code"></div>

    {#if submissionOutput !== undefined}
        <h2>Submission Output</h2>
    {/if}
    <div id="submission-output"></div>

    {#if judgeInput !== undefined}
        <h2>Judge Input</h2>
    {/if}
    <div id="judge-input"></div>

    {#if judgeOutput!== undefined}
        <h2>Judge Output</h2>
    {/if}
    <div id="judge-output"></div>
</div>