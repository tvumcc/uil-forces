<script lang="ts">
    let { status_code, fit_text } = $props()
    let display_selector = fit_text ? "inline-block" : "block"
    let status_str = ["Pending", "Accepted", "Wrong Answer", "Compile Error", "Runtime Error", "Time Limit Exceeded"]
</script>

<style>
    /* Pending */
    .Status0 {
        background-color: rgb(114, 107, 112);
    }

    /* Accepted */
    .Status1 {
        background-color: green;
    }

    /* Wrong Answer */
    .Status2 {
        background-color: red;        
    }

    /* Compile Error */
    .Status3 {
        background-color: red;        
    }
    
    /* Runtime Error */
    .Status4 {
        background-color: red;        
    }

    /* Time Limit Exceeded */
    .Status5 {
        background-color: red;        
    }

    div {
        padding: 5px;
        border-radius: 13px;
    }
</style>

<div class="Status{status_code}" style="display: {display_selector};">
    <b>{ status_str[status_code] }</b>
</div>