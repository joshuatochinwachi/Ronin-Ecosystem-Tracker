"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import useSWR from "swr"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function TokenMetrics() {
  const { data } = useSWR("/api/coingecko/ron", fetcher, {
    refreshInterval: 60000,
  })

  console.log("[v0] Token Metrics - Full data:", data)

  if (!data?.data?.market_data) return null

  const marketData = data.data.market_data

  console.log("[v0] Token Metrics - Market data:", marketData)

  // Mock sparkline data for visualization
  const priceData =
    marketData.sparkline_7d?.price?.map((price: number, index: number) => ({
      time: index,
      price: price,
    })) || []

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Detailed Token Metrics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">7-Day Price Trend</CardTitle>
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(data.timestamp).toLocaleString()} UTC
            </p>
          </CardHeader>
          <CardContent>
            {priceData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={priceData}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="time" className="text-muted-foreground" />
                  <YAxis className="text-muted-foreground" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="price"
                    stroke="hsl(var(--chart-1))"
                    fillOpacity={1}
                    fill="url(#colorPrice)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-muted-foreground h-[250px] flex items-center justify-center">
                No sparkline data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">Market Performance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Market Cap</p>
                <p className="text-xl font-bold text-foreground">
                  ${marketData.market_cap?.usd ? (marketData.market_cap.usd / 1e9).toFixed(2) : "N/A"}B
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Fully Diluted Val.</p>
                <p className="text-xl font-bold text-foreground">
                  $
                  {marketData.fully_diluted_valuation?.usd
                    ? (marketData.fully_diluted_valuation.usd / 1e9).toFixed(2)
                    : "N/A"}
                  B
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Circulating Supply</p>
                <p className="text-xl font-bold text-foreground">
                  {marketData.circulating_supply ? (marketData.circulating_supply / 1e9).toFixed(2) : "N/A"}B
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Supply</p>
                <p className="text-xl font-bold text-foreground">
                  {marketData.total_supply ? (marketData.total_supply / 1e9).toFixed(2) : "N/A"}B
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">24h High</p>
                <p className="text-xl font-bold text-green-400">
                  ${marketData.high_24h?.usd ? marketData.high_24h.usd.toFixed(4) : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">24h Low</p>
                <p className="text-xl font-bold text-red-400">
                  ${marketData.low_24h?.usd ? marketData.low_24h.usd.toFixed(4) : "N/A"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
