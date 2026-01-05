/**
 * Import programs and requirements from degree-requirements.json
 *
 * Reads program data from JSON file and imports into the database.
 * Creates Program records and associated Requirement records.
 * Validates that referenced courses exist in the database.
 */

import { PrismaClient, RequirementType } from '@prisma/client'
import { readFileSync } from 'fs'
import { join } from 'path'

const prisma = new PrismaClient()

// Type definitions for the JSON structure
interface RequirementJSON {
  name: string
  type: 'required' | 'choice' | 'level_requirement' | 'elective'
  courses?: string[]
  credits_needed?: number
  choose_count?: number
  level_filter?: string[]
  subject_filter?: string
  order_index?: number
}

interface SpecialRule {
  type?: string
  courses?: string[]
  rule?: string
  original?: string
  alternatives?: string[]
  note?: string
  [key: string]: any
}

interface ProgramJSON {
  id: string
  name: string
  total_credits: number
  requirements: RequirementJSON[]
  special_rules?: SpecialRule[]
  min_credits?: number
  min_cmput_credits?: number
  min_senior_level?: number
  [key: string]: any
}

interface ProgramDataJSON {
  programs: ProgramJSON[]
}

/**
 * Convert requirement type from JSON to Prisma enum
 */
function parseRequirementType(type: string): RequirementType {
  const typeMap: Record<string, RequirementType> = {
    required: RequirementType.REQUIRED,
    choice: RequirementType.CHOICE,
    level_requirement: RequirementType.LEVEL_REQUIREMENT,
    elective: RequirementType.ELECTIVE,
  }

  const mappedType = typeMap[type.toLowerCase()]
  if (!mappedType) {
    console.warn(`Unknown requirement type: ${type}, defaulting to REQUIRED`)
    return RequirementType.REQUIRED
  }

  return mappedType
}

/**
 * Validate that courses exist in the database
 */
async function validateCourses(
  courses: string[],
  programCode: string,
  requirementName: string
): Promise<{ valid: string[]; missing: string[] }> {
  const valid: string[] = []
  const missing: string[] = []

  for (const courseCode of courses) {
    const course = await prisma.course.findUnique({
      where: { code: courseCode },
    })

    if (course) {
      valid.push(courseCode)
    } else {
      missing.push(courseCode)
    }
  }

  if (missing.length > 0) {
    console.warn(
      `⚠️  Program "${programCode}", Requirement "${requirementName}": ` +
        `${missing.length} course(s) not found: ${missing.join(', ')}`
    )
  }

  return { valid, missing }
}

/**
 * Import programs and requirements from JSON file
 */
async function importPrograms() {
  console.log('🎓 Starting program import...\n')

  try {
    // Read JSON file from project root
    const jsonPath = join(process.cwd(), '..', '..', 'degree-requirements.json')
    console.log(`Reading from: ${jsonPath}`)

    let fileContent: string
    try {
      fileContent = readFileSync(jsonPath, 'utf-8')
    } catch (error) {
      console.error(`❌ Failed to read file: ${jsonPath}`)
      console.error(
        'Make sure degree-requirements.json exists in the project root directory'
      )
      throw error
    }

    // Parse JSON
    let data: ProgramDataJSON
    try {
      data = JSON.parse(fileContent)
    } catch (error) {
      console.error('❌ Failed to parse JSON file')
      throw error
    }

    if (!data.programs || !Array.isArray(data.programs)) {
      throw new Error('Invalid JSON structure: missing "programs" array')
    }

    console.log(`Found ${data.programs.length} programs to import\n`)

    // Import statistics
    let programsImported = 0
    let programsUpdated = 0
    let programsFailed = 0
    let requirementsImported = 0
    let totalMissingCourses = 0

    // Process each program
    for (const programData of data.programs) {
      try {
        // Validate required fields
        if (!programData.id || !programData.name) {
          console.warn(
            `⚠️  Skipping program: missing id or name`,
            programData
          )
          programsFailed++
          continue
        }

        console.log(`\nProcessing: ${programData.name} (${programData.id})`)

        // Prepare requirements JSONB data
        const requirementsData: any = {}
        if (programData.min_credits !== undefined) {
          requirementsData.minCredits = programData.min_credits
        }
        if (programData.min_cmput_credits !== undefined) {
          requirementsData.minCMPUTCredits = programData.min_cmput_credits
        }
        if (programData.min_senior_level !== undefined) {
          requirementsData.minSeniorLevel = programData.min_senior_level
        }

        // Add any additional fields from the JSON
        Object.keys(programData).forEach((key) => {
          if (
            !['id', 'name', 'total_credits', 'requirements', 'special_rules'].includes(
              key
            ) &&
            !key.startsWith('min_')
          ) {
            requirementsData[key] = programData[key]
          }
        })

        // Prepare special rules JSONB data
        const specialRules = programData.special_rules
          ? { rules: programData.special_rules }
          : null

        // Check if program exists
        const existingProgram = await prisma.program.findUnique({
          where: { code: programData.id },
        })

        // Upsert program
        const program = await prisma.program.upsert({
          where: { code: programData.id },
          update: {
            name: programData.name,
            totalCredits: programData.total_credits || 120,
            requirements:
              Object.keys(requirementsData).length > 0
                ? (requirementsData as any)
                : null,
            specialRules: specialRules as any,
          },
          create: {
            code: programData.id,
            name: programData.name,
            totalCredits: programData.total_credits || 120,
            requirements:
              Object.keys(requirementsData).length > 0
                ? (requirementsData as any)
                : null,
            specialRules: specialRules as any,
          },
        })

        if (existingProgram) {
          programsUpdated++
          console.log(`  ✓ Updated program: ${programData.name}`)

          // Delete existing requirements to avoid duplicates
          await prisma.requirement.deleteMany({
            where: { programId: program.id },
          })
          console.log(`  🗑️  Removed old requirements`)
        } else {
          programsImported++
          console.log(`  ✓ Created program: ${programData.name}`)
        }

        // Create requirements
        if (programData.requirements && programData.requirements.length > 0) {
          console.log(
            `  📋 Processing ${programData.requirements.length} requirements...`
          )

          for (const [index, reqData] of programData.requirements.entries()) {
            try {
              // Validate courses if provided
              const courses = reqData.courses || []
              let validCourses = courses

              if (courses.length > 0) {
                const validation = await validateCourses(
                  courses,
                  programData.id,
                  reqData.name
                )
                validCourses = validation.valid
                totalMissingCourses += validation.missing.length
              }

              // Create requirement
              await prisma.requirement.create({
                data: {
                  programId: program.id,
                  name: reqData.name,
                  requirementType: parseRequirementType(reqData.type),
                  courses: validCourses,
                  creditsNeeded: reqData.credits_needed ?? null,
                  chooseCount: reqData.choose_count ?? null,
                  levelFilter: reqData.level_filter || [],
                  subjectFilter: reqData.subject_filter ?? null,
                  orderIndex: reqData.order_index ?? index,
                },
              })

              requirementsImported++
              console.log(
                `    ✓ ${reqData.name} (${reqData.type}${reqData.courses ? `: ${reqData.courses.length} courses` : ''})`
              )
            } catch (error) {
              console.error(
                `    ❌ Failed to create requirement: ${reqData.name}`,
                error instanceof Error ? error.message : error
              )
            }
          }
        }
      } catch (error) {
        programsFailed++
        console.error(
          `❌ Failed to import program: ${programData.id}`,
          error instanceof Error ? error.message : error
        )
      }
    }

    // Print summary
    console.log('\n' + '='.repeat(60))
    console.log('📊 Import Summary:')
    console.log('='.repeat(60))
    console.log(`Total programs processed: ${data.programs.length}`)
    console.log(`✅ Successfully imported: ${programsImported}`)
    console.log(`🔄 Updated existing: ${programsUpdated}`)
    console.log(`❌ Failed: ${programsFailed}`)
    console.log(`📋 Requirements created: ${requirementsImported}`)
    if (totalMissingCourses > 0) {
      console.log(
        `⚠️  Missing course references: ${totalMissingCourses} (check warnings above)`
      )
    }
    console.log('='.repeat(60) + '\n')

    if (programsFailed > 0) {
      console.warn('⚠️  Some programs failed to import. Check errors above.')
      process.exit(1)
    }

    if (totalMissingCourses > 0) {
      console.warn(
        '⚠️  Some requirements reference courses that do not exist in the database.'
      )
      console.warn('   Consider importing courses first or updating the JSON file.\n')
    }

    console.log('✨ Program import completed successfully!\n')
  } catch (error) {
    console.error('\n❌ Program import failed:', error)
    throw error
  } finally {
    await prisma.$disconnect()
  }
}

// Run import if this file is executed directly
if (require.main === module) {
  importPrograms()
    .then(() => process.exit(0))
    .catch(() => process.exit(1))
}

export { importPrograms }
