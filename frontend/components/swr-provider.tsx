"use client"

import { SWRConfig } from "swr"
import type React from "react"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function SWRProvider({ children }: { children: React.ReactNode }) {
    return (
        <SWRConfig
            value={{
                fetcher,
                // Aggressive caching for instant tab switching
                dedupingInterval: 60000, // Prevent duplicate requests for 60s
                revalidateOnFocus: false, // Don't refetch when window regains focus
                revalidateOnReconnect: false, // Don't refetch on reconnect
                keepPreviousData: true, // Show stale data while revalidating
                // Longer cache time for better performance
                focusThrottleInterval: 60000,
            }}
        >
            {children}
        </SWRConfig>
    )
}
