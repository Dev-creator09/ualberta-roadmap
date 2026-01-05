/**
 * Import courses from course-data.json
 *
 * Reads course data from JSON file and imports into the database.
 * Supports both simple prerequisite arrays and nested AND/OR logic.
 */

import { PrismaClient, CourseLevel } from '@prisma/client'
import { readFileSync } from 'fs'
import { join } from 'path'

const prisma = new PrismaClient()

// Type definitions for the JSON structure
interface CourseJSON {
  code: string
  title: string
  credits?: number
  description?: string
  prerequisites?: string[] | PrerequisiteNode
  typically_offered?: string[]
}

interface PrerequisiteNode {
  type: 'AND' | 'OR'
  courses?: string[]
  conditions?: (PrerequisiteNode | { type: 'COURSE'; code: string })[]
}

interface CourseDataJSON {
  courses: CourseJSON[]
}

/**
 * Extract subject and level from course code
 * Examples: "CMPUT 174" -> {subject: "CMPUT", level: "100"}
 *           "MATH 225" -> {subject: "MATH", level: "200"}
 */
function extractCourseInfo(code: string): { subject: string; level: CourseLevel } {
  const parts = code.trim().split(/\s+/)
  if (parts.length < 2) {
    throw new Error(`Invalid course code format: ${code}`)
  }

  const subject = parts[0]
  const number = parts[1]

  // Extract level from course number (first digit * 100)
  const levelDigit = parseInt(number.charAt(0))
  const levelMap: Record<number, CourseLevel> = {
    1: CourseLevel.LEVEL_100,
    2: CourseLevel.LEVEL_200,
    3: CourseLevel.LEVEL_300,
    4: CourseLevel.LEVEL_400,
    5: CourseLevel.LEVEL_500,
  }

  const level = levelMap[levelDigit]
  if (!level) {
    throw new Error(`Cannot determine level for course: ${code}`)
  }

  return { subject, level }
}

/**
 * Convert prerequisite structure to JSONB formula
 * Handles both simple arrays and nested AND/OR logic
 */
function parsePrerequisites(
  prerequisites: string[] | PrerequisiteNode | undefined
): object | null {
  if (!prerequisites) {
    return null
  }

  // Simple array of course codes - convert to AND logic
  if (Array.isArray(prerequisites)) {
    if (prerequisites.length === 0) {
      return null
    }
    if (prerequisites.length === 1) {
      return {
        type: 'COURSE',
        code: prerequisites[0],
      }
    }
    return {
      type: 'AND',
      conditions: prerequisites.map((code) => ({
        type: 'COURSE',
        code,
      })),
    }
  }

  // Nested AND/OR structure
  if (prerequisites.type === 'AND' || prerequisites.type === 'OR') {
    // Handle direct courses array
    if (prerequisites.courses && Array.isArray(prerequisites.courses)) {
      return {
        type: prerequisites.type,
        conditions: prerequisites.courses.map((code) => ({
          type: 'COURSE',
          code,
        })),
      }
    }

    // Handle nested conditions
    if (prerequisites.conditions) {
      return {
        type: prerequisites.type,
        conditions: prerequisites.conditions.map((condition) => {
          if ('code' in condition) {
            return condition
          }
          return parsePrerequisites(condition)
        }),
      }
    }
  }

  console.warn('Unrecognized prerequisite structure:', prerequisites)
  return null
}

/**
 * Import courses from JSON file
 */
async function importCourses() {
  console.log('📚 Starting course import...\n')

  try {
    // Read JSON file from project root
    const jsonPath = join(process.cwd(), '..', '..', 'course-data.json')
    console.log(`Reading from: ${jsonPath}`)

    let fileContent: string
    try {
      fileContent = readFileSync(jsonPath, 'utf-8')
    } catch (error) {
      console.error(`❌ Failed to read file: ${jsonPath}`)
      console.error(
        'Make sure course-data.json exists in the project root directory'
      )
      throw error
    }

    // Parse JSON
    let data: CourseDataJSON
    try {
      data = JSON.parse(fileContent)
    } catch (error) {
      console.error('❌ Failed to parse JSON file')
      throw error
    }

    if (!data.courses || !Array.isArray(data.courses)) {
      throw new Error('Invalid JSON structure: missing "courses" array')
    }

    console.log(`Found ${data.courses.length} courses to import\n`)

    // Import statistics
    let imported = 0
    let updated = 0
    let failed = 0

    // Process each course
    for (const courseData of data.courses) {
      try {
        // Validate required fields
        if (!courseData.code || !courseData.title) {
          console.warn(
            `⚠️  Skipping course: missing code or title`,
            courseData
          )
          failed++
          continue
        }

        // Extract subject and level
        const { subject, level } = extractCourseInfo(courseData.code)

        // Parse prerequisites
        const prerequisiteFormula = parsePrerequisites(
          courseData.prerequisites
        )

        // Upsert course
        const result = await prisma.course.upsert({
          where: { code: courseData.code },
          update: {
            title: courseData.title,
            credits: courseData.credits ?? 3,
            description: courseData.description ?? null,
            prerequisiteFormula:
              prerequisiteFormula as any, // Prisma handles JSONB type
            typicallyOffered: courseData.typically_offered ?? [],
            level,
            subject,
          },
          create: {
            code: courseData.code,
            title: courseData.title,
            credits: courseData.credits ?? 3,
            description: courseData.description ?? null,
            prerequisiteFormula:
              prerequisiteFormula as any,
            typicallyOffered: courseData.typically_offered ?? [],
            level,
            subject,
          },
        })

        // Check if it was an update or create
        const existingCourse = await prisma.course.findUnique({
          where: { code: courseData.code },
          select: { createdAt: true, updatedAt: true },
        })

        if (
          existingCourse &&
          existingCourse.createdAt.getTime() !==
            existingCourse.updatedAt.getTime()
        ) {
          updated++
          console.log(`✓ Updated: ${courseData.code} - ${courseData.title}`)
        } else {
          imported++
          console.log(`✓ Imported: ${courseData.code} - ${courseData.title}`)
        }
      } catch (error) {
        failed++
        console.error(
          `❌ Failed to import course: ${courseData.code}`,
          error instanceof Error ? error.message : error
        )
      }
    }

    // Print summary
    console.log('\n' + '='.repeat(60))
    console.log('📊 Import Summary:')
    console.log('='.repeat(60))
    console.log(`Total courses processed: ${data.courses.length}`)
    console.log(`✅ Successfully imported: ${imported}`)
    console.log(`🔄 Updated existing: ${updated}`)
    console.log(`❌ Failed: ${failed}`)
    console.log('='.repeat(60) + '\n')

    if (failed > 0) {
      console.warn('⚠️  Some courses failed to import. Check errors above.')
      process.exit(1)
    }

    console.log('✨ Course import completed successfully!\n')
  } catch (error) {
    console.error('\n❌ Course import failed:', error)
    throw error
  } finally {
    await prisma.$disconnect()
  }
}

// Run import if this file is executed directly
if (require.main === module) {
  importCourses()
    .then(() => process.exit(0))
    .catch(() => process.exit(1))
}

export { importCourses }
