let toasts: Toast[] = $state([])
let toastIDCounter = 0;

export enum ToastType {
    Success = "success",
    Info = "info",
    Error = "error"
}

export interface Toast {
    message: string,
    id: number,
    type: ToastType,
}

let errorCodeToMessageMap: Map<string, string> = new Map([
    ["user_not_found", "User does not exist"],
    ["problem_not_found", "Problem does not exist"],
    ["pset_not_found", "Problem set does not exist"],
    ["contest_not_found", "Contest does not exist"],
    ["submission_not_found", "Submission does not exist"],
    ["pdf_not_found", "PDF file does not exist"],

    ["user_exists", "A user with that username already exists"],
    ["pset_exists", "A problem set with that name already exists"],
    ["contest_exists", "A contest with that name already exists"],
    ["problem_exists_in_pset", "A problem with that name already exists in this problem set"],

    ["invalid_username", "Usernames must consist of 3 to 25 alphanumeric characters or underscores"],
    ["invalid_name", "Name must be between 3 to 50 characters"],
    ["invalid_scoring", "Scoring must consist of integer values"],
    ["invalid_timeout", "Timeout must consist of real number values greater than 0"],
    ["invalid_credentials", "Incorrect username or password"],
    ["invalid_file_type", "Invalid file type"],

    ["submission_cooldown_ongoing", "Please wait at least 5 seconds in between submissions"],
    ["pdf_restricted", "Access to this PDF file is restricted"],
    ["problem_already_linked", "Problem already linked to contest"],
    ["problem_not_linked", "Problem not linked to contest"],
    ["invalid_language", "Invalid language submitted"],
    ["contest_not_ongoing", "Submissions are not allowed at this time"],
    ["submission_view_restricted", "You may not view this submission right now"],
])

export function getToasts(): Toast[] {
    return toasts
}

export function addToast(message: string, type: ToastType, duration_ms: number = 4000) {
    const id = toastIDCounter++;
    toasts.push({message, id, type})

    console.log(`adding toast ${id} "${message}"`)

    if (duration_ms > 0) {
        setTimeout(() => dismissToast(id), duration_ms)
    }
}

export async function addErrorToast(response: Response, fallbackMessage: string) {
    const data = await response.json().catch(() => ({}))
    console.log(`addErrorToast: data.error = ${data.error}`)
    const errorMessage = data.error && errorCodeToMessageMap.has(data.error) ? 
        errorCodeToMessageMap.get(data.error) : fallbackMessage
    addToast(errorMessage!, ToastType.Error)
}

export function dismissToast(id: number) {
    const idx = toasts.findIndex((t) => t.id === id) 
    if (idx !== 1) toasts.splice(idx, 1)
}