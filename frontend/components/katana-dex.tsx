"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
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
import { ExternalLink } from "lucide-react"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function KatanaDEX() {
  const { data: pairsData, error: pairsError } = useSWR("/api/dune/trade-pairs", fetcher)
  const { data: whalesData, error: whalesError } = useSWR("/api/dune/whales", fetcher)
  const { data: volumeData, error: volumeError } = useSWR("/api/dune/volume-liquidity", fetcher)
  const { data: hourlyData, error: hourlyError } = useSWR("/api/dune/hourly", fetcher)
  const { data: weeklyData, error: weeklyError } = useSWR("/api/dune/weekly-segmentation", fetcher)

  console.log("[v0] Volume Data - Full:", volumeData)
  if (volumeData?.data?.[0]) {
    console.log("[v0] Volume Data - First row keys:", Object.keys(volumeData.data[0]))
    console.log("[v0] Volume Data - First row:", volumeData.data[0])
  }

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

  const hourlyBoughtData = hourlyData?.data
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

  const hourlySoldData = hourlyData?.data
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

  const hourlyTableData = hourlyData?.data
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

  const weeklyCategories = weeklyData?.data
    ? Array.from(new Set(weeklyData.data.map((item: any) => item["Amount Category"])))
    : []

  const weeklyByCategory = weeklyCategories.map((category) => {
    const categoryData = weeklyData.data
      .filter((item: any) => item["Amount Category"] === category)
      .map((item: any) => ({
        week: new Date(item["trade week"]).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        volume: item["USD Volume"],
        users: item["Weekly active users"],
      }))
    return { category, data: categoryData }
  })

  const weeklyTableData = weeklyData?.data
    ? weeklyData.data.map((item: any) => ({
        ...item,
        "Trade Week": new Date(item["trade week"]).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        }),
      }))
    : []

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

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Katana DEX Analytics</h2>

      <Tabs defaultValue="pairs" className="w-full">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto">
          <TabsTrigger value="pairs">Trade Pairs</TabsTrigger>
          <TabsTrigger value="whales">Whales</TabsTrigger>
          <TabsTrigger value="volume">Volume</TabsTrigger>
          <TabsTrigger value="hourly">Hourly</TabsTrigger>
          <TabsTrigger value="weekly">Weekly</TabsTrigger>
        </TabsList>

        <TabsContent value="pairs" className="space-y-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>WRON Active Trade Pairs</CardTitle>
              {pairsData?.metadata && (
                <p className="text-xs text-muted-foreground">
                  Last updated: {new Date(pairsData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {pairsData?.data ? (
                <DataTable columns={pairsColumns} data={pairsData.data} />
              ) : pairsError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <div className="text-muted-foreground">Loading...</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="whales" className="space-y-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>WRON Whale Tracking (Traders who traded over $10k in the last 30 days)</CardTitle>
              {whalesData?.metadata && (
                <p className="text-xs text-muted-foreground">
                  Last updated: {new Date(whalesData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {whalesData?.data ? (
                <DataTable columns={whalesColumns} data={whalesData.data} />
              ) : whalesError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <div className="text-muted-foreground">Loading...</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="volume" className="space-y-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Daily WRON Volume & Liquidity</CardTitle>
              {volumeData?.metadata && (
                <p className="text-xs text-muted-foreground">
                  Last updated: {new Date(volumeData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {volumeData?.data ? (
                <DataTable columns={volumeColumns} data={volumeData.data} />
              ) : volumeError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <div className="text-muted-foreground">Loading...</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hourly" className="space-y-4">
          {hourlyData?.data ? (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle>WRON Bought - Trading Volume & Trades</CardTitle>
                    {hourlyData?.metadata && (
                      <p className="text-xs text-muted-foreground">
                        Last updated: {new Date(hourlyData.metadata.last_updated).toLocaleString()} UTC
                      </p>
                    )}
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={hourlyBoughtData.slice(-30)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="hour" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
                        <YAxis yAxisId="left" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                        <YAxis yAxisId="right" orientation="right" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                            color: "hsl(var(--foreground))",
                          }}
                        />
                        <Legend />
                        <Bar yAxisId="left" dataKey="trades" fill="hsl(217 91% 60%)" name="Trades Count" />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="volume"
                          stroke="hsl(217 91% 75%)"
                          name="Volume (USD)"
                          strokeWidth={2}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle>WRON Sold - Trading Volume & Trades</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={hourlySoldData.slice(-30)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="hour" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
                        <YAxis yAxisId="left" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                        <YAxis yAxisId="right" orientation="right" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                            color: "hsl(var(--foreground))",
                          }}
                        />
                        <Legend />
                        <Bar yAxisId="left" dataKey="trades" fill="hsl(217 91% 60%)" name="Trades Count" />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="volume"
                          stroke="hsl(217 91% 75%)"
                          name="Volume (USD)"
                          strokeWidth={2}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle>WRON Bought - Unique Traders</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={hourlyBoughtData.slice(-30)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="hour" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
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
                          dataKey="traders"
                          stroke="hsl(217 91% 60%)"
                          name="Unique Traders"
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle>WRON Sold - Unique Traders</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={hourlySoldData.slice(-30)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="hour" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
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
                          dataKey="traders"
                          stroke="hsl(217 91% 60%)"
                          name="Unique Traders"
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>

              <Card className="glass-card">
                <CardHeader>
                  <CardTitle>Average Trade Size Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="hour" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
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
                        data={hourlyBoughtData.slice(-30)}
                        type="monotone"
                        dataKey="avgSize"
                        stroke="hsl(217 91% 60%)"
                        name="Bought Avg Size (USD)"
                        strokeWidth={2}
                      />
                      <Line
                        data={hourlySoldData.slice(-30)}
                        type="monotone"
                        dataKey="avgSize"
                        stroke="hsl(217 91% 75%)"
                        name="Sold Avg Size (USD)"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
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
            </>
          ) : hourlyError ? (
            <Card className="glass-card">
              <CardContent className="py-8">
                <div className="text-destructive">Error loading hourly data</div>
              </CardContent>
            </Card>
          ) : (
            <Card className="glass-card">
              <CardContent className="py-8">
                <div className="text-muted-foreground">Loading...</div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="weekly" className="space-y-4">
          {weeklyData?.data ? (
            <>
              {weeklyByCategory.map(({ category, data }) => (
                <Card key={category} className="glass-card">
                  <CardHeader>
                    <CardTitle>{category} - Weekly Trends</CardTitle>
                    {weeklyData?.metadata && (
                      <p className="text-xs text-muted-foreground">
                        Last updated: {new Date(weeklyData.metadata.last_updated).toLocaleString()} UTC
                      </p>
                    )}
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <ComposedChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="week" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                        <YAxis yAxisId="left" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                        <YAxis yAxisId="right" orientation="right" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                            color: "hsl(var(--foreground))",
                          }}
                        />
                        <Legend />
                        <Bar yAxisId="left" dataKey="volume" fill="hsl(217 91% 60%)" name="USD Volume" />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="users"
                          stroke="hsl(217 91% 75%)"
                          name="Active Users"
                          strokeWidth={2}
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              ))}

              <Card className="glass-card">
                <CardHeader>
                  <CardTitle>Complete Weekly Data</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataTable columns={weeklyTableColumns} data={weeklyTableData} />
                </CardContent>
              </Card>
            </>
          ) : weeklyError ? (
            <Card className="glass-card">
              <CardContent className="py-8">
                <div className="text-destructive">Error loading weekly data</div>
              </CardContent>
            </Card>
          ) : (
            <Card className="glass-card">
              <CardContent className="py-8">
                <div className="text-muted-foreground">Loading...</div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </section>
  )
}
