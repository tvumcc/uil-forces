<script>
    import SubmitPage from "./components/submitPage.svelte"

    let params = new URLSearchParams(document.location.search)
    let id = params.get("id")
</script>

<SubmitPage submissionType={"pset"} ID={id}/>