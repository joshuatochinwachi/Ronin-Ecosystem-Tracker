"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/data-table"
import useSWR from "swr"
import { ExternalLink } from "lucide-react"

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export function NFTMarketplace() {
  const { data } = useSWR("/api/dune/nft-collections", fetcher)

  const sortedData = data?.data
    ? [...data.data].sort((a: any, b: any) => {
        const aVolume = a.volume_usd ?? 0
        const bVolume = b.volume_usd ?? 0
        return bVolume - aVolume
      })
    : []

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
        </CardHeader>
        <CardContent>
          {sortedData.length > 0 ? (
            <DataTable columns={columns} data={sortedData} />
          ) : (
            <div className="text-muted-foreground">Loading...</div>
          )}
        </CardContent>
      </Card>
    </section>
  )
}
