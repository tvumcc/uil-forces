<script lang="ts">
    import { statusStr } from "$lib/utils"

    let { statusCode, fitText } = $props()
</script>

<div class="Status{statusCode}" style="display: {fitText ? "inline-block" : "block"};">
    <b>{ statusStr[statusCode] }</b>
</div>

<style>
    /* Pending */
    .Status0 {
        background-color: #737373;
    }

    /* Accepted */
    .Status1 {
        background-color: #009966;
    }

    /* Wrong Answer, Compile Error, Runtime Error, Time Limit Exceeded, Server Error */
    .Status2, .Status3, .Status4, .Status5, .Status6 {
        background-color: #fb2c36;        
    }

    div {
        padding: 5px 10px;
        border-radius: 13px;
    }
</style>