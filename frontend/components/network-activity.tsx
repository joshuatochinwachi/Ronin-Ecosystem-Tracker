"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import useSWR from "swr"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function NetworkActivity() {
  const { data } = useSWR("/api/dune/ronin-daily", fetcher)

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

  if (!data) return null

  const chartData = data.data.map((item: any) => ({
    ...item,
    date: new Date(item.day).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }))

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Ronin Network Activity</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Daily Network Metrics (All Time)</CardTitle>
            {data?.metadata && (
              <p className="text-xs text-muted-foreground">
                Last updated: {new Date(data.metadata.last_updated).toLocaleString()} UTC
              </p>
            )}
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    color: "hsl(var(--foreground))",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="active_wallets"
                  stroke="hsl(217 91% 60%)"
                  name="Active Wallets"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="daily_transactions"
                  stroke="hsl(217 91% 75%)"
                  name="Transactions"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Daily Total RON Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    color: "hsl(var(--foreground))",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="total_ron_volume_sent"
                  stroke="hsl(217 91% 60%)"
                  name="Total RON Volume"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Gas Usage Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    color: "hsl(var(--foreground))",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg_gas_price_in_gwei"
                  stroke="hsl(217 91% 60%)"
                  name="Avg Gas Price (Gwei)"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Detailed Daily Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          {data?.data ? (
            <DataTable columns={columns} data={data.data} />
          ) : (
            <div className="text-muted-foreground">Loading...</div>
          )}
        </CardContent>
      </Card>
    </section>
  )
}
