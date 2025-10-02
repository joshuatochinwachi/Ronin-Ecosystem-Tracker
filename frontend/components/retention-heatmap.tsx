"use client"

interface RetentionData {
  cohort_week: string
  game_project: string
  new_users: number
  week_1: number | null
  week_2: number | null
  week_3: number | null
  week_4: number | null
  week_5: number | null
  week_6: number | null
  week_7: number | null
  week_8: number | null
  week_9: number | null
  week_10: number | null
  week_11: number | null
  week_12: number | null
}

interface RetentionHeatmapProps {
  data: RetentionData[]
}

export function RetentionHeatmap({ data }: RetentionHeatmapProps) {
  const getColorForValue = (value: number | null | undefined) => {
    if (value == null) return "bg-muted/30"
    if (value >= 80) return "bg-blue-600"
    if (value >= 60) return "bg-blue-500"
    if (value >= 40) return "bg-blue-400"
    if (value >= 20) return "bg-blue-300"
    return "bg-blue-200"
  }

  const weeks = [
    "week_1",
    "week_2",
    "week_3",
    "week_4",
    "week_5",
    "week_6",
    "week_7",
    "week_8",
    "week_9",
    "week_10",
    "week_11",
    "week_12",
  ]

  return (
    <div className="overflow-x-auto">
      <div className="inline-block min-w-full">
        <div className="grid gap-2" style={{ gridTemplateColumns: `120px 150px 100px repeat(${weeks.length}, 80px)` }}>
          {/* Header */}
          <div className="font-semibold text-sm text-muted-foreground p-2 sticky left-0 bg-card z-10">Cohort Week</div>
          <div className="font-semibold text-sm text-muted-foreground p-2">Game Project</div>
          <div className="font-semibold text-sm text-muted-foreground p-2">New Users</div>
          {weeks.map((week, index) => (
            <div key={week} className="font-semibold text-sm text-muted-foreground p-2 text-center">
              Week {index + 1}
            </div>
          ))}

          {/* Data rows */}
          {data.map((row, rowIndex) => (
            <>
              <div
                key={`${row.cohort_week}-${rowIndex}-label`}
                className="font-medium text-sm p-2 flex items-center sticky left-0 bg-card z-10"
              >
                {row.cohort_week}
              </div>
              <div key={`${row.cohort_week}-${rowIndex}-game`} className="text-sm p-2 flex items-center">
                {row.game_project}
              </div>
              <div key={`${row.cohort_week}-${rowIndex}-users`} className="text-sm p-2 flex items-center">
                {row.new_users.toLocaleString()}
              </div>
              {weeks.map((week) => {
                const value = row[week as keyof RetentionData] as number | null
                return (
                  <div
                    key={`${row.cohort_week}-${rowIndex}-${week}`}
                    className={`p-2 rounded text-center text-sm font-medium text-white ${getColorForValue(value)}`}
                  >
                    {value != null ? `${value.toFixed(1)}%` : "-"}
                  </div>
                )
              })}
            </>
          ))}
        </div>
      </div>
    </div>
  )
}
