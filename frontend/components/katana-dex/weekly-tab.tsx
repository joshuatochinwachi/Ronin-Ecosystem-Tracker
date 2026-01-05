"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import {
    Bar,
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

export function KatanaWeeklyTab() {
    const { data: weeklyData, error: weeklyError, isLoading } = useSWR("/api/dune/weekly-segmentation", fetcher)
    const [isMounted, setIsMounted] = useState(false)

    useEffect(() => {
        setIsMounted(true)
    }, [])

    const weeklyCategories = useMemo(() => {
        return weeklyData?.data
            ? Array.from(new Set(weeklyData.data.map((item: any) => item["Amount Category"])))
            : []
    }, [weeklyData])

    const weeklyByCategory = useMemo(() => {
        const order = ["Micro trades", "Small trades", "Medium value trades", "High value trades", "Hyper value trades"]

        return weeklyCategories
            .sort((a: any, b: any) => {
                const indexA = order.indexOf(a)
                const indexB = order.indexOf(b)
                // If both are in the order list, sort by index
                if (indexA !== -1 && indexB !== -1) return indexA - indexB
                // If only A is in list, it comes first
                if (indexA !== -1) return -1
                // If only B is in list, it comes first
                if (indexB !== -1) return 1
                // Otherwise sort alphabetically
                return String(a).localeCompare(String(b))
            })
            .map((category) => {
                const categoryData = weeklyData.data
                    .filter((item: any) => item["Amount Category"] === category)
                    .sort((a: any, b: any) => new Date(a["trade week"]).getTime() - new Date(b["trade week"]).getTime())
                    .map((item: any) => ({
                        week: new Date(item["trade week"]).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
                        volume: item["USD Volume"],
                        users: item["Weekly active users"],
                    }))
                return { category, data: categoryData }
            })
    }, [weeklyData, weeklyCategories])

    const weeklyTableData = useMemo(() => {
        return weeklyData?.data
            ? weeklyData.data.map((item: any) => ({
                ...item,
                "Trade Week": new Date(item["trade week"]).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                }),
            }))
            : []
    }, [weeklyData])

    const weeklyTableColumns = [
        { key: "Trade Week", label: "Trade Week" },
        { key: "Amount Category", label: "Amount Category" },
        {
            key: "USD Volume",
            label: "USD Volume",
            format: (val: number) => `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
        },
        { key: "Weekly active users", label: "Weekly Active Users", format: (val: number) => val.toLocaleString() },
    ]

    if (isLoading) {
        return (
            <div className="space-y-4">
                <ChartSkeleton />
                <ChartSkeleton />
                <TableSkeleton />
            </div>
        )
    }

    if (weeklyError) return <div className="text-destructive">Error loading weekly data</div>

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

    return (
        <div className="space-y-4">
            {weeklyByCategory.map(({ category, data }) => (
                <Card key={category} className="glass-card">
                    <CardHeader>
                        <CardTitle>{category} - Weekly Trends</CardTitle>
                        {weeklyData?.metadata && (
                            <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                                Last updated: {new Date(weeklyData.metadata.last_updated).toLocaleString()} UTC
                            </p>
                        )}
                    </CardHeader>
                    <CardContent>
                        {isMounted ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <ComposedChart data={data}>
                                    <defs>
                                        <linearGradient id={`colorVol-${(category as string).replace(/\s+/g, '-')}`} x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="hsl(217 91% 60%)" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="hsl(217 91% 60%)" stopOpacity={0.2} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                                    <XAxis
                                        dataKey="week"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                        minTickGap={30}
                                    />
                                    <YAxis
                                        yAxisId="left"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                                    />
                                    <YAxis
                                        yAxisId="right"
                                        orientation="right"
                                        tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted)/0.2)" }} />
                                    <Legend />
                                    <Bar
                                        yAxisId="left"
                                        dataKey="volume"
                                        fill={`url(#colorVol-${(category as string).replace(/\s+/g, '-')})`}
                                        name="USD Volume"
                                        animationDuration={0}
                                        radius={[4, 4, 0, 0]}
                                    />
                                    <Line
                                        yAxisId="right"
                                        type="monotone"
                                        dataKey="users"
                                        stroke="hsl(180 100% 50%)"
                                        name="Active Users"
                                        strokeWidth={2}
                                        dot={false}
                                        activeDot={{ r: 4, strokeWidth: 0, fill: "hsl(180 100% 50%)" }}
                                        animationDuration={0}
                                    />
                                </ComposedChart>
                            </ResponsiveContainer>
                        ) : (
                            <ChartSkeleton />
                        )}
                    </CardContent>
                </Card>
            ))}

            <Card className="glass-card">
                <CardHeader>
                    <CardTitle>Complete Weekly Data</CardTitle>
                </CardHeader>
                <CardContent>
                    <DataTable columns={weeklyTableColumns} data={weeklyTableData} pageSize={10} />
                </CardContent>
            </Card>
        </div>
    )
}
