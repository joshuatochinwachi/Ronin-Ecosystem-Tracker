"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import useSWR from "swr"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function NFTCollections() {
  const { data, error } = useSWR("/api/dune/nft-collections", fetcher)

  console.log("[v0] NFT Collections - Data:", data)
  console.log("[v0] NFT Collections - Error:", error)

  const columns = [
    { key: "collection_name", label: "Collection Name" },
    {
      key: "floor_price_ron",
      label: "Floor Price (RON)",
      format: (val: number) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 4 }) : "N/A"),
    },
    {
      key: "total_volume_ron",
      label: "Total Volume (RON)",
      format: (val: number) => (val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "N/A"),
    },
    { key: "total_sales", label: "Total Sales", format: (val: number) => (val != null ? val.toLocaleString() : "N/A") },
    {
      key: "unique_buyers",
      label: "Unique Buyers",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
    },
    {
      key: "unique_sellers",
      label: "Unique Sellers",
      format: (val: number) => (val != null ? val.toLocaleString() : "N/A"),
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
              Last updated: {new Date(data.metadata.last_updated).toLocaleString()}
            </p>
          )}
        </CardHeader>
        <CardContent>
          {data?.data ? (
            <DataTable columns={columns} data={data.data} />
          ) : error ? (
            <div className="text-destructive">Error loading NFT collections data</div>
          ) : (
            <div className="text-muted-foreground">Loading...</div>
          )}
        </CardContent>
      </Card>
    </section>
  )
}
