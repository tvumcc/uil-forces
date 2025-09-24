<script lang="ts">
    import Status from "./status.svelte"

    let {submissions, submissionProblemID, showSelectedProblemSubmissions, showUsers} = $props()
</script>

<style>
    @import "../../style.css";

    table {
        width: 100%;
        margin: 0;
        border-collapse: collapse;
    }

    td {
        border: 1px gray solid;
        margin: 0;
        padding: 8px;
        text-align: center;
    }
</style>

{#if submissions.length > 0}
    <table>
        <thead>
            <tr>
                <th>Time</th>
                {#if showUsers}
                    <th>User</th>
                {/if}
                <th>Problem</th>
                <th>Language</th>
                <th>Status</th>
                <th>Code</th>
            </tr>
        </thead>
        <tbody>
            {#each submissions as submission}
                {#if !showSelectedProblemSubmissions || submission["problem"]["id"] === submissionProblemID}
                    <tr>
                        <td>{submission["submit_time"]}</td>
                        {#if showUsers}
                            <td>{submission["user"]}</td>
                        {/if}
                        <td>{submission["problem"]["name"]}</td>
                        <td>{submission["language"]}</td>
                        <td style="width: 175px;"><Status statusCode={submission["status"]} fitText={false}/></td>
                        <td style="width: 80px;"><a href="/submission?id={submission["id"]}">View Code</a></td>
                    </tr>
                {/if}
            {/each}
        </tbody>
    </table>
{:else}
    <p>No submissions at this time</p>
{/if}