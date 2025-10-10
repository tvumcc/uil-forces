<script lang="ts">
    import * as ace from "ace-builds"
    import { onMount } from "svelte";

    let { 
        submissionType, 
        ID,
        problems,
        submissionProblemID = $bindable(-1),
        allowed_languages = ["Java", "Python", "C++"],
        reloadSubmissions = () => {},
        reloadLeaderboard = () => {},
    } = $props()

    // [Language Name, Language File Extension]
    const languages = new Map([
        ["Java", "java"],
        ["Python", "py"],
        ["C++", "cpp"]
    ])

    let files: FileList = $state()!
    let fileText = $state("")

    let codeText = $state("")

    let submissionLanguage = $state("Java")
    let submissionMethod = $state("write_code") 

    ace.config.set("basePath", "ace-builds/src-noconflict")
    let editor: ace.Editor

    async function loadEditor() {
        editor = ace.edit("editor")
        editor.setOption("minLines", 5)
        editor.setOption("maxLines", 30)
        editor.setTheme("ace/theme/monokai")

        editor.on("change", () => {
            localStorage.setItem(`problem_code_${submissionLanguage}_${submissionProblemID}`, editor.getValue())
            codeText = editor.getValue()
        })
    }

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

        reloadSubmissions()
        reloadLeaderboard()

        let count = json["estimated_wait"]
        let interval_id = setInterval(async () => {
            if (count > 0) {
                reloadSubmissions()
                reloadLeaderboard()
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

    onMount(() => {
        loadEditor()
    })
</script>

<form onsubmit={submitProblem}>
    <div>
        <label for="problem-select">Problem:</label>
        <select id="problem-select" bind:value={submissionProblemID}>
            {#each problems as problem, i}
                <option value="{problem["id"]}">{i+1}. {problem["name"]}</option>
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
                {#if allowed_languages.includes(lang)}
                    <option value="{lang}">{lang}</option>
                {/if}
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