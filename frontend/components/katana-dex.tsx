"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { KatanaPairsTab } from "@/components/katana-dex/pairs-tab"
import { KatanaWhalesTab } from "@/components/katana-dex/whales-tab"
import { KatanaVolumeTab } from "@/components/katana-dex/volume-tab"
import { KatanaHourlyTab } from "@/components/katana-dex/hourly-tab"
import { KatanaWeeklyTab } from "@/components/katana-dex/weekly-tab"

import { useState } from "react"

export function KatanaDEX() {
  const [activeTab, setActiveTab] = useState("pairs")

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">Katana DEX Analytics</h2>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto">
          <TabsTrigger value="pairs">Trade Pairs</TabsTrigger>
          <TabsTrigger value="whales">Whales</TabsTrigger>
          <TabsTrigger value="volume">Volume</TabsTrigger>
          <TabsTrigger value="hourly">Hourly</TabsTrigger>
          <TabsTrigger value="weekly">Weekly</TabsTrigger>
        </TabsList>

        {/* Keep all tabs mounted but control visibility with CSS for instant switching */}
        <div className={activeTab === "pairs" ? "block space-y-4" : "hidden"}>
          <KatanaPairsTab />
        </div>

        <div className={activeTab === "whales" ? "block space-y-4" : "hidden"}>
          <KatanaWhalesTab />
        </div>

        <div className={activeTab === "volume" ? "block space-y-4" : "hidden"}>
          <KatanaVolumeTab />
        </div>

        <div className={activeTab === "hourly" ? "block space-y-4" : "hidden"}>
          <KatanaHourlyTab />
        </div>

        <div className={activeTab === "weekly" ? "block space-y-4" : "hidden"}>
          <KatanaWeeklyTab />
        </div>
      </Tabs>
    </section>
  )
}
