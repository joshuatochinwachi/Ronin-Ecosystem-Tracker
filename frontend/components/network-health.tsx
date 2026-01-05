"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { DataTable } from "@/components/data-table"
import useSWR from "swr"
import { useState, useEffect, useMemo } from "react"
import { ChartSkeleton, TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function NetworkHealth() {
  const { data, error } = useSWR("/api/dune/ronin-daily", fetcher)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  const chartData = useMemo(() => {
    return data?.data
      ? [...data.data]
        .sort((a: any, b: any) => new Date(a.day).getTime() - new Date(b.day).getTime())
        .map((item: any) => ({
          ...item,
          date: item.day, // Map day to date for Recharts
          // Add normalized keys if needed
          total_transactions: item.daily_transactions,
          unique_active_wallets: item.active_wallets,
          avg_gas_price_gwei: item.avg_gas_price_in_gwei
        }))
        .slice(-30) // Slice AFTER sorting
      : []
  }, [data])

  const columns = [
    {
      key: "day", // Changed from date to day to match API
      label: "Date",
      format: (val: string) =>
        new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    },
    {
      key: "daily_transactions", // Mapped from corrected key
      label: "Total Transactions",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "active_wallets", // Mapped from corrected key
      label: "Active Wallets",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "avg_gas_price_in_gwei", // Correct key
      label: "Avg Gas Price (Gwei)",
      format: (val: number) => (val != null ? val.toFixed(2) : "N/A"),
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
                {entry.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
              </span>
            </div>
          ))}
        </div>
      )
    }
    return null
  }

  if (!data?.data) {
    return (
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-foreground">Ronin Network Activity</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
        <TableSkeleton />
      </section>
    )
  }

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Ronin Network Activity</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Daily Network Metrics (Last 30 Days)</CardTitle>
            <p className="text-xs text-muted-foreground" suppressHydrationWarning>
              Last updated: {new Date(data.metadata.last_updated).toLocaleString()}
            </p>
          </CardHeader>
          <CardContent>
            {isMounted ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorTxHealth" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(142 71% 45%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(142 71% 45%)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorWalletsHealth" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(217 91% 60%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(217 91% 60%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) =>
                      new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                    }
                  />
                  <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="total_transactions"
                    stroke="hsl(142 71% 45%)"
                    fillOpacity={1}
                    fill="url(#colorTxHealth)"
                    name="Transactions"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="unique_active_wallets"
                    stroke="hsl(217 91% 60%)"
                    fillOpacity={1}
                    fill="url(#colorWalletsHealth)"
                    name="Active Wallets"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
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
            <CardTitle>Gas Usage Trends</CardTitle>
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(data.metadata.last_updated).toLocaleString()}
            </p>
          </CardHeader>
          <CardContent>
            {isMounted ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorGasHealth" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(25 90% 60%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(25 90% 60%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) =>
                      new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                    }
                  />
                  <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="avg_gas_price_gwei"
                    stroke="hsl(25 90% 60%)"
                    fillOpacity={1}
                    fill="url(#colorGasHealth)"
                    name="Avg Gas Price (Gwei)"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <ChartSkeleton />
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Detailed Daily Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} data={data.data} />
        </CardContent>
      </Card>
    </section>
  )
}
