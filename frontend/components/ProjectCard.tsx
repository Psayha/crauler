import { useRouter } from "next/navigation";
import { getStatusColor, getStatusLabel, formatRelativeTime } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

interface ProjectCardProps {
  project: any;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const router = useRouter();

  const getProjectIcon = (type: string) => {
    const icons: Record<string, string> = {
      website: "🌐",
      mobile_app: "📱",
      marketing_campaign: "📊",
      data_analysis: "📈",
      content_creation: "✍️",
      custom: "⚙️",
    };
    return icons[type] || "📋";
  };

  const getProgress = () => {
    if (project.status === "completed") return 100;
    if (project.status === "in_progress") return 65; // TODO: Calculate real progress
    if (project.status === "planning") return 25;
    return 0;
  };

  const progress = getProgress();

  return (
    <div
      onClick={() => router.push(`/projects/${project.id}`)}
      className="bg-tg-secondary-bg rounded-xl p-4 active:opacity-70 transition-opacity cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{getProjectIcon(project.type)}</span>
          <div>
            <h3 className="font-semibold line-clamp-1">{project.name}</h3>
            <p className="text-xs text-tg-hint">
              {formatRelativeTime(project.created_at)}
            </p>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-tg-hint flex-shrink-0" />
      </div>

      <div className="flex items-center gap-2 mb-2">
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
            project.status
          )} bg-opacity-20`}
        >
          {getStatusLabel(project.status)}
        </span>
        {project.priority && project.priority !== "normal" && (
          <span className="px-2 py-1 rounded text-xs font-medium bg-orange-500 bg-opacity-20 text-orange-500">
            {project.priority === "high" ? "Высокий" : "Критичный"}
          </span>
        )}
      </div>

      {project.status === "in_progress" && (
        <div>
          <div className="flex items-center justify-between text-xs text-tg-hint mb-1">
            <span>Прогресс</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-tg-bg rounded-full h-2">
            <div
              className="bg-tg-button h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
