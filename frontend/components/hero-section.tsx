"use client"

import { Card, CardContent } from "@/components/ui/card"
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Activity, Smile } from "lucide-react"
import useSWR from "swr"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function HeroSection() {
  const { data, error } = useSWR("/api/coingecko/ron", fetcher, {
    refreshInterval: 60000,
  })

  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="p-6">
          <div className="text-destructive">Failed to load RON market data</div>
        </CardContent>
      </Card>
    )
  }
  if (!data) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-muted-foreground">Loading market data...</div>
        </CardContent>
      </Card>
    )
  }

  const ronData = data.data?.[0] || {}
  const marketData = ronData.market_data || {}
  const priceChange = marketData.price_change_percentage_24h || 0
  const isPositive = priceChange >= 0
  const lastUpdated = data.metadata?.last_updated || new Date().toISOString()

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-foreground">RON Token Health Overview</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Last updated: {new Date(lastUpdated).toLocaleString()} UTC
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <Card className="border-blue-500/30 bg-blue-500/5">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">RON Price</span>
              <DollarSign className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">
              ${marketData.current_price?.usd?.toFixed(4) || "0.0000"}
            </div>
            <div className={`flex items-center gap-1 mt-2 text-sm ${isPositive ? "text-green-500" : "text-red-500"}`}>
              {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {Math.abs(priceChange).toFixed(2)}%
            </div>
          </CardContent>
        </Card>

        <Card className="border-purple-500/30 bg-purple-500/5">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Market Cap Rank</span>
              <BarChart3 className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">#{marketData.market_cap_rank || "N/A"}</div>
            <div className="text-sm text-muted-foreground mt-2">
              ${((marketData.market_cap?.usd || 0) / 1e9).toFixed(2)}B
            </div>
          </CardContent>
        </Card>

        <Card className="border-cyan-500/30 bg-cyan-500/5">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">24h Volume</span>
              <Activity className="w-4 h-4 text-cyan-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">
              ${((marketData.total_volume?.usd || 0) / 1e6).toFixed(2)}M
            </div>
            <div className="text-sm text-muted-foreground mt-2">
              Vol/MCap: {(((marketData.total_volume?.usd || 0) / (marketData.market_cap?.usd || 1)) * 100).toFixed(2)}%
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-500/30 bg-green-500/5">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">ATH</span>
              <TrendingUp className="w-4 h-4 text-green-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">${marketData.ath?.usd?.toFixed(4) || "0.0000"}</div>
            <div className="text-sm text-red-500 mt-2">
              {marketData.ath_change_percentage?.usd?.toFixed(2) || "0"}% from ATH
            </div>
          </CardContent>
        </Card>

        <Card className="border-orange-500/30 bg-orange-500/5">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">ATL</span>
              <TrendingDown className="w-4 h-4 text-orange-500" />
            </div>
            <div className="text-2xl font-bold text-foreground">${marketData.atl?.usd?.toFixed(4) || "0.0000"}</div>
            <div className="text-sm text-green-500 mt-2">
              +{marketData.atl_change_percentage?.usd?.toFixed(2) || "0"}% from ATL
            </div>
          </CardContent>
        </Card>

        <Card className="border-pink-500/30 bg-pink-500/5">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Sentiment</span>
              <Smile className="w-4 h-4 text-pink-500" />
            </div>
            <div className="text-2xl font-bold text-green-500">
              {ronData.sentiment_votes_up_percentage?.toFixed(0) || "0"}%
            </div>
            <div className="text-sm text-muted-foreground mt-2">Community Bullish</div>
          </CardContent>
        </Card>
      </div>
    </section>
  )
}
