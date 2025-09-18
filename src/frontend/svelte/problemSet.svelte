<script>
    import SubmitPage from "./components/submitPage.svelte"

    let params = new URLSearchParams(document.location.search)
    let ID = params.get("id")
</script>

<SubmitPage submissionType={"pset"} {ID}/>