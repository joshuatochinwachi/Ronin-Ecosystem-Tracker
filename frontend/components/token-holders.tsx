"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DataTable } from "@/components/data-table"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import useSWR from "swr"
import { ExternalLink } from "lucide-react"
import { useState, useEffect } from "react"
import { ChartSkeleton, TableSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function TokenHolders() {
  const { data: holdersData, error: holdersError } = useSWR("/api/dune/holders", fetcher)
  const { data: segmentedData, error: segmentedError } = useSWR("/api/dune/segmented-holders", fetcher)

  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  const holdersColumns = [
    {
      key: "wallet",
      label: "Wallet Address",
      format: (val: string) => (
        <a
          href={`https://app.roninchain.com/address/${val}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:text-primary/80 flex items-center gap-1"
        >
          {val.slice(0, 8)}...{val.slice(-6)}
          <ExternalLink className="w-3 h-3" />
        </a>
      ),
    },
    {
      key: "current $RON balance",
      label: "Balance (RON/WRON)",
      format: (val: number) => val.toLocaleString(undefined, { maximumFractionDigits: 2 }),
    },
  ]

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
                {Number(entry.value).toLocaleString()}
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
      <h2 className="text-2xl font-bold text-foreground">Token Holder Intelligence</h2>

      <Tabs defaultValue="distribution" className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:w-auto">
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
          <TabsTrigger value="top-holders">Current Holders</TabsTrigger>
        </TabsList>

        <TabsContent value="distribution" className="space-y-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>RON/WRON Holder Segmentation</CardTitle>
              {segmentedData?.metadata && (
                <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                  Last updated: {new Date(segmentedData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {segmentedData?.data && isMounted ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={segmentedData.data}>
                    <defs>
                      <linearGradient id="colorHolders" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(217 91% 60%)" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="hsl(217 91% 60%)" stopOpacity={0.2} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis
                      dataKey="tier"
                      tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(var(--muted)/0.2)" }} />
                    <Bar
                      dataKey="holders"
                      name="Holders Count"
                      fill="url(#colorHolders)"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : !segmentedData?.data && isMounted ? (
                <ChartSkeleton height={400} />
              ) : segmentedError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <ChartSkeleton height={400} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="top-holders" className="space-y-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Current RON/WRON Holders</CardTitle>
              {holdersData?.metadata && (
                <p className="text-xs text-muted-foreground" suppressHydrationWarning>
                  Last updated: {new Date(holdersData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {holdersData?.data ? (
                <DataTable columns={holdersColumns} data={holdersData.data} pageSize={10} />
              ) : holdersError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <TableSkeleton />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </section>
  )
}
