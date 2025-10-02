"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { DataTable } from "@/components/data-table"
import useSWR from "swr"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function NetworkHealth() {
  const { data, error } = useSWR("/api/dune/ronin-daily", fetcher)

  console.log("[v0] Network Health - Data:", data)
  console.log("[v0] Network Health - Error:", error)

  const columns = [
    { key: "date", label: "Date" },
    {
      key: "total_transactions",
      label: "Total Transactions",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "unique_active_wallets",
      label: "Active Wallets",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "total_gas_used_gwei",
      label: "Total Gas (Gwei)",
      format: (val: number) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "N/A"),
    },
    {
      key: "avg_gas_price_gwei",
      label: "Avg Gas Price (Gwei)",
      format: (val: number) => (val != null ? val.toFixed(2) : "N/A"),
    },
  ]

  if (!data?.data) {
    return (
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-foreground">Ronin Network Activity</h2>
        <Card className="glass-card">
          <CardContent className="py-8">
            {error ? (
              <div className="text-destructive">Error loading network data</div>
            ) : (
              <div className="text-muted-foreground">Loading...</div>
            )}
          </CardContent>
        </Card>
      </section>
    )
  }

  const chartData = data.data.slice(-30) // Last 30 days

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Ronin Network Activity</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Daily Network Metrics (Last 30 Days)</CardTitle>
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(data.metadata.last_updated).toLocaleString()}
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  className="text-muted-foreground"
                  tickFormatter={(value) =>
                    new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                  }
                />
                <YAxis className="text-muted-foreground" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="total_transactions"
                  stroke="hsl(var(--chart-1))"
                  name="Transactions"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="unique_active_wallets"
                  stroke="hsl(var(--chart-2))"
                  name="Active Wallets"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
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
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  className="text-muted-foreground"
                  tickFormatter={(value) =>
                    new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                  }
                />
                <YAxis className="text-muted-foreground" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg_gas_price_gwei"
                  stroke="hsl(var(--chart-3))"
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
          <DataTable columns={columns} data={data.data} />
        </CardContent>
      </Card>
    </section>
  )
}
