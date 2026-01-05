-- CreateEnum
CREATE TYPE "CourseLevel" AS ENUM ('100', '200', '300', '400', '500');

-- CreateEnum
CREATE TYPE "RequirementType" AS ENUM ('REQUIRED', 'CHOICE', 'LEVEL_REQUIREMENT', 'ELECTIVE');

-- CreateEnum
CREATE TYPE "Term" AS ENUM ('FALL', 'WINTER', 'SPRING', 'SUMMER');

-- CreateEnum
CREATE TYPE "CourseStatus" AS ENUM ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'DROPPED', 'WAITLISTED');

-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('STUDENT', 'ADVISOR', 'ADMIN');

-- CreateTable
CREATE TABLE "courses" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "credits" INTEGER NOT NULL DEFAULT 3,
    "description" TEXT,
    "prerequisiteFormula" JSONB,
    "typicallyOffered" TEXT[],
    "level" "CourseLevel" NOT NULL,
    "subject" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "courses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "programs" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "totalCredits" INTEGER NOT NULL DEFAULT 120,
    "requirements" JSONB,
    "specialRules" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "programs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "requirements" (
    "id" TEXT NOT NULL,
    "programId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "requirementType" "RequirementType" NOT NULL,
    "courses" TEXT[],
    "creditsNeeded" INTEGER,
    "chooseCount" INTEGER,
    "levelFilter" TEXT[],
    "subjectFilter" TEXT,
    "orderIndex" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "requirements_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "students" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "startingYear" INTEGER NOT NULL,
    "programCode" TEXT NOT NULL,
    "specialization" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "students_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "roadmaps" (
    "id" TEXT NOT NULL,
    "studentId" TEXT NOT NULL,
    "programId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "generatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "roadmaps_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "roadmap_courses" (
    "id" TEXT NOT NULL,
    "roadmapId" TEXT NOT NULL,
    "courseCode" TEXT NOT NULL,
    "semester" INTEGER NOT NULL,
    "year" INTEGER NOT NULL,
    "term" "Term" NOT NULL,
    "status" "CourseStatus" NOT NULL DEFAULT 'PLANNED',
    "satisfiesRequirements" TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "roadmap_courses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "role" "UserRole" NOT NULL DEFAULT 'STUDENT',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "_RequirementCourses" (
    "A" TEXT NOT NULL,
    "B" TEXT NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "courses_code_key" ON "courses"("code");

-- CreateIndex
CREATE INDEX "courses_code_idx" ON "courses"("code");

-- CreateIndex
CREATE INDEX "courses_subject_idx" ON "courses"("subject");

-- CreateIndex
CREATE INDEX "courses_level_idx" ON "courses"("level");

-- CreateIndex
CREATE UNIQUE INDEX "programs_code_key" ON "programs"("code");

-- CreateIndex
CREATE INDEX "programs_code_idx" ON "programs"("code");

-- CreateIndex
CREATE INDEX "requirements_programId_idx" ON "requirements"("programId");

-- CreateIndex
CREATE INDEX "requirements_requirementType_idx" ON "requirements"("requirementType");

-- CreateIndex
CREATE UNIQUE INDEX "students_email_key" ON "students"("email");

-- CreateIndex
CREATE INDEX "students_email_idx" ON "students"("email");

-- CreateIndex
CREATE INDEX "students_programCode_idx" ON "students"("programCode");

-- CreateIndex
CREATE INDEX "roadmaps_studentId_idx" ON "roadmaps"("studentId");

-- CreateIndex
CREATE INDEX "roadmaps_programId_idx" ON "roadmaps"("programId");

-- CreateIndex
CREATE INDEX "roadmaps_isActive_idx" ON "roadmaps"("isActive");

-- CreateIndex
CREATE INDEX "roadmap_courses_roadmapId_idx" ON "roadmap_courses"("roadmapId");

-- CreateIndex
CREATE INDEX "roadmap_courses_courseCode_idx" ON "roadmap_courses"("courseCode");

-- CreateIndex
CREATE INDEX "roadmap_courses_status_idx" ON "roadmap_courses"("status");

-- CreateIndex
CREATE INDEX "roadmap_courses_term_idx" ON "roadmap_courses"("term");

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_email_idx" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "_RequirementCourses_AB_unique" ON "_RequirementCourses"("A", "B");

-- CreateIndex
CREATE INDEX "_RequirementCourses_B_index" ON "_RequirementCourses"("B");

-- AddForeignKey
ALTER TABLE "requirements" ADD CONSTRAINT "requirements_programId_fkey" FOREIGN KEY ("programId") REFERENCES "programs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "students" ADD CONSTRAINT "students_programCode_fkey" FOREIGN KEY ("programCode") REFERENCES "programs"("code") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "roadmaps" ADD CONSTRAINT "roadmaps_studentId_fkey" FOREIGN KEY ("studentId") REFERENCES "students"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "roadmaps" ADD CONSTRAINT "roadmaps_programId_fkey" FOREIGN KEY ("programId") REFERENCES "programs"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "roadmap_courses" ADD CONSTRAINT "roadmap_courses_roadmapId_fkey" FOREIGN KEY ("roadmapId") REFERENCES "roadmaps"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "roadmap_courses" ADD CONSTRAINT "roadmap_courses_courseCode_fkey" FOREIGN KEY ("courseCode") REFERENCES "courses"("code") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_RequirementCourses" ADD CONSTRAINT "_RequirementCourses_A_fkey" FOREIGN KEY ("A") REFERENCES "courses"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_RequirementCourses" ADD CONSTRAINT "_RequirementCourses_B_fkey" FOREIGN KEY ("B") REFERENCES "requirements"("id") ON DELETE CASCADE ON UPDATE CASCADE;
