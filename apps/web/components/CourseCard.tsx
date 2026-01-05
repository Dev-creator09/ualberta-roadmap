"use client";

import { RoadmapCourse } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Circle, AlertTriangle } from "lucide-react";

interface CourseCardProps {
  course: RoadmapCourse;
  isCompleted: boolean;
  onToggleComplete: () => void;
}

export function CourseCard({ course, isCompleted, onToggleComplete }: CourseCardProps) {
  return (
    <Card
      className={`p-4 cursor-pointer transition-all hover:shadow-md ${
        isCompleted ? "bg-green-50 border-green-300" : "bg-white"
      }`}
      onClick={onToggleComplete}
    >
      <div className="flex items-start gap-3">
        {/* Completion Icon */}
        <div className="flex-shrink-0 mt-0.5">
          {isCompleted ? (
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          ) : (
            <Circle className="h-5 w-5 text-gray-400" />
          )}
        </div>

        {/* Course Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <div className="flex-1">
              <h4 className={`font-semibold text-sm ${isCompleted ? "line-through text-gray-600" : "text-gray-900"}`}>
                {course.code}
              </h4>
              <p className={`text-xs ${isCompleted ? "line-through text-gray-500" : "text-gray-600"}`}>
                {course.title}
              </p>
            </div>
            <Badge variant="outline" className="flex-shrink-0 text-xs">
              {course.credits} cr
            </Badge>
          </div>

          {/* Prerequisites Warning */}
          {!course.prerequisites_met && (
            <div className="flex items-center gap-1 mt-2 text-xs text-amber-700 bg-amber-50 rounded px-2 py-1">
              <AlertTriangle className="h-3 w-3" />
              <span>Prerequisites not met</span>
            </div>
          )}

          {/* Course Warnings */}
          {course.warnings.length > 0 && (
            <div className="mt-2 space-y-1">
              {course.warnings.map((warning, idx) => (
                <div key={idx} className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1">
                  {warning}
                </div>
              ))}
            </div>
          )}

          {/* Satisfies Requirements */}
          {course.satisfies_requirements.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {course.satisfies_requirements.map((req) => (
                <Badge key={req} variant="secondary" className="text-xs">
                  {req}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
