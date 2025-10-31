"use client";

import { AlertCircle, Info, TrendingUp, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from '../lib/cn';

interface ConfidenceIndicatorProps {
  confidence: number;
  filledSlots: number;
  totalSlots: number;
  className?: string;
}

export function ConfidenceIndicator({ 
  confidence, 
  filledSlots, 
  totalSlots, 
  className 
}: ConfidenceIndicatorProps) {
  // Backend returns confidence as 0-100 percentage
  // Handle both 0-1 (decimal) and 0-100 (percentage) for backwards compatibility
  const confidencePercentage = confidence > 1 ? Math.round(confidence) : Math.round(confidence * 100);
  const isLowConfidence = confidencePercentage < 30;
  const isMediumConfidence = confidencePercentage >= 30 && confidencePercentage < 60;
  const _isHighConfidence = confidencePercentage >= 60;

  const _getConfidenceColor = () => {
    if (isLowConfidence) return "text-amber-400";
    if (isMediumConfidence) return "text-blue-400";
    return "text-emerald-400";
  };

  const getConfidenceBadge = () => {
    if (isLowConfidence) return "bg-amber-500/20 text-amber-300 border-amber-500/30";
    if (isMediumConfidence) return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
  };

  const getConfidenceExplanation = () => {
    if (filledSlots === 0) {
      return "No picks made yet. Confidence will increase as you add champions to the draft.";
    }
    
    if (filledSlots < 3) {
      return "Early draft phase. Limited data available for accurate predictions.";
    }
    
    if (filledSlots < 6) {
      return "Partial draft. More picks needed for higher confidence predictions.";
    }
    
    if (filledSlots < 10) {
      return "Mostly complete draft. Good confidence level with current picks.";
    }
    
    return "Complete draft. Maximum confidence with full team compositions.";
  };

  const getConfidenceIcon = () => {
    if (isLowConfidence) return <AlertCircle className="h-3 w-3" />;
    if (isMediumConfidence) return <Info className="h-3 w-3" />;
    return <TrendingUp className="h-3 w-3" />;
  };

  return (
    <TooltipProvider>
      <div className={cn("flex items-center gap-2", className)}>
        <Badge 
          variant="outline" 
          className={cn("flex items-center gap-1.5 px-2 py-1 text-xs", getConfidenceBadge())}
        >
          {getConfidenceIcon()}
          <span className="font-medium">{confidencePercentage}%</span>
        </Badge>
        
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-1 text-xs text-white/60">
              <Users className="h-3 w-3" />
              <span>{filledSlots}/{totalSlots}</span>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <div className="space-y-2">
              <div className="font-medium text-white">Confidence: {confidencePercentage}%</div>
              <div className="text-sm text-white/80">{getConfidenceExplanation()}</div>
              <div className="text-xs text-white/60">
                Draft Progress: {filledSlots} of {totalSlots} slots filled
              </div>
            </div>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}

