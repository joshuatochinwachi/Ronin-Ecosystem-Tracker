"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DataTable } from "@/components/data-table"
import { RetentionHeatmap } from "@/components/retention-heatmap"
import useSWR from "swr"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState, useMemo } from "react"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function GamingEconomy() {
  const { data: overallData, error: overallError } = useSWR("/api/dune/games-overall", fetcher)
  const { data: dailyData, error: dailyError } = useSWR("/api/dune/games-daily", fetcher)
  const { data: retentionData, error: retentionError } = useSWR("/api/dune/retention", fetcher)
  const [selectedGame, setSelectedGame] = useState<string>("all")

  const overallColumns = [
    { key: "game_project", label: "Game Name" },
    {
      key: "total_volume_ron_sent_to_game",
      label: "Volume (RON) sent to game",
      format: (val: any) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "N/A"),
    },
    {
      key: "unique_players",
      label: "Total Players",
      format: (val: any) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "transaction_count",
      label: "Total Transactions",
      format: (val: any) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "avg_gas_price_in_gwei",
      label: "Avg Gas (Gwei)",
      format: (val: any) => (val != null ? val.toFixed(2) : "N/A"),
    },
  ]

  const dailyColumns = [
    {
      key: "day",
      label: "Date",
      format: (val: string) =>
        new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    },
    { key: "game_project", label: "Game Name" },
    {
      key: "total_volume_ron_sent_to_game",
      label: "Volume (RON) sent to game",
      format: (val: any) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "N/A"),
    },
    {
      key: "unique_players",
      label: "Players",
      format: (val: any) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "transaction_count",
      label: "Transactions",
      format: (val: any) => (val != null ? val.toLocaleString() : "N/A"),
    },
  ]

  const processedRetentionData = useMemo(() => {
    return retentionData?.data
      ? retentionData.data.map((item: any) => ({
        cohort_week: item["cohort week"] ? item["cohort week"].split("T")[0] : "Unknown",
        game_project: item.game_project || "Unknown",
        new_users: item["new users"] || 0,
        week_1: item["% retention 1 week later"] || null,
        week_2: item["% retention 2 weeks later"] || null,
        week_3: item["% retention 3 weeks later"] || null,
        week_4: item["% retention 4 weeks later"] || null,
        week_5: item["% retention 5 weeks later"] || null,
        week_6: item["% retention 6 weeks later"] || null,
        week_7: item["% retention 7 weeks later"] || null,
        week_8: item["% retention 8 weeks later"] || null,
        week_9: item["% retention 9 weeks later"] || null,
        week_10: item["% retention 10 weeks later"] || null,
        week_11: item["% retention 11 weeks later"] || null,
        week_12: item["% retention 12 weeks later"] || null,
      }))
      : []
  }, [retentionData])

  const uniqueGames = useMemo(() => {
    const games = new Set(processedRetentionData.map((item: any) => item.game_project))
    return Array.from(games).sort()
  }, [processedRetentionData])

  const filteredRetentionData = useMemo(() => {
    if (selectedGame === "all") return processedRetentionData
    return processedRetentionData.filter((item: any) => item.game_project === selectedGame)
  }, [processedRetentionData, selectedGame])

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Gaming Economy Dashboard</h2>

      <Tabs defaultValue="overall" className="w-full">
        {/* ... existing tabs list ... */}
        <TabsList className="grid w-full grid-cols-3 lg:w-auto">
          <TabsTrigger value="overall">Overall Activity</TabsTrigger>
          <TabsTrigger value="daily">Daily Activity</TabsTrigger>
          <TabsTrigger value="retention">User Retention</TabsTrigger>
        </TabsList>

        {/* ... existing tabs content ... */}
        <TabsContent value="overall" className="space-y-4">
          {/* ... existing content ... */}
          <Card className="glass-card">
            <CardHeader>
              <CardTitle>Games Overall Activity</CardTitle>
              {overallData?.metadata && (
                <p className="text-xs text-muted-foreground">
                  Last updated: {new Date(overallData.metadata.last_updated).toLocaleString()} UTC
                </p>
              )}
            </CardHeader>
            <CardContent>
              {overallData?.data ? (
                <DataTable columns={overallColumns} data={overallData.data} />
              ) : overallError ? (
                <div className="text-destructive">Error loading data</div>
              ) : (
                <div className="text-muted-foreground">Loading...</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="daily" className="space-y-4">
          {/* ... existing content ... */}
          {dailyData?.data ? (
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>Detailed Daily Data</CardTitle>
                {dailyData?.metadata && (
                  <p className="text-xs text-muted-foreground">
                    Last updated: {new Date(dailyData.metadata.last_updated).toLocaleString()} UTC
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <DataTable columns={dailyColumns} data={dailyData.data} />
              </CardContent>
            </Card>
          ) : dailyError ? (
            <Card className="glass-card">
              <CardContent className="py-8">
                <div className="text-destructive">Error loading daily activity data</div>
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

        <TabsContent value="retention" className="space-y-4">
          <Card className="glass-card">
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle>User Activation & Retention Cohort Analysis</CardTitle>
                  <CardDescription className="text-sm text-muted-foreground mt-2">
                    This analyzes weekly user activation and retention across these Ronin games.
                  </CardDescription>
                  {retentionData?.metadata && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Last updated: {new Date(retentionData.metadata.last_updated).toLocaleString()} UTC
                    </p>
                  )}
                </div>
                <div className="w-[200px]">
                  <Select value={selectedGame} onValueChange={setSelectedGame}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select Game" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Games</SelectItem>
                      {uniqueGames.map((game: any) => (
                        <SelectItem key={game} value={game}>
                          {game}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {retentionData?.data ? (
                <RetentionHeatmap data={filteredRetentionData} />
              ) : retentionError ? (
                <div className="text-destructive">Error loading retention data</div>
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
