"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import {
    Bar,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    ComposedChart,
} from "recharts"
import useSWR from "swr"
import { useState, useEffect, useMemo } from "react"
import { ChartSkeleton, TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function KatanaHourlyTab() {
    const { data: hourlyData, error: hourlyError, isLoading } = useSWR("/api/dune/hourly", fetcher)
    const [isMounted, setIsMounted] = useState(false)

    useEffect(() => {
        setIsMounted(true)
    }, [])

    const hourlyBoughtData = useMemo(() => {
        return hourlyData?.data
            ? hourlyData.data
                .filter((item: any) => item.direction === "WRON Bought")
                .map((item: any) => {
                    const date = new Date(item["hour of the day (UTC)"])
                    return {
                        hour: `${date.toLocaleDateString("en-US", { month: "short", day: "numeric" })} ${date.getHours()}:00`,
                        trades: item["trades count"],
                        volume: item["trade volume (USD)"],
                        traders: item["unique traders"],
                        avgSize: item["avg trade size (USD)"],
                    }
                })
            : []
    }, [hourlyData])

    const hourlySoldData = useMemo(() => {
        return hourlyData?.data
            ? hourlyData.data
                .filter((item: any) => item.direction === "WRON Sold")
                .map((item: any) => {
                    const date = new Date(item["hour of the day (UTC)"])
                    return {
                        hour: `${date.toLocaleDateString("en-US", { month: "short", day: "numeric" })} ${date.getHours()}:00`,
                        trades: item["trades count"],
                        volume: item["trade volume (USD)"],
                        traders: item["unique traders"],
                        avgSize: item["avg trade size (USD)"],
                    }
                })
            : []
    }, [hourlyData])

    const hourlyTableData = useMemo(() => {
        return hourlyData?.data
            ? hourlyData.data
                .map((item: any) => {
                    const date = new Date(item["hour of the day (UTC)"])
                    return {
                        ...item,
                        "Date and Hour": `${date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })} ${date.getHours()}:00`,
                        sortKey: date.getTime(),
                    }
                })
                .sort((a: any, b: any) => b.sortKey - a.sortKey)
            : []
    }, [hourlyData])

    const hourlyTableColumns = [
        { key: "Date and Hour", label: "Date and Hour" },
        { key: "direction", label: "Direction" },
        { key: "trades count", label: "Trades", format: (val: number) => val.toLocaleString() },
        {
            key: "trade volume (USD)",
            label: "Volume (USD)",
            format: (val: number) => `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
        },
        { key: "unique traders", label: "Unique Traders", format: (val: number) => val.toLocaleString() },
        {
            key: "avg trade size (USD)",
            label: "Avg Trade Size (USD)",
            format: (val: number) => `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
        },
    ]

    if (isLoading) {
        return (
            <div className="space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <ChartSkeleton />
                    <ChartSkeleton />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <ChartSkeleton />
                    <ChartSkeleton />
                </div>
                <ChartSkeleton />
                <TableSkeleton />
            </div>
        )
    }

    if (hourlyError) return <div className="text-destructive">Error loading hourly data</div>

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="rounded-lg border border-border bg-card p-3 shadow-sm">
                    <p className="mb-2 font-semibold text-foreground">{label}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                            <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
                            <span className="text-muted-foreground">{entry.name}:</span>
                            <span className="font-mono font-medium text-foreground">
                                {entry.name.toLowerCase().includes("trades") || entry.name.toLowerCase().includes("traders")
                                    ? entry.value.toLocaleString()
                                    : `$${Number(entry.value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                                }
                            </span>
                        </div>
                    ))}
                </div>
            )
        }
        return null
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle>WRON Bought - Trading Volume & Trades</CardTitle>
                        {hourlyData?.metadata && (
                            <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                                Last updated: {new Date(hourlyData.metadata.last_updated).toLocaleString()} UTC
                            </p>
                        )}
                    </CardHeader>
                    <CardContent>
                        {isMounted ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <ComposedChart data={hourlyBoughtData.slice(-30)}>
                                    <defs>
                                        <linearGradient id="colorTrades" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="hsl(217 91% 60%)" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="hsl(217 91% 60%)" stopOpacity={0.2} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                    <XAxis
                                        dataKey="hour"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        yAxisId="left"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        yAxisId="right"
                                        orientation="right"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                                    />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted)/0.2)" }} />
                                    <Legend />
                                    <Bar
                                        yAxisId="left"
                                        dataKey="trades"
                                        fill="url(#colorTrades)"
                                        name="Trades Count"
                                        animationDuration={0}
                                        radius={[4, 4, 0, 0]}
                                    />
                                    <Line
                                        yAxisId="right"
                                        type="monotone"
                                        dataKey="volume"
                                        stroke="hsl(25 90% 60%)"
                                        name="Volume (USD)"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, strokeWidth: 0, fill: "hsl(25 90% 60%)" }}
                                        animationDuration={0}
                                    />
                                </ComposedChart>
                            </ResponsiveContainer>
                        ) : (
                            <ChartSkeleton />
                        )}
                    </CardContent>
                </Card>

                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle>WRON Sold - Trading Volume & Trades</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {isMounted ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <ComposedChart data={hourlySoldData.slice(-30)}>
                                    <defs>
                                        <linearGradient id="colorTradesSold" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="hsl(339 90% 60%)" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="hsl(339 90% 60%)" stopOpacity={0.2} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                    <XAxis
                                        dataKey="hour"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        yAxisId="left"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        yAxisId="right"
                                        orientation="right"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                                    />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted)/0.2)" }} />
                                    <Legend />
                                    <Bar
                                        yAxisId="left"
                                        dataKey="trades"
                                        fill="url(#colorTradesSold)"
                                        name="Trades Count"
                                        animationDuration={0}
                                        radius={[4, 4, 0, 0]}
                                    />
                                    <Line
                                        yAxisId="right"
                                        type="monotone"
                                        dataKey="volume"
                                        stroke="hsl(217 91% 75%)"
                                        name="Volume (USD)"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, strokeWidth: 0, fill: "hsl(217 91% 75%)" }}
                                        animationDuration={0}
                                    />
                                </ComposedChart>
                            </ResponsiveContainer>
                        ) : (
                            <ChartSkeleton />
                        )}
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle>WRON Bought - Unique Traders</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {isMounted ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={hourlyBoughtData.slice(-30)}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                    <XAxis
                                        dataKey="hour"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }} />
                                    <Legend />
                                    <Line
                                        type="monotone"
                                        dataKey="traders"
                                        stroke="hsl(217 91% 60%)"
                                        name="Unique Traders"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, strokeWidth: 0, fill: "hsl(217 91% 60%)" }}
                                        animationDuration={0}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <ChartSkeleton />
                        )}
                    </CardContent>
                </Card>

                <Card className="glass-card">
                    <CardHeader>
                        <CardTitle>WRON Sold - Unique Traders</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {isMounted ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={hourlySoldData.slice(-30)}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                    <XAxis
                                        dataKey="hour"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }} />
                                    <Legend />
                                    <Line
                                        type="monotone"
                                        dataKey="traders"
                                        stroke="hsl(339 90% 60%)"
                                        name="Unique Traders"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, strokeWidth: 0, fill: "hsl(339 90% 60%)" }}
                                        animationDuration={0}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <ChartSkeleton />
                        )}
                    </CardContent>
                </Card>
            </div>

            <Card className="glass-card">
                <CardHeader>
                    <CardTitle>Average Trade Size Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                    {isMounted ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart>
                                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                <XAxis dataKey="hour" xAxisId={0} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} allowDuplicatedCategory={false} tickLine={false} axisLine={false} />
                                <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                                <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }} />
                                <Legend />
                                <Line
                                    data={hourlyBoughtData.slice(-30)}
                                    type="monotone"
                                    dataKey="avgSize"
                                    stroke="hsl(217 91% 60%)"
                                    name="Bought Avg Size (USD)"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4, strokeWidth: 0, fill: "hsl(217 91% 60%)" }}
                                    animationDuration={0}
                                />
                                <Line
                                    data={hourlySoldData.slice(-30)}
                                    type="monotone"
                                    dataKey="avgSize"
                                    stroke="hsl(339 90% 60%)"
                                    name="Sold Avg Size (USD)"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 4, strokeWidth: 0, fill: "hsl(339 90% 60%)" }}
                                    animationDuration={0}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <ChartSkeleton />
                    )}
                </CardContent>
            </Card>

            <Card className="glass-card">
                <CardHeader>
                    <CardTitle>Complete Hourly Data</CardTitle>
                </CardHeader>
                <CardContent>
                    <DataTable columns={hourlyTableColumns} data={hourlyTableData} />
                </CardContent>
            </Card>
        </div>
    )
}
