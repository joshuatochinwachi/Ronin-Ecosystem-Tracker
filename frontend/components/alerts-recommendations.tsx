"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { TrendingUp, AlertTriangle, CheckCircle, Lightbulb, TrendingDown, Activity } from "lucide-react"
import useSWR from "swr"
import { useMemo } from "react"
import { ChartSkeleton } from "@/components/skeletons"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function AlertsRecommendations() {
  const { data: networkData, isLoading: networkLoading } = useSWR("/api/dune/network-activity", fetcher)
  const { data: volumeData, isLoading: volumeLoading } = useSWR("/api/dune/volume-liquidity", fetcher)
  const { data: gamesData, isLoading: gamesLoading } = useSWR("/api/dune/games-daily", fetcher)

  const analysis = useMemo(() => {
    const result = {
      walletGrowth: 0,
      volumeChange: 0,
      topGame: null as any,
      gasStatus: 'low',
      gasPrice: 0,
      hasNetworkData: false,
      hasVolumeData: false,
      hasGameData: false
    }

    // 1. Network Trend Analysis
    if (networkData?.data?.length >= 2) {
      const sortedNetwork = [...networkData.data].sort((a: any, b: any) => new Date(a.day).getTime() - new Date(b.day).getTime())
      const currentNetwork = sortedNetwork[sortedNetwork.length - 1]
      const prevNetwork = sortedNetwork[sortedNetwork.length - 2]

      if (currentNetwork && prevNetwork) {
        result.walletGrowth = ((currentNetwork.active_wallets - prevNetwork.active_wallets) / prevNetwork.active_wallets) * 100
        result.hasNetworkData = true
        result.gasPrice = currentNetwork.avg_gas_price || 0
        result.gasStatus = result.gasPrice > 50 ? "high" : "low"
      }
    }

    // 2. Volume Analysis
    if (volumeData?.data?.length >= 7) {
      const last7DaysVolume = volumeData.data.slice(-7)
      const avgVolume = last7DaysVolume.reduce((acc: number, curr: any) => acc + (curr["WRON Volume (USD)"] || 0), 0) / last7DaysVolume.length
      const currentVolume = last7DaysVolume[last7DaysVolume.length - 1]["WRON Volume (USD)"] || 0

      if (avgVolume > 0) {
        result.volumeChange = ((currentVolume - avgVolume) / avgVolume) * 100
        result.hasVolumeData = true
      }
    }

    // 3. Gaming Analysis
    if (gamesData?.data?.length > 0) {
      const lastDayData = gamesData.data[gamesData.data.length - 1]
      // Filter for games from the latest day
      const currentGames = gamesData.data.filter((g: any) => g.day === lastDayData.day)
      if (currentGames.length > 0) {
        result.topGame = currentGames.sort((a: any, b: any) => b.unique_players - a.unique_players)[0]
        result.hasGameData = true
      }
    }

    return result
  }, [networkData, volumeData, gamesData])

  if (networkLoading || volumeLoading || gamesLoading) {
    return (
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-foreground">Alerts & Recommendations</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
        <ChartSkeleton />
      </section>
    )
  }

  const alerts = []
  const watchAreas = []
  const recommendations = []

  // Generate Dynamic Content
  if (analysis) {
    // Alert 1: Network Growth
    if (analysis.hasNetworkData) {
      if (analysis.walletGrowth > 0) {
        alerts.push({
          title: "Network Activity Increasing",
          desc: `Active wallets are up ${analysis.walletGrowth.toFixed(1)}% compared to yesterday, showing healthy ecosystem growth.`,
          icon: TrendingUp
        })
      } else {
        watchAreas.push({
          title: "Network Activity Cooling",
          desc: `Active wallets slight dip of ${Math.abs(analysis.walletGrowth).toFixed(1)}%. Monitor for sustained trend.`,
          icon: TrendingDown
        })
      }
    }

    // Alert 2: Volume
    if (analysis.hasVolumeData) {
      if (analysis.volumeChange > 20) {
        alerts.push({
          title: "Surge in DEX Volume",
          desc: `Trading volume is ${analysis.volumeChange.toFixed(0)}% above the 7-day average. High liquidity usage detected.`,
          icon: Activity
        })
      } else if (analysis.volumeChange < -20) {
        watchAreas.push({
          title: "DEX Volume Low",
          desc: `Trading volume is ${Math.abs(analysis.volumeChange).toFixed(0)}% below 7-day average. Liquidity may be thinner than usual.`,
          icon: AlertTriangle
        })
      } else {
        alerts.push({
          title: "Stable DEX Volume",
          desc: "Trading volume remains consistent with weekly averages.",
          icon: CheckCircle
        })
      }
    }

    // Recommendations
    // Rec 1: Trading (Depends on Network Data for Gas)
    if (analysis.hasNetworkData) {
      // Add to Positive Trends if gas is low
      if (analysis.gasStatus === 'low') {
        alerts.push({
          title: "Gas Fees Optimized",
          desc: `Network fees are efficient (~${analysis.gasPrice.toFixed(4)} Gwei), reducing transaction costs.`,
          icon: CheckCircle
        })

        recommendations.push({
          title: "Optimal Time for Transactions",
          desc: `Gas costs are minimal. Ideal time for complex contract interactions.`
        })
      } else {
        recommendations.push({
          title: "Wait for Gas to Cooldown",
          desc: `Gas prices are elevated (~${analysis.gasPrice.toFixed(2)} Gwei). Consider delaying non-urgent transactions.`
        })
      }
    }

    // Rec 2: Gaming
    if (analysis.hasGameData && analysis.topGame) {
      // Also add to Positive Trends as a "Highlight"
      alerts.push({
        title: `Strong Engagement in ${analysis.topGame.game_project}`,
        desc: `${analysis.topGame.game_project} leads with ${analysis.topGame.unique_players.toLocaleString()} active users today.`,
        icon: TrendingUp
      })

      recommendations.push({
        title: `Engage with ${analysis.topGame.game_project}`,
        desc: `Join the active community in ${analysis.topGame.game_project}, currently the top driver of ecosystem activity.`
      })
    }

    // Rec 3: Whale Watch
    recommendations.push({
      title: "Monitor Whale Movements",
      desc: "Track top 10 whale addresses. Recent large volume spikes suggest potential accumulation phases."
    })
  }

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Alerts & Recommendations</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Positive Trends / Alerts */}
        <Card className="glass-card border-l-4 border-l-green-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-500">
              <TrendingUp className="w-5 h-5" />
              Positive Trends
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alerts.length > 0 ? (
              alerts.map((alert, i) => (
                <Alert key={i} className="bg-green-500/10 border-green-500/20">
                  <alert.icon className="h-4 w-4 text-green-500" />
                  <AlertTitle className="text-green-500">{alert.title}</AlertTitle>
                  <AlertDescription className="text-foreground/80">
                    {alert.desc}
                  </AlertDescription>
                </Alert>
              ))
            ) : (
              <p className="text-muted-foreground text-sm">No significant positive trends detected right now.</p>
            )}
          </CardContent>
        </Card>

        {/* Watch Areas */}
        <Card className="glass-card border-l-4 border-l-yellow-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-500">
              <AlertTriangle className="w-5 h-5" />
              Watch Areas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {watchAreas.length > 0 ? (
              watchAreas.map((item, i) => (
                <Alert key={i} className="bg-yellow-500/10 border-yellow-500/20">
                  <item.icon className="h-4 w-4 text-yellow-500" />
                  <AlertTitle className="text-yellow-500">{item.title}</AlertTitle>
                  <AlertDescription className="text-foreground/80">
                    {item.desc}
                  </AlertDescription>
                </Alert>
              ))
            ) : (
              <Alert className="bg-green-500/10 border-green-500/20">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <AlertTitle className="text-green-500">All Systems Nominal</AlertTitle>
                <AlertDescription className="text-foreground/80">
                  No critical watch areas detected. Ecosystem is stable.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actionable Recommendations */}
      <Card className="glass-card border-l-4 border-l-blue-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-500">
            <Lightbulb className="w-5 h-5" />
            Actionable Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {recommendations.map((rec, i) => (
            <div key={i} className="space-y-2">
              <h4 className="font-semibold text-foreground flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm">
                  {i + 1}
                </span>
                {rec.title}
              </h4>
              <p className="text-muted-foreground ml-8">
                {rec.desc}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    </section>
  )
}
