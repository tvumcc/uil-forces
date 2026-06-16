<script lang="ts">
    import * as ace from "ace-builds"
    import Status from "../components/status.svelte"
    import MenuBar from "../components/menuBar.svelte"
    import type {Submission} from "../../utils"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")
    let validRequest = $state(true)
    let message = $state("")

    let submission: Submission | undefined = $state()

    ace.config.set("basePath", "/ace-builds/src-noconflict")
    let submissionCodeEditor: ace.Editor
    let submissionOutputEditor: ace.Editor
    let judgeInputEditor: ace.Editor
    let judgeOutputEditor: ace.Editor

    async function getData() {
        let response: Response = await fetch(`/api/submission/${ID}`)
        let json = await response.json()

        if (!response.ok) {
            validRequest = false
            message = json.description        
        }

        submission = json.submission
    }

    function fillEditors(node: Node) {
        if (submission !== undefined) {
            if (submission.code !== undefined) {
                submissionCodeEditor = ace.edit("submission-code")
                loadEditor(submissionCodeEditor, submission.code, true, submission.language)
            }

            if (submission.output !== undefined) {
                submissionOutputEditor = ace.edit("submission-output")
                loadEditor(submissionOutputEditor, submission.output)
            }

            if (submission.judgeInput !== undefined) {
                judgeInputEditor = ace.edit("judge-input")
                loadEditor(judgeInputEditor, submission.judgeInput)
            }

            if (submission.judgeOutput !== undefined) {
                judgeOutputEditor = ace.edit("judge-output")
                loadEditor(judgeOutputEditor, submission.judgeOutput)
            }
        }
    }

    function loadEditor(editor: ace.Editor, text: string, code = false, language: string = "Java") {
        if (code) {
            switch (language) {
                case "Java":
                    editor.session.setMode("ace/mode/java")
                    break
                case "Python":
                    editor.session.setMode("ace/mode/python")
                    break
            }
        }

        editor.setOption("minLines", 5)
        editor.setOption("maxLines", 30)
        editor.setOption("readOnly", true)
        editor.setShowPrintMargin(false)
        editor.setTheme("ace/theme/monokai")
        editor.setValue(text)
        editor.clearSelection()
        editor.gotoLine(1)
        editor.getSession().setScrollTop(1)
        editor.blur()
        editor.focus()
    }
</script>

<style>
    @import "../../style.css";
</style>

<MenuBar />
<div class="main-container">
    <h1>Submission</h1>
    {#await getData()}
        <p>Loading...</p> 
    {:then}
        {#if validRequest && submission !== undefined}
            <p>User: {submission.user.username}</p>
            <p>Submit Time: {new Date(submission.submitTime).toLocaleString()}</p>
            <p>Status: <Status statusCode={submission.status} fitText={true}/></p>

            {#if submission.contestProfile}
                <p>Contest: <a href="/contest?id={submission.contestProfile.contest.id}">{submission.contestProfile.contest.name}</a></p>
            {/if}

            <div use:fillEditors>
                {#if submission.code !== undefined}
                    <h2>Submitted Code</h2>
                    <div id="submission-code"></div>
                {/if}

                {#if submission.output !== undefined}
                    <h2>Submission Output</h2>
                    <div id="submission-output"></div>
                {/if}

                {#if submission.judgeInput!== undefined}
                    <h2>Judge Input</h2>
                    <div id="judge-input"></div>
                {/if}

                {#if submission.judgeOutput !== undefined}
                    <h2>Judge Output</h2>
                    <div id="judge-output"></div>
                {/if}
            </div>
        {:else}
            <p>{message}</p>
        {/if}
    {/await}
</div>