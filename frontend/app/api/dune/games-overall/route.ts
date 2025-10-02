import { NextResponse } from "next/server"

const API_BASE = "https://web-production-4fae.up.railway.app"

export async function GET() {
  try {
    const response = await fetch(`${API_BASE}/api/raw/dune/games_overall_activity`, {
      next: { revalidate: 60 },
    })

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("[v0] Dune Games Overall API Error:", error)
    return NextResponse.json({ error: "Failed to fetch data" }, { status: 500 })
  }
}
