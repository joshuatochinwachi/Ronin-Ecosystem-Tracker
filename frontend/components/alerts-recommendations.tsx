"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { TrendingUp, AlertTriangle, CheckCircle, Lightbulb } from "lucide-react"

export function AlertsRecommendations() {
  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Alerts & Recommendations</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="glass-card border-l-4 border-l-green-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-500">
              <TrendingUp className="w-5 h-5" />
              Positive Trends
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Alert className="bg-green-500/10 border-green-500/20">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <AlertTitle className="text-green-500">Network Activity Increasing</AlertTitle>
              <AlertDescription className="text-foreground/80">
                Daily active wallets have increased by 15% over the past week, indicating growing ecosystem adoption.
              </AlertDescription>
            </Alert>
            <Alert className="bg-green-500/10 border-green-500/20">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <AlertTitle className="text-green-500">Gaming Volume Strong</AlertTitle>
              <AlertDescription className="text-foreground/80">
                Gaming transactions remain robust with consistent daily player engagement across top titles.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        <Card className="glass-card border-l-4 border-l-yellow-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-500">
              <AlertTriangle className="w-5 h-5" />
              Watch Areas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Alert className="bg-yellow-500/10 border-yellow-500/20">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <AlertTitle className="text-yellow-500">DEX Volume Fluctuation</AlertTitle>
              <AlertDescription className="text-foreground/80">
                Katana DEX trading volume has shown increased volatility. Monitor whale activity for potential impacts.
              </AlertDescription>
            </Alert>
            <Alert className="bg-yellow-500/10 border-yellow-500/20">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <AlertTitle className="text-yellow-500">Gas Price Variability</AlertTitle>
              <AlertDescription className="text-foreground/80">
                Average gas prices have fluctuated. Consider optimizing transaction timing for cost efficiency.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-card border-l-4 border-l-blue-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-500">
            <Lightbulb className="w-5 h-5" />
            Actionable Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-semibold text-foreground flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm">
                1
              </span>
              Optimize Trading Strategy
            </h4>
            <p className="text-muted-foreground ml-8">
              Based on hourly trading patterns, consider executing large trades during off-peak hours (2-6 AM UTC) for
              better liquidity and lower slippage.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-foreground flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm">
                2
              </span>
              Monitor Whale Movements
            </h4>
            <p className="text-muted-foreground ml-8">
              Track the top 10 whale addresses for early signals of market movements. Set up alerts for transactions
              exceeding $50k.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-foreground flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm">
                3
              </span>
              Engage with Growing Games
            </h4>
            <p className="text-muted-foreground ml-8">
              Games showing consistent player retention (7-day+) present partnership opportunities. Focus on titles with
              increasing daily active users.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-foreground flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm">
                4
              </span>
              NFT Collection Analysis
            </h4>
            <p className="text-muted-foreground ml-8">
              Collections with rising floor prices and increasing unique buyers indicate strong community interest.
              Consider these for investment or collaboration.
            </p>
          </div>
        </CardContent>
      </Card>
    </section>
  )
}
