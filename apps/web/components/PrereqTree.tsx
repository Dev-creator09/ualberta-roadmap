"use client";

import { PrerequisiteNode } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface PrereqTreeProps {
  prerequisites: PrerequisiteNode | null;
  completedCourses?: string[];
}

function PrereqNodeComponent({
  node,
  depth = 0,
  completedCourses = []
}: {
  node: PrerequisiteNode;
  depth?: number;
  completedCourses?: string[];
}) {
  const indent = depth * 24;
  const isCompleted = node.code ? completedCourses.includes(node.code) : false;

  if (node.type === "COURSE") {
    return (
      <div
        className="flex items-center gap-2 mb-2"
        style={{ marginLeft: `${indent}px` }}
      >
        <Badge
          variant={isCompleted ? "default" : "outline"}
          className={isCompleted ? "bg-green-600" : ""}
        >
          {node.code}
        </Badge>
        {node.title && (
          <span className="text-xs text-gray-600">{node.title}</span>
        )}
      </div>
    );
  }

  if (node.type === "AND" || node.type === "OR") {
    return (
      <div className="mb-2">
        <div
          className="flex items-center gap-2 mb-2"
          style={{ marginLeft: `${indent}px` }}
        >
          <Badge variant="secondary" className="text-xs">
            {node.type}
          </Badge>
        </div>
        {node.conditions && node.conditions.map((child, idx) => (
          <PrereqNodeComponent
            key={idx}
            node={child}
            depth={depth + 1}
            completedCourses={completedCourses}
          />
        ))}
      </div>
    );
  }

  return null;
}

export function PrereqTree({ prerequisites, completedCourses = [] }: PrereqTreeProps) {
  if (!prerequisites) {
    return (
      <Card className="p-4">
        <p className="text-sm text-gray-500">No prerequisites</p>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <h4 className="font-semibold text-sm mb-3">Prerequisites</h4>
      <div className="space-y-2">
        <PrereqNodeComponent
          node={prerequisites}
          completedCourses={completedCourses}
        />
      </div>
    </Card>
  );
}
