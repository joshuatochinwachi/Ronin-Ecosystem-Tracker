"use client"

import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function ChartSkeleton({ height = 300 }: { height?: number }) {
    return (
        <div className="w-full space-y-2">
            <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-[100px]" />
                <Skeleton className="h-4 w-[60px]" />
            </div>
            <Skeleton className={`w-full rounded-xl`} style={{ height: `${height}px` }} />
        </div>
    )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <Skeleton className="h-8 w-[200px]" />
                <Skeleton className="h-8 w-[100px]" />
            </div>
            <div className="space-y-2">
                {Array.from({ length: rows }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                ))}
            </div>
        </div>
    )
}

export function MetricCardSkeleton() {
    return (
        <Card className="glass-card">
            <CardHeader>
                <Skeleton className="h-5 w-[140px]" />
                <Skeleton className="h-3 w-[100px] mt-1" />
            </CardHeader>
            <CardContent>
                <Skeleton className="h-[200px] w-full" />
            </CardContent>
        </Card>
    )
}
