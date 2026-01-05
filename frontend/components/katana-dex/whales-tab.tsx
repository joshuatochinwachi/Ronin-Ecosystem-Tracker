"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import useSWR from "swr"
import { ExternalLink } from "lucide-react"
import { TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function KatanaWhalesTab() {
    const { data: whalesData, error: whalesError, isLoading } = useSWR("/api/dune/whales", fetcher)

    const whalesColumns = [
        {
            key: "trader (whale) who traded over $10,000 in the last 30 days",
            label: "Trader Address",
            format: (val: string) => {
                const cleanAddress = val.replace(/^0x/, "0x")
                return (
                    <a
                        href={`https://app.roninchain.com/address/${cleanAddress}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:text-primary/80 flex items-center gap-1"
                    >
                        {cleanAddress.slice(0, 8)}...{cleanAddress.slice(-6)}
                        <ExternalLink className="w-3 h-3" />
                    </a>
                )
            },
        },
        {
            key: "total trade volume (USD)",
            label: "Volume (USD)",
            format: (val: number) => `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
        },
        { key: "total trades", label: "Trades", format: (val: number) => val.toLocaleString() },
        {
            key: "avg trade size (USD)",
            label: "Avg Trade Size",
            format: (val: number) => `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
        },
        { key: "primary activity", label: "Primary Activity" },
    ]

    return (
        <Card className="glass-card">
            <CardHeader>
                <CardTitle>WRON Whale Tracking (Traders who traded over $10k in the last 30 days)</CardTitle>
                {whalesData?.metadata && (
                    <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                        Last updated: {new Date(whalesData.metadata.last_updated).toLocaleString()} UTC
                    </p>
                )}
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <TableSkeleton rows={5} />
                ) : whalesData?.data ? (
                    <DataTable columns={whalesColumns} data={whalesData.data} />
                ) : whalesError ? (
                    <div className="text-destructive">Error loading data</div>
                ) : null}
            </CardContent>
        </Card>
    )
}
