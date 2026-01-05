"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { GraduationCap, Sparkles, ArrowRight } from "lucide-react";

import { getPrograms, getCourses, generateRoadmap } from "@/lib/api";
import { useRoadmapStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { Term, CreditLoad } from "@/lib/types";

export default function HomePage() {
  const router = useRouter();
  const { formData, setFormData, setRoadmap } = useRoadmapStore();

  // State for multi-select courses
  const [searchTerm, setSearchTerm] = useState("");
  const [showCourseDropdown, setShowCourseDropdown] = useState(false);

  // Fetch programs
  const { data: programsData, isLoading: programsLoading } = useQuery({
    queryKey: ["programs"],
    queryFn: getPrograms,
  });

  // Fetch all CMPUT courses for selection
  const { data: coursesData, isLoading: coursesLoading } = useQuery({
    queryKey: ["courses", "CMPUT"],
    queryFn: () => getCourses({ subject: "CMPUT", page_size: 500 }),
  });

  // Generate roadmap mutation
  const generateMutation = useMutation({
    mutationFn: generateRoadmap,
    onSuccess: (data) => {
      setRoadmap(data);
      toast.success("Roadmap generated successfully!");
      router.push("/roadmap");
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to generate roadmap");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.program_code) {
      toast.error("Please select a program");
      return;
    }

    const request = {
      program_code: formData.program_code,
      starting_year: formData.starting_year,
      starting_term: formData.starting_term,
      completed_courses: formData.completed_courses,
      preferences: {
        specialization: formData.specialization || undefined,
        avoid_terms: formData.avoid_terms.length > 0 ? formData.avoid_terms : undefined,
      },
      credit_load_preference: formData.credit_load_preference,
      max_years: formData.max_years,
    };

    generateMutation.mutate(request);
  };

  const toggleCourse = (courseCode: string) => {
    const current = formData.completed_courses;
    if (current.includes(courseCode)) {
      setFormData({ completed_courses: current.filter((c) => c !== courseCode) });
    } else {
      setFormData({ completed_courses: [...current, courseCode] });
    }
  };

  const filteredCourses = coursesData?.courses.filter((course) =>
    course.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-amber-50">
      {/* Hero Section */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GraduationCap className="h-8 w-8 text-green-700" />
              <span className="text-xl font-bold text-gray-900">UAlberta Roadmap</span>
            </div>
            <Button variant="outline">About</Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <Sparkles className="h-4 w-4" />
            AI-Powered Planning
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Plan Your UAlberta CS Degree
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Generate a personalized semester-by-semester roadmap for your Computing Science degree
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle>Generate Your Roadmap</CardTitle>
              <CardDescription>
                Fill out your details to get an AI-generated course plan tailored to your needs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Program Selection */}
              <div className="space-y-2">
                <Label htmlFor="program">Program *</Label>
                {programsLoading ? (
                  <Skeleton className="h-10 w-full" />
                ) : (
                  <Select
                    value={formData.program_code}
                    onValueChange={(value) => setFormData({ program_code: value })}
                  >
                    <SelectTrigger id="program">
                      <SelectValue placeholder="Select your program" />
                    </SelectTrigger>
                    <SelectContent>
                      {programsData?.programs.map((program) => (
                        <SelectItem key={program.code} value={program.code}>
                          {program.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              {/* Starting Year and Term */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="year">Starting Year *</Label>
                  <Select
                    value={formData.starting_year?.toString() || new Date().getFullYear().toString()}
                    onValueChange={(value) => setFormData({ starting_year: parseInt(value) })}
                  >
                    <SelectTrigger id="year">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[2024, 2025, 2026, 2027].map((year) => (
                        <SelectItem key={year} value={year.toString()}>
                          {year}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Starting Term *</Label>
                  <RadioGroup
                    value={formData.starting_term}
                    onValueChange={(value) => setFormData({ starting_term: value as Term })}
                    className="flex gap-4"
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="FALL" id="fall" />
                      <Label htmlFor="fall" className="cursor-pointer">Fall</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="WINTER" id="winter" />
                      <Label htmlFor="winter" className="cursor-pointer">Winter</Label>
                    </div>
                  </RadioGroup>
                </div>
              </div>

              {/* Completed Courses */}
              <div className="space-y-2">
                <Label>Completed Courses (Optional)</Label>
                <div className="border rounded-md p-3 space-y-2">
                  <input
                    type="text"
                    placeholder="Search courses (e.g., CMPUT 174)..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value);
                      setShowCourseDropdown(true);
                    }}
                    onFocus={() => setShowCourseDropdown(true)}
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  />

                  {/* Selected courses */}
                  <div className="flex flex-wrap gap-2 min-h-[40px]">
                    {formData.completed_courses.map((code) => (
                      <Badge
                        key={code}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => toggleCourse(code)}
                      >
                        {code} ✕
                      </Badge>
                    ))}
                    {formData.completed_courses.length === 0 && (
                      <span className="text-sm text-gray-400">No courses selected</span>
                    )}
                  </div>

                  {/* Course dropdown */}
                  {showCourseDropdown && searchTerm && (
                    <div className="border rounded-md max-h-48 overflow-y-auto bg-white">
                      {coursesLoading ? (
                        <div className="p-3 space-y-2">
                          <Skeleton className="h-8 w-full" />
                          <Skeleton className="h-8 w-full" />
                        </div>
                      ) : (
                        filteredCourses?.slice(0, 10).map((course) => (
                          <div
                            key={course.code}
                            className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-0"
                            onClick={() => {
                              toggleCourse(course.code);
                              setSearchTerm("");
                              setShowCourseDropdown(false);
                            }}
                          >
                            <div className="font-medium">{course.code}</div>
                            <div className="text-sm text-gray-600">{course.title}</div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Specialization/Preferences */}
              <div className="space-y-2">
                <Label htmlFor="specialization">Specialization (Optional)</Label>
                <Textarea
                  id="specialization"
                  placeholder="e.g., AI, machine learning, software engineering..."
                  value={formData.specialization}
                  onChange={(e) => setFormData({ specialization: e.target.value })}
                  rows={2}
                />
              </div>

              {/* Terms to Avoid */}
              <div className="space-y-2">
                <Label>Terms to Avoid (Optional)</Label>
                <div className="flex flex-wrap gap-2">
                  {(["FALL", "WINTER", "SPRING", "SUMMER"] as Term[]).map((term) => (
                    <Badge
                      key={term}
                      variant={formData.avoid_terms.includes(term) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => {
                        const current = formData.avoid_terms;
                        if (current.includes(term)) {
                          setFormData({ avoid_terms: current.filter((t) => t !== term) });
                        } else {
                          setFormData({ avoid_terms: [...current, term] });
                        }
                      }}
                    >
                      {term}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Credit Load */}
              <div className="space-y-2">
                <Label>Credit Load Preference *</Label>
                <RadioGroup
                  value={formData.credit_load_preference}
                  onValueChange={(value) => setFormData({ credit_load_preference: value as CreditLoad })}
                  className="flex flex-col gap-2"
                >
                  <div className="flex items-center space-x-2 border rounded-md p-3 cursor-pointer hover:bg-gray-50">
                    <RadioGroupItem value="LIGHT" id="light" />
                    <Label htmlFor="light" className="cursor-pointer flex-1">
                      <div className="font-medium">Light (12 credits/semester)</div>
                      <div className="text-sm text-gray-500">Easier workload, takes longer</div>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 border rounded-md p-3 cursor-pointer hover:bg-gray-50">
                    <RadioGroupItem value="STANDARD" id="standard" />
                    <Label htmlFor="standard" className="cursor-pointer flex-1">
                      <div className="font-medium">Standard (15 credits/semester)</div>
                      <div className="text-sm text-gray-500">Recommended balanced approach</div>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 border rounded-md p-3 cursor-pointer hover:bg-gray-50">
                    <RadioGroupItem value="HEAVY" id="heavy" />
                    <Label htmlFor="heavy" className="cursor-pointer flex-1">
                      <div className="font-medium">Heavy (18 credits/semester)</div>
                      <div className="text-sm text-gray-500">Challenging but faster completion</div>
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full bg-green-700 hover:bg-green-800"
                size="lg"
                disabled={generateMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <>Generating Roadmap...</>
                ) : (
                  <>
                    Generate My Roadmap
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </form>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm mt-20">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-sm text-gray-600">
            <p className="mb-2">
              This is an unofficial tool for UAlberta Computing Science students.
            </p>
            <p>
              Always verify your course plan with an academic advisor.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
