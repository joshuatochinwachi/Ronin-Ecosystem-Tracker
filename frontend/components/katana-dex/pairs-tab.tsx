"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import useSWR from "swr"
import { ExternalLink } from "lucide-react"
import { TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function KatanaPairsTab() {
    const { data: pairsData, error: pairsError, isLoading } = useSWR("/api/dune/trade-pairs", fetcher)

    const pairsColumns = [
        { key: "Active Pairs", label: "Trading Pair" },
        {
            key: "Total Trade Volume (USD)",
            label: "Volume (USD)",
            format: (val: number) => `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
        },
        { key: "Total Transactions", label: "Trades", format: (val: number) => val.toLocaleString() },
        { key: "Active Traders", label: "Unique Traders", format: (val: number) => val.toLocaleString() },
        {
            key: "Active Pairs Link",
            label: "Verify On-Chain",
            format: (val: string) => {
                if (!val) return "N/A"
                const match = val.match(/0x[a-fA-F0-9]{40}/)
                const address = match ? match[0] : null
                if (!address) return "N/A"
                return (
                    <a
                        href={`https://app.roninchain.com/address/${address}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:text-primary/80 flex items-center gap-1"
                    >
                        View <ExternalLink className="w-3 h-3" />
                    </a>
                )
            },
        },
    ]

    return (
        <Card className="glass-card">
            <CardHeader>
                <CardTitle>WRON Active Trade Pairs</CardTitle>
                {pairsData?.metadata && (
                    <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                        Last updated: {new Date(pairsData.metadata.last_updated).toLocaleString()} UTC
                    </p>
                )}
            </CardHeader>
            <CardContent>
                {isLoading ? (
                    <TableSkeleton rows={5} />
                ) : pairsData?.data ? (
                    <DataTable columns={pairsColumns} data={pairsData.data} />
                ) : pairsError ? (
                    <div className="text-destructive">Error loading data</div>
                ) : null}
            </CardContent>
        </Card>
    )
}
