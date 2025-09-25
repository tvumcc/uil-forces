<script lang="ts">
    let { statusCode, fitText } = $props()
    let displaySelector = fitText ? "inline-block" : "block"
    let statusStr = ["Pending", "Accepted", "Wrong Answer", "Compile Error", "Runtime Error", "Time Limit Exceeded", "Server Error"]
</script>

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

<div class="Status{statusCode}" style="display: {displaySelector};">
    <b>{ statusStr[statusCode] }</b>
</div>