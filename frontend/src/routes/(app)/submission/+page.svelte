<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/state";
    import { addErrorToast, addToast, ToastType } from "$lib/toastStore.svelte";
    import { goBack } from "$lib/navigationHistory.svelte";
    import * as ace from "ace-builds"

    import type { Submission } from "$lib/utils"
    import Status from "$lib/status.svelte"

    let ID = page.url.searchParams.get("id")
    let submission: Submission | undefined = $state()
    let loading = $state(true)

    ace.config.set("basePath", "/ace-builds/src-noconflict")
    let submissionCodeEditor: ace.Editor
    let submissionOutputEditor: ace.Editor
    let judgeInputEditor: ace.Editor
    let judgeOutputEditor: ace.Editor

    async function getData() {
        const response: Response = await fetch(`/api/submission/${ID}`)

        if (!response.ok) {
            await addErrorToast(response, "Failed to load submission")
            goBack()
            return
        }

        const data = await response.json()
        submission = data.submission
        loading = false
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

    onMount(() => {
        getData()
    })
</script>

<div class="main-container">
    {#if loading}
        <div class="panel skeleton"></div>
    {:else if submission !== undefined}
        <header class="hero">
            <h1>Submission</h1>
        </header>

        <section class="panel">
            <h2 class="section-header">Details</h2>
            <dl class="detail-list">
                <div class="detail-row">
                    <dt>User</dt>
                    <dd>{submission.user.username}</dd>
                </div>
                <div class="detail-row">
                    <dt>Submit Time</dt>
                    <dd>{new Date(submission.submitTime).toLocaleString()}</dd>
                </div>
                <div class="detail-row">
                    <dt>Language</dt>
                    <dd>{submission.language}</dd>
                </div>
                <div class="detail-row">
                    <dt>Status</dt>
                    <dd><Status statusCode={submission.status} fitText={true} /></dd>
                </div>
                {#if submission.contestProfile}
                    <div class="detail-row">
                        <dt>Contest</dt>
                        <dd><a href="/contest?id={submission.contestProfile.contest.id}">{submission.contestProfile.contest.name}</a></dd>
                    </div>
                {/if}
            </dl>
        </section>

        <div use:fillEditors>
            {#if submission.code !== undefined}
                <section class="panel spaced">
                    <h2 class="section-header">Submitted Code</h2>
                    <div id="submission-code" class="editor"></div>
                </section>
            {/if}

            {#if submission.output !== undefined}
                <section class="panel spaced">
                    <h2 class="section-header">Submission Output</h2>
                    <div id="submission-output" class="editor"></div>
                </section>
            {/if}

            {#if submission.judgeInput !== undefined}
                <section class="panel spaced">
                    <h2 class="section-header">Judge Input</h2>
                    <div id="judge-input" class="editor"></div>
                </section>
            {/if}

            {#if submission.judgeOutput !== undefined}
                <section class="panel spaced">
                    <h2 class="section-header">Judge Output</h2>
                    <div id="judge-output" class="editor"></div>
                </section>
            {/if}
        </div>
    {/if}
</div>

<style>
    .detail-list {
        margin: 0;
    }
    .detail-row {
        display: flex;
        gap: 14px;
        padding: 7px 0;
        border-bottom: 1px solid #131d2e;
        font-size: 14px;
    }
    .detail-row:last-child {
        border-bottom: none;
    }
    .detail-row dt {
        width: 120px;
        flex-shrink: 0;
        color: #64748b;
    }
    .detail-row dd {
        margin: 0;
    }

    .editor {
        border: 1px solid #1e293b;
        border-radius: 6px;
        overflow: hidden;
    }
</style>