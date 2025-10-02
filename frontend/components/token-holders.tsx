"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DataTable } from "@/components/data-table"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import useSWR from "swr"
import { ExternalLink } from "lucide-react"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function TokenHolders() {
  const { data: holdersData, error: holdersError } = useSWR("/api/dune/holders", fetcher)
  const { data: segmentedData, error: segmentedError } = useSWR("/api/dune/segmented-holders", fetcher)

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
      label: "Balance (RON)",
      format: (val: number) => val.toLocaleString(undefined, { maximumFractionDigits: 2 }),
    },
  ]

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
              <CardTitle>RON Holder Segmentation</CardTitle>
              {segmentedData?.metadata && (
                <p className="text-xs text-muted-foreground">
                  Last updated: {new Date(segmentedData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {segmentedData?.data ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={segmentedData.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="tier" tick={{ fill: "hsl(var(--muted-foreground))" }} />
                    <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        color: "hsl(var(--foreground))",
                      }}
                    />
                    <Bar dataKey="holders" fill="hsl(217 91% 60%)" />
                  </BarChart>
                </ResponsiveContainer>
              ) : segmentedError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <div className="text-muted-foreground">Loading...</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="top-holders" className="space-y-4">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Current RON Holders</CardTitle>
              {holdersData?.metadata && (
                <p className="text-xs text-muted-foreground">
                  Last updated: {new Date(holdersData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {holdersData?.data ? (
                <DataTable columns={holdersColumns} data={holdersData.data} />
              ) : holdersError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <div className="text-muted-foreground">Loading...</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </section>
  )
}
