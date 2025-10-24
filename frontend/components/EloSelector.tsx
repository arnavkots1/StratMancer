'use client';

import { useState } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/cn';

export type EloGroup = 'low' | 'mid' | 'high';

interface EloSelectorProps {
  value: EloGroup;
  onChange: (_elo: EloGroup) => void | Promise<void>;
  className?: string;
}

const ELO_OPTIONS = [
  {
    value: 'low' as const,
    label: 'Low ELO',
    description: 'Iron, Bronze, Silver',
    color: 'text-red-500',
    bgColor: 'bg-red-50 dark:bg-red-950/20',
    borderColor: 'border-red-200 dark:border-red-800'
  },
  {
    value: 'mid' as const,
    label: 'Mid ELO',
    description: 'Gold, Platinum, Emerald',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/20',
    borderColor: 'border-yellow-200 dark:border-yellow-800'
  },
  {
    value: 'high' as const,
    label: 'High ELO',
    description: 'Diamond, Master, GM, Challenger',
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-950/20',
    borderColor: 'border-blue-200 dark:border-blue-800'
  }
];

export default function EloSelector({ value, onChange, className }: EloSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  
  const selectedOption = ELO_OPTIONS.find(option => option.value === value);

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center justify-between w-full px-4 py-3 text-left',
          'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
          'rounded-lg shadow-sm hover:shadow-md transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
          selectedOption?.bgColor,
          selectedOption?.borderColor
        )}
      >
        <div className="flex flex-col">
          <span className={cn('font-medium', selectedOption?.color)}>
            {selectedOption?.label}
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {selectedOption?.description}
          </span>
        </div>
        <ChevronDown 
          className={cn(
            'w-5 h-5 text-gray-400 transition-transform duration-200',
            isOpen && 'rotate-180'
          )} 
        />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div className="absolute top-full left-0 right-0 mt-1 z-20">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
              {ELO_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                  className={cn(
                    'w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700',
                    'transition-colors duration-150 flex items-center justify-between',
                    value === option.value && option.bgColor
                  )}
                >
                  <div className="flex flex-col">
                    <span className={cn('font-medium', option.color)}>
                      {option.label}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {option.description}
                    </span>
                  </div>
                  {value === option.value && (
                    <Check className="w-5 h-5 text-green-500" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
