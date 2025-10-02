import { HeroSection } from "@/components/hero-section"
import { TokenMetrics } from "@/components/token-metrics"
import { GamingEconomy } from "@/components/gaming-economy"
import { NetworkActivity } from "@/components/network-activity"
import { TokenHolders } from "@/components/token-holders"
import { KatanaDEX } from "@/components/katana-dex"
import { NFTMarketplace } from "@/components/nft-marketplace"
import { AlertsRecommendations } from "@/components/alerts-recommendations"
import { Header } from "@/components/header"
import { AnimatedBackground } from "@/components/animated-background"

export default function Page() {
  return (
    <div className="min-h-screen bg-background relative">
      <AnimatedBackground />
      <Header />
      <main className="container mx-auto px-4 py-8 space-y-8 relative z-10">
        <HeroSection />
        <AlertsRecommendations />
        <TokenMetrics />
        <GamingEconomy />
        <NetworkActivity />
        <TokenHolders />
        <KatanaDEX />
        <NFTMarketplace />
      </main>
    </div>
  )
}
