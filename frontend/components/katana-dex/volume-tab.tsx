"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import useSWR from "swr"
import { useState, useEffect, useMemo } from "react"
import { ChartSkeleton, TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function KatanaVolumeTab() {
    const { data: volumeData, error: volumeError, isLoading } = useSWR("/api/dune/volume-liquidity", fetcher)
    const [isMounted, setIsMounted] = useState(false)

    useEffect(() => {
        setIsMounted(true)
    }, [])

    const chartData = useMemo(() => {
        if (!volumeData?.data) return []

        // Aggregate data by date (since API returns multiple rows per day for different pairs/directions)
        const aggregatedData = volumeData.data.reduce((acc: any, item: any) => {
            const date = item["Trade Day"]
            if (!acc[date]) {
                acc[date] = {
                    date,
                    volume: 0,
                    trades: 0
                }
            }
            acc[date].volume += item["WRON Volume (USD)"] || 0
            acc[date].trades += item["Number of Trades"] || 0
            return acc
        }, {})

        return Object.values(aggregatedData)
            .sort((a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime())
            .slice(-90)
    }, [volumeData])

    const volumeColumns = [
        {
            key: "Trade Day",
            label: "Trade Day",
            format: (val: string) =>
                new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        },
        { key: "WRON Trade Direction", label: "WRON Trade Direction" },
        { key: "Number of Trades", label: "Number of Trades", format: (val: number) => val.toLocaleString() },
        {
            key: "Number of Unique Traders",
            label: "Number of Unique Traders",
            format: (val: number) => val.toLocaleString(),
        },
        {
            key: "WRON Volume (Tokens)",
            label: "WRON Volume (Tokens)",
            format: (val: number) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 4 }) : "N/A"),
        },
        {
            key: "WRON Volume (USD)",
            label: "WRON Volume (USD)",
            format: (val: number) =>
                val != null ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "N/A",
        },
        {
            key: "Counterparty Token Volume",
            label: "Counterparty Token Volume",
            format: (val: number) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 4 }) : "N/A"),
        },
        { key: "Counterparty Token Symbol", label: "Counterparty Token Symbol" },
        {
            key: "Daily % Share of WRON Volume (by Counterparty Token)",
            label: "Daily % Share of WRON Volume (by Counterparty Token)",
            format: (val: number) => `${val.toFixed(2)}%`,
        },
    ]

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="rounded-lg border border-border bg-card p-3 shadow-sm">
                    <p className="mb-2 font-semibold text-foreground">
                        {new Date(label).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
                            <span className="text-muted-foreground">{entry.name}:</span>
                            <span className="font-mono font-medium text-foreground">
                                {entry.name.includes("Volume")
                                    ? `$${Number(entry.value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                                    : entry.value.toLocaleString()}
                            </span>
                        </div>
                    ))}
                </div>
            )
        }
        return null
    }

    if (isLoading) {
        return (
            <div className="space-y-4">
                <ChartSkeleton />
                <TableSkeleton rows={10} />
            </div>
        )
    }

    if (volumeError) return <div className="text-destructive">Error loading data</div>

    return (
        <div className="space-y-4">
            <Card className="glass-card">
                <CardHeader>
                    <CardTitle>Daily Volume Trends</CardTitle>
                    <CardDescription>
                        Aggregated total WRON trading volume (USD) across all pairs and directions over the last 90 days.
                    </CardDescription>
                    {volumeData?.metadata && (
                        <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                            Last updated: {new Date(volumeData.metadata.last_updated).toLocaleString()} UTC
                        </p>
                    )}
                </CardHeader>
                <CardContent>
                    {isMounted ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="colorVolumeMain" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="hsl(217 91% 60%)" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="hsl(217 91% 60%)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                    minTickGap={30}
                                    tickFormatter={(val) => new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                                />
                                <YAxis
                                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                    tickLine={false}
                                    axisLine={false}
                                    tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                                />
                                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }} />
                                <Area
                                    type="monotone"
                                    dataKey="volume"
                                    name="Volume (USD)"
                                    stroke="hsl(217 91% 60%)"
                                    fill="url(#colorVolumeMain)"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4, strokeWidth: 0 }}
                                    animationDuration={0}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <ChartSkeleton />
                    )}
                </CardContent>
            </Card>

            <Card className="glass-card">
                <CardHeader>
                    <CardTitle>Detailed Volume Data</CardTitle>
                </CardHeader>
                <CardContent>
                    <DataTable columns={volumeColumns} data={volumeData.data} />
                </CardContent>
            </Card>
        </div>
    )
}
