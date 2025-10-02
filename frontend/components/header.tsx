"use client"

import { RefreshCw, Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { useTheme } from "next-themes"

export function Header() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const { theme, setTheme } = useTheme()

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await fetch("https://web-production-4fae.up.railway.app/api/cache/refresh", {
        method: "POST",
      })
      // Reload the page to fetch fresh data
      window.location.reload()
    } catch (error) {
      console.error("Refresh failed:", error)
    } finally {
      setTimeout(() => setIsRefreshing(false), 1000)
    }
  }

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-lg sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center text-2xl">
            🎮
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Ronin Ecosystem Tracker</h1>
            <p className="text-xs text-muted-foreground">Real-time blockchain analytics</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="gap-2"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {theme === "dark" ? "Light" : "Dark"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="gap-2 bg-transparent"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>
    </header>
  )
}
