"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import useSWR from "swr"
import { useState, useEffect, useMemo } from "react"
import { ChartSkeleton, MetricCardSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function TokenMetrics() {
  const { data } = useSWR("/api/coingecko/ron", fetcher, {
    refreshInterval: 60000,
  })

  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  if (!data?.data?.[0]?.market_data) {
    return (
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-foreground">Detailed Token Metrics</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <MetricCardSkeleton />
          <MetricCardSkeleton />
        </div>
      </section>
    )
  }

  const marketData = data.data[0].market_data

  const getPriceChangeColor = (change: number) => {
    if (change > 0) return "text-green-400"
    if (change < 0) return "text-red-400"
    return "text-muted-foreground"
  }

  const formatPriceChange = (change: number) => {
    const sign = change > 0 ? "+" : ""
    return `${sign}${change.toFixed(2)}%`
  }

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Detailed Token Metrics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="text-lg">Price Performance</CardTitle>
            <p className="text-xs text-muted-foreground" suppressHydrationWarning>
              Last updated: {new Date(data.metadata?.last_updated).toLocaleString()} UTC
            </p>
          </CardHeader>
          <CardContent>
            {isMounted ? (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground mb-2">24 Hours</p>
                    <p className={`text-2xl font-bold ${getPriceChangeColor(marketData.price_change_percentage_24h)}`}>
                      {formatPriceChange(marketData.price_change_percentage_24h)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground mb-2">7 Days</p>
                    <p className={`text-2xl font-bold ${getPriceChangeColor(marketData.price_change_percentage_7d)}`}>
                      {formatPriceChange(marketData.price_change_percentage_7d)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground mb-2">30 Days</p>
                    <p className={`text-2xl font-bold ${getPriceChangeColor(marketData.price_change_percentage_30d)}`}>
                      {formatPriceChange(marketData.price_change_percentage_30d)}
                    </p>
                  </div>
                </div>
                <div className="pt-4 border-t border-border">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Current Price</p>
                      <p className="text-lg font-semibold text-foreground">
                        ${marketData.current_price?.usd?.toFixed(4) || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">24h Change</p>
                      <p className="text-lg font-semibold text-foreground">
                        ${marketData.price_change_24h?.toFixed(6) || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">24h High</p>
                      <p className="text-sm font-medium text-green-400">
                        ${marketData.high_24h?.usd?.toFixed(4) || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">24h Low</p>
                      <p className="text-sm font-medium text-red-400">
                        ${marketData.low_24h?.usd?.toFixed(4) || "N/A"}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <ChartSkeleton height={250} />
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
