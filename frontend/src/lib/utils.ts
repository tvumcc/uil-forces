function pad(n: number) {
    return (n < 10 ? '0' : '') + n;
}

export function getTzOffset() {
    let tzOffset = -(new Date().getTimezoneOffset())
    let diff = tzOffset >= 0 ? "+" : "-"

    return diff + pad(Math.floor(Math.abs(tzOffset) / 60)) + ":" + pad(Math.abs(tzOffset) % 60)
}

export function toTzIsoString(date: Date): string {
    return date.getFullYear() +
        '-' + pad(date.getMonth() + 1) +
        '-' + pad(date.getDate()) +
        'T' + pad(date.getHours()) +
        ':' + pad(date.getMinutes())
}

export const statusStr = ["Pending", "Accepted", "Wrong Answer", "Compile Error", "Runtime Error", "Time Limit Exceeded", "Server Error"]

let csrfToken: string | null = null

async function getCsrfToken() {
    if (!csrfToken) {
        let response = await fetch("/api/csrf-token")
        let data = await response.json()
        csrfToken = data.csrfToken
    }
    return csrfToken
}

export async function csrfFetch(url: string, method: string, body?: any) {
    const token = await getCsrfToken()
    const isFormData = body instanceof FormData

    return fetch(url, {
        method,
        headers: {
            "X-CSRFToken": token!,
            ...(isFormData ? {} : {"Content-Type": "application/json; charset=UTF-8"}),
        },
        body: isFormData ? body : JSON.stringify(body),
    })
}


export interface Problem {
    id: number
    name: string

    pages?: string
    useStdin?: boolean
    inputFileName?: string
    studentInput?: string
    judgeInput?: string
    judgeOutput?: string
    problemSetID?: number
}

export interface ContestProblem {
    problem: Problem
    correctScore: number
    incorrectPenalty: number
    gradingTimeout: number
}

export interface User {
    id: number
    username: string
    isAdmin?: boolean
}

export interface Contest {
    id: number
    name: string
    startTime: string
    endTime: string
    status: string
    allowedLanguages: string
    showLeaderboard: boolean
    showPdf: boolean

    problems?: ContestProblem[]
    contestProfiles?: ContestProfile[]
    submissions?: Submission[]
}

export interface ContestProfile {
    user: User
    contest: Contest
    id: number
    score: number

    submissions?: Submission[]
}

export interface Submission {
    id: number
    user: User
    problem: Problem
    contestProfile?: ContestProfile

    submitTime: string
    status: number
    language: string

    code?: string
    output?: string
    judgeInput?: string
    judgeOutput?: string
}

export interface ProblemSet {
    id: number
    name: string
    problems?: Problem[]
    submissions?: Submission[]
}

export interface LeaderboardEntry {
    user: User
    score: number
    problemsSolved: number[][]
}

export interface Settings {
    docker_grading: boolean
}