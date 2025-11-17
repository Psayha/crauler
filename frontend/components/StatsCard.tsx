import { ReactNode } from "react";

interface StatsCardProps {
  icon: ReactNode;
  label: string;
  value: number;
  color?: string;
}

export function StatsCard({ icon, label, value, color = "text-tg-text" }: StatsCardProps) {
  return (
    <div className="bg-tg-secondary-bg rounded-lg p-3">
      <div className={`mb-2 ${color}`}>{icon}</div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-xs text-tg-hint">{label}</div>
    </div>
  );
}
