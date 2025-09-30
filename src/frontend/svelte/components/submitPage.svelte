<script lang="ts">
    import { onMount } from "svelte"
    import MenuBar from "./menubar.svelte"
    import SubmissionTable from "./submissionTable.svelte"
    import Leaderboard from "./leaderboard.svelte"
    import * as ace from "ace-builds"

    // [Language Name, Language File Extension]
    const languages = new Map([
        ["Java", "java"],
        ["Python", "py"],
        ["C++", "cpp"]
    ])

    // submissionType can either be "contest" or "pset", which determines whether id refers to a
    // Contest or ProblemSet respectively
    let { submissionType, ID } = $props()

    // Contest/ProblemSet Data
    let pageTitle = $state()
    let problems = $state([])
    let submissions = $state([])

    // File Upload Vars
    let files: FileList = $state()!
    let fileText = $state("")
    let fileName = $state("")

    // Code Editor Vars
    let codeText = $state("")

    // Options
    let showSelectedProblemSubmissions = $state(false)
    let submissionProblemID = $state(-1)
    let submissionLanguage = $state("Java")
    let submissionMethod = $state("write_code") 

    let leaderboard: Leaderboard

    ace.config.set("basePath", "ace-builds/src-noconflict")
    let editor: ace.Editor

    async function loadEditor() {
        editor = ace.edit("editor")
        editor.setOption("minLines", 5)
        editor.setOption("maxLines", 30)
        editor.setTheme("ace/theme/monokai")
        // editor.session.setMode("ace/mode/java")
        // editor.setKeyboardHandler("ace/keyboard/vim")

        editor.on("change", () => {
            localStorage.setItem(`problem_code_${submissionLanguage}_${submissionProblemID}`, editor.getValue())
            codeText = editor.getValue()
        })
    }

    async function getData() {
        let contest = submissionType === "contest"
        let response: Response = await fetch(`/api/${contest ? "contest" : "pset"}/${ID}`)
        let json = await response.json()
        console.log(json)
        pageTitle = json["name"]
        problems = json["problems"]
        submissions = json["submissions"]
    }

    // Submits a problem as a Contest or ProblemSet submission, depending on the value of the submissionType property
    async function submitProblem(event: Event) {
        event.preventDefault()
        let response: Response = await fetch(`/api/${submissionType}/submit`, {
            method: "POST",
            body: JSON.stringify({
                contest_id: ID,
                problem_id: submissionProblemID,
                code: submissionMethod === "upload_file" ? fileText : codeText,
                language: submissionLanguage 
            }),
            headers: {
                "Content-Type": "application/json; charset=UTF-8"
            }
        })
        let json = await response.json()
        submissions = json["submissions"]

        let count = json["estimated_wait"]
        let interval_id = setInterval(async () => {
            if (count > 0) {
                let response: Response = await fetch(`/api/${submissionType}/${ID}`)
                let json = await response.json()
                submissions = json["submissions"]
                leaderboard.getData()
                count--;
            } else {
                clearInterval(interval_id)
            }
        }, 1000)
    }

    $effect(() => {
        (async () => {
            if (files) {
                for (let file of files) {
                    fileText = await file.text()
                    fileName = file.name
                }
            }
        })()
    })

    $effect(() => {
        const storedCode = localStorage.getItem(`problem_code_${submissionLanguage}_${submissionProblemID}`) || ""
        if (submissionProblemID !== -1 && submissionMethod === "write_code" && submissionLanguage !== "") {
            document.getElementById("editor")!.style.display = "block"
            switch (submissionLanguage) {
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
            editor.setValue(storedCode)
            editor.clearSelection();
            editor.gotoLine(1);
            editor.getSession().setScrollTop(1);
            editor.blur();
            editor.focus();
        } else {
            document.getElementById("editor")!.style.display = "none"
        }
    })

    $effect(() => {
        if (submissionProblemID === -1) {
            document.getElementById("pdf-viewer")!.style.display = "none"
        } else {
            document.getElementById("pdf-viewer")!.style.display = "flex"
        }
    })

    onMount(() => {
        getData()
        loadEditor()
    })
</script>

<style>
    @import "../../style.css";

    .horizontal-split {
        display: flex;
        /* grid-template-columns: 1fr 1fr; */
        width: 100%;
        height: 100%;

        overflow: hidden;
    }

    .submit-panel {
        margin: 0;
        display: flex;
        align-items: center;
        flex-direction: column;
        height: 100vh;
        overflow-y: auto;
        flex: 1;

        scrollbar-width: none;
        -ms-overflow-style: none;
    }
    .submit-panel::-webkit-scrollbar {display: none;}
    
    #pdf-viewer {
        background-color: #101828;
        height: 100vh;
        display: flex;
        flex: 1;
        justify-content: center;
        align-items: center;
        text-align: center;
    }

    #editor {
        position: relative;
        display: none;
        width: 100%;
        min-height: 100px;
    }

    .lb::-webkit-scrollbar {
        display: none;
    }
    .lb {
        scrollbar-width: none;
        -ms-overflow-style: none;
    }
</style>

<div class="horizontal-split">
    <div id="pdf-viewer">
        {#if submissionProblemID !== -1}
            <embed type="application/pdf" src={`/api/problem/${submissionProblemID}/pdf#toolbar=0&navpanes=0`} width="100%" height="100%">
        {:else}
            <p>No Problem Selected</p>
        {/if}
    </div>
    <div class="submit-panel">
        <MenuBar />
        <div class="main-container" style="flex: 0 0 auto;">
            <h1>{pageTitle}</h1>
            <h2>Submit Code</h2>
            <form onsubmit={submitProblem}>
                <div>
                    <label for="problem-select">Problem:</label>
                    <select id="problem-select" bind:value={submissionProblemID}>
                        {#each problems as problem}
                            <option value="{problem["id"]}">{problem["name"]}</option>
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
                            <option value="{lang}">{lang}</option>
                        {/each}
                    </select>
                    <br>
                    {#if submissionLanguage !== ""}
                        <label for="code">
                            <input type="radio" id="write_code" name="submitType" value="write_code" bind:group={submissionMethod}>
                            Write Code
                        </label>
                        <label for="file">
                            <input type="radio" id="upload_file" name="submitType" value="upload_file" bind:group={submissionMethod}>
                            Upload File
                        </label>

                        {#if submissionMethod === "upload_file"}
                            <div>
                                <input type="file" bind:files>
                            </div>
                        {/if}
                    {/if}
                {/if}
                <div id="editor"></div>
            </form>
            <br>

            <h2>Leaderboard</h2>
            <div class="lb" style="width: 100%; overflow-x: scroll;">
                <Leaderboard {ID} {problems} bind:this={leaderboard}/>            
            </div>

            <br>

            <h2>Submissions</h2>
            <label for="show-selected-problem-submissions">Only Show Submissions for the Selected Problem</label>
            <input type="checkbox" id="show-selected-problem-submissions" bind:checked={showSelectedProblemSubmissions}>
            <SubmissionTable {submissions} {showSelectedProblemSubmissions} {submissionProblemID} showUsers={false}/>
        </div>
    </div>
</div>