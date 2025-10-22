"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import useSWR from "swr"
import { ExternalLink } from 'lucide-react'
import { useState } from "react"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function NFTMarketplace() {
  const { data } = useSWR("/api/dune/nft-collections", fetcher)
  const [activeTab, setActiveTab] = useState<"collections" | "summary">("collections")

  const sortedData = data?.data
    ? [...data.data].sort((a: any, b: any) => {
        const aVolume = a.volume_usd ?? 0
        const bVolume = b.volume_usd ?? 0
        return bVolume - aVolume
      })
    : []

  const summaryStats = sortedData.reduce(
    (acc, item) => {
      return {
        totalSalesVolume: acc.totalSalesVolume + (item.volume_usd ?? 0),
        totalCreatorRoyalties: acc.totalCreatorRoyalties + (item.royalty_usd ?? 0),
        totalRoninFees: acc.totalRoninFees + (item.ronin_usd ?? 0),
        totalPlatformFees: acc.totalPlatformFees + (item.platform_usd ?? 0),
        floorPrices: [...acc.floorPrices, item.floor_usd ?? 0],
      }
    },
    {
      totalSalesVolume: 0,
      totalCreatorRoyalties: 0,
      totalRoninFees: 0,
      totalPlatformFees: 0,
      floorPrices: [] as number[],
    }
  )

  const averageFloorPrice =
    summaryStats.floorPrices.length > 0
      ? summaryStats.floorPrices.reduce((a, b) => a + b, 0) / summaryStats.floorPrices.length
      : 0

  const columns = [
    {
      key: "nft_contract_address",
      label: "NFT Collection",
      format: (val: string) => {
        const match = val.match(/0x[a-fA-F0-9]{40}/)
        const address = match ? match[0] : val
        return (
          <a
            href={`https://marketplace.roninchain.com/collections/${address}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:text-primary/80 flex items-center gap-1 font-mono text-sm"
          >
            {address}
            <ExternalLink className="w-3 h-3" />
          </a>
        )
      },
    },
    {
      key: "token_standard",
      label: "Token Standard",
    },
    {
      key: "holders",
      label: "Holders",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "sales",
      label: "Sales",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "floor_usd",
      label: "floor price (USD)",
      format: (val: number) =>
        val != null ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "N/A",
    },
    {
      key: "platform_usd",
      label: "generated platform fees (USD)",
      format: (val: number) =>
        val != null ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "N/A",
    },
    {
      key: "volume_usd",
      label: "sales volume (USD)",
      format: (val: number) =>
        val != null ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "N/A",
    },
    {
      key: "royalty_usd",
      label: "creator royalties (USD)",
      format: (val: number) =>
        val != null ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "N/A",
    },
    {
      key: "ronin_usd",
      label: "generated Ronin fees (USD)",
      format: (val: number) =>
        val != null ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "N/A",
    },
  ]

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-bold text-foreground">NFT Collections Analytics</h2>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>NFT Collections on Sky Mavis Marketplace</CardTitle>
          {data?.metadata && (
            <p className="text-xs text-muted-foreground">
              Last updated: {new Date(data.metadata.last_updated).toLocaleString()} UTC
            </p>
          )}
          <div className="flex gap-2 mt-4 border-b border-border">
            <button
              onClick={() => setActiveTab("collections")}
              className={`px-4 py-2 font-medium text-sm transition-colors ${
                activeTab === "collections"
                  ? "text-primary border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Collections
            </button>
            <button
              onClick={() => setActiveTab("summary")}
              className={`px-4 py-2 font-medium text-sm transition-colors ${
                activeTab === "summary"
                  ? "text-primary border-b-2 border-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Summary Stats
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {activeTab === "collections" ? (
            sortedData.length > 0 ? (
              <DataTable columns={columns} data={sortedData} />
            ) : (
              <div className="text-muted-foreground">Loading...</div>
            )
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <div className="bg-card/50 backdrop-blur-sm border border-border rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-2">Total Sales Volume (USD)</p>
                <p className="text-2xl font-bold text-foreground">
                  ${summaryStats.totalSalesVolume.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-card/50 backdrop-blur-sm border border-border rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-2">Total Creator Royalties (USD)</p>
                <p className="text-2xl font-bold text-foreground">
                  ${summaryStats.totalCreatorRoyalties.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-card/50 backdrop-blur-sm border border-border rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-2">Total Ronin Fees (USD)</p>
                <p className="text-2xl font-bold text-foreground">
                  ${summaryStats.totalRoninFees.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-card/50 backdrop-blur-sm border border-border rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-2">Total Platform Fees (USD)</p>
                <p className="text-2xl font-bold text-foreground">
                  ${summaryStats.totalPlatformFees.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-card/50 backdrop-blur-sm border border-border rounded-lg p-4">
                <p className="text-xs text-muted-foreground mb-2">Average Floor Price (USD)</p>
                <p className="text-2xl font-bold text-foreground">
                  ${averageFloorPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </section>
  )
}
