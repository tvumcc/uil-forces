<script lang="ts">
    let { status_code, fit_text } = $props()
    let display_selector = fit_text ? "inline-block" : "block"
    let status_str = ["Pending", "Accepted", "Wrong Answer", "Compile Error", "Runtime Error", "Time Limit Exceeded"]
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

    /* Wrong Answer, Compile Error, Runtime Error, Time Limit Exceeded */
    .Status2, .Status3, .Status4, .Status5 {
        background-color: #fb2c36;        
    }

    div {
        padding: 5px 10px;
        border-radius: 13px;
    }
</style>

<div class="Status{status_code}" style="display: {display_selector};">
    <b>{ status_str[status_code] }</b>
</div>