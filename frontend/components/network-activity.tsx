"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import useSWR from "swr"
import { useState, useEffect, useMemo } from "react"
import { ChartSkeleton, TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function NetworkActivity() {
  const { data } = useSWR("/api/dune/ronin-daily", fetcher)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  const columns = [
    {
      key: "day",
      label: "Date",
      format: (val: string) =>
        new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    },
    {
      key: "daily_transactions",
      label: "Total Transactions",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "active_wallets",
      label: "Active Wallets",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "total_ron_volume_sent",
      label: "Total RON Volume",
      format: (val: number) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "N/A"),
    },
    {
      key: "avg_gas_price_in_gwei",
      label: "Avg Gas Price (Gwei)",
      format: (val: number) => (val != null ? val.toFixed(2) : "N/A"),
    },
  ]

  const chartData = useMemo(() => {
    return data?.data
      ? [...data.data]
        .sort((a: any, b: any) => new Date(a.day).getTime() - new Date(b.day).getTime())
        .map((item: any) => ({
          ...item,
          // Use full date as key to support multi-year data correctly
          date: item.day,
          // Pre-formatted label for tooltip if needed, or rely on formatters
          displayDate: new Date(item.day).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        }))
      : []
  }, [data])

  if (!data) {
    return (
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-foreground">Ronin Network Activity</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartSkeleton />
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
        <TableSkeleton />
      </section>
    )
  }

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

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Ronin Network Activity</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Daily Network Metrics (All Time)</CardTitle>
            {data?.metadata && (
              <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                Last updated: {new Date(data.metadata.last_updated).toLocaleString()} UTC
              </p>
            )}
          </CardHeader>
          <CardContent>
            {isMounted ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorWallets" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(217 91% 60%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(217 91% 60%)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorTx" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(142 71% 45%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(142 71% 45%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(val) => new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={30}
                  />
                  <YAxis
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    content={<CustomTooltip />}
                    labelFormatter={(label) => new Date(label).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="active_wallets"
                    stroke="hsl(217 91% 60%)"
                    fillOpacity={1}
                    fill="url(#colorWallets)"
                    name="Active Wallets"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                    animationDuration={1000}
                  />
                  <Area
                    type="monotone"
                    dataKey="daily_transactions"
                    stroke="hsl(142 71% 45%)"
                    fillOpacity={1}
                    fill="url(#colorTx)"
                    name="Transactions"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                    animationDuration={1000}
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
            <CardTitle>Daily Total RON Volume</CardTitle>
          </CardHeader>
          <CardContent>
            {isMounted ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(280 80% 60%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(280 80% 60%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(val) => new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={30}
                  />
                  <YAxis
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`}
                  />
                  <Tooltip
                    content={<CustomTooltip />}
                    labelFormatter={(label) => new Date(label).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="total_ron_volume_sent"
                    stroke="hsl(280 80% 60%)"
                    fillOpacity={1}
                    fill="url(#colorVolume)"
                    name="Total RON Volume"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                    animationDuration={1000}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <ChartSkeleton />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Gas Usage Trends</CardTitle>
          </CardHeader>
          <CardContent>
            {isMounted ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorGas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(25 90% 60%)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(25 90% 60%)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(val) => new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={30}
                  />
                  <YAxis
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    content={<CustomTooltip />}
                    labelFormatter={(label) => new Date(label).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    cursor={{ stroke: "hsl(var(--muted-foreground))", strokeWidth: 1, strokeDasharray: "4 4" }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="avg_gas_price_in_gwei"
                    stroke="hsl(25 90% 60%)"
                    fillOpacity={1}
                    fill="url(#colorGas)"
                    name="Avg Gas Price (Gwei)"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                    animationDuration={1000}
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
            <CardTitle>Detailed Daily Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.data ? (
              <DataTable columns={columns} data={data.data} pageSize={10} />
            ) : (
              <TableSkeleton />
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
