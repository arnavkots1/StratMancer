/**
 * Accessible, responsive table component for Draft IQ v2
 */

"use client"

import React from 'react'
import { cn } from '../../lib/cn'

interface TableColumn {
  header: string
  key: string
  className?: string
}

interface TableLiteProps {
  columns: TableColumn[]
  data: Record<string, React.ReactNode>[]
  className?: string
  headerClassName?: string
  rowClassName?: string
}

export function TableLite({ 
  columns, 
  data, 
  className,
  headerClassName,
  rowClassName 
}: TableLiteProps) {
  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full border-collapse">
        <thead>
          <tr className={cn("border-b border-white/10", headerClassName)}>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={cn(
                  "px-4 py-3 text-left text-xs uppercase tracking-[0.28em] text-white/60",
                  col.className
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={idx}
              className={cn(
                "border-b border-white/5 transition-colors hover:bg-white/5",
                rowClassName
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={cn(
                    "px-4 py-3 text-sm text-white/80",
                    col.className
                  )}
                >
                  {row[col.key] ?? '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

