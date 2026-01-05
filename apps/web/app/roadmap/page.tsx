"use client";

import { useRouter } from "next/navigation";
import { useRoadmapStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ArrowLeft, CheckCircle2, AlertCircle, Circle, GraduationCap } from "lucide-react";
import { CourseCard } from "@/components/CourseCard";
import { WarningsPanel } from "@/components/WarningsPanel";

export default function RoadmapPage() {
  const router = useRouter();
  const { roadmap, visuallyCompletedCourses, toggleVisualCompletion } = useRoadmapStore();

  if (!roadmap) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>No Roadmap Found</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              You haven't generated a roadmap yet.
            </p>
            <Button onClick={() => router.push("/")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const completedCount = roadmap.requirement_progress.filter((r) => r.is_satisfied).length;
  const totalRequirements = roadmap.requirement_progress.length;
  const overallProgress = (completedCount / totalRequirements) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-amber-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" onClick={() => router.push("/")}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <div className="flex items-center gap-2">
                <GraduationCap className="h-6 w-6 text-green-700" />
                <span className="font-semibold text-gray-900">{roadmap.program_name}</span>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              {roadmap.total_credits} credits planned
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Program Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Your Academic Roadmap
          </h1>
          <p className="text-gray-600">
            {roadmap.semesters.length} semesters planned • {roadmap.total_credits} total credits
          </p>
        </div>

        {/* Overall Progress */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Degree Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Overall Requirements</span>
                  <span className="font-medium">
                    {completedCount} / {totalRequirements} complete
                  </span>
                </div>
                <Progress value={overallProgress} className="h-2" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                  <div>
                    <div className="text-2xl font-bold">{completedCount}</div>
                    <div className="text-sm text-gray-600">Satisfied</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-amber-600" />
                  <div>
                    <div className="text-2xl font-bold">
                      {totalRequirements - completedCount}
                    </div>
                    <div className="text-sm text-gray-600">Remaining</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Circle className="h-5 w-5 text-blue-600" />
                  <div>
                    <div className="text-2xl font-bold">{roadmap.semesters.length}</div>
                    <div className="text-sm text-gray-600">Semesters</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Warnings */}
        {roadmap.warnings.length > 0 && (
          <WarningsPanel warnings={roadmap.warnings} />
        )}

        {/* Requirements Progress */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Requirements Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {roadmap.requirement_progress.map((req) => {
                const progress = req.credits_needed > 0
                  ? (req.credits_completed / req.credits_needed) * 100
                  : 0;

                return (
                  <div key={req.requirement_id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {req.is_satisfied ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                        ) : (
                          <Circle className="h-5 w-5 text-gray-400 flex-shrink-0" />
                        )}
                        <div>
                          <div className="font-medium">{req.requirement_name}</div>
                          <div className="text-sm text-gray-600">
                            {req.requirement_type.replace(/_/g, " ")}
                          </div>
                        </div>
                      </div>
                      <Badge variant={req.is_satisfied ? "default" : "secondary"}>
                        {req.credits_completed} / {req.credits_needed} credits
                      </Badge>
                    </div>

                    {req.credits_needed > 0 && (
                      <Progress value={progress} className="h-1.5 mb-2" />
                    )}

                    {req.courses_used.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {req.courses_used.map((code) => (
                          <Badge key={code} variant="outline" className="text-xs">
                            {code}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Semester Grid */}
        <div className="space-y-8">
          <h2 className="text-2xl font-bold text-gray-900">Semester Plan</h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {roadmap.semesters.map((semester) => {
              const semesterCompleted = semester.courses.every((course) =>
                visuallyCompletedCourses.has(course.code)
              );

              return (
                <Card
                  key={semester.number}
                  className={`${
                    semesterCompleted ? "border-green-300 bg-green-50/50" : ""
                  }`}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">
                          {semester.term} {semester.year + 2023} - Year {semester.year}
                        </CardTitle>
                        <p className="text-sm text-gray-600 mt-1">
                          Semester {semester.number}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-lg">{semester.total_credits}</div>
                        <div className="text-xs text-gray-600">credits</div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {semester.courses.map((course) => (
                      <CourseCard
                        key={course.code}
                        course={course}
                        isCompleted={visuallyCompletedCourses.has(course.code)}
                        onToggleComplete={() => toggleVisualCompletion(course.code)}
                      />
                    ))}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-12 flex justify-center gap-4">
          <Button variant="outline" onClick={() => router.push("/")}>
            Generate New Roadmap
          </Button>
          <Button
            onClick={() => {
              window.print();
            }}
          >
            Print Roadmap
          </Button>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm mt-20">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-sm text-gray-600">
            <p className="mb-2">
              This is an unofficial tool for UAlberta Computing Science students.
            </p>
            <p>Always verify your course plan with an academic advisor.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
