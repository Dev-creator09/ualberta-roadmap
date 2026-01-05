/**
 * Database seeding script for UAlberta Roadmap
 *
 * This script populates the database with:
 * - Sample courses from Computing Science department
 * - Program definitions (Honors CS, Specialization CS)
 * - Program requirements
 * - Sample student and roadmap
 */

import { PrismaClient, CourseLevel, RequirementType, Term, CourseStatus } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Starting database seed...\n')

  // ============================================================================
  // CLEAN UP (optional - comment out if you want to preserve existing data)
  // ============================================================================
  console.log('🧹 Cleaning up existing data...')
  await prisma.roadmapCourse.deleteMany()
  await prisma.roadmap.deleteMany()
  await prisma.student.deleteMany()
  await prisma.requirement.deleteMany()
  await prisma.program.deleteMany()
  await prisma.course.deleteMany()
  await prisma.user.deleteMany()
  console.log('✅ Cleanup complete\n')

  // ============================================================================
  // SEED COURSES
  // ============================================================================
  console.log('📚 Seeding courses...')

  const courses = await Promise.all([
    // 100-level courses
    prisma.course.create({
      data: {
        code: 'CMPUT 174',
        title: 'Introduction to the Foundations of Computation I',
        credits: 3,
        description: 'Introduction to problem solving and computer programming using a procedural approach.',
        prerequisiteFormula: null,
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_100,
        subject: 'CMPUT',
      },
    }),
    prisma.course.create({
      data: {
        code: 'CMPUT 175',
        title: 'Introduction to the Foundations of Computation II',
        credits: 3,
        description: 'Introduction to object-oriented programming and data structures.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [{ type: 'COURSE', code: 'CMPUT 174' }],
        },
        typicallyOffered: ['Winter', 'Spring'],
        level: CourseLevel.LEVEL_100,
        subject: 'CMPUT',
      },
    }),

    // 200-level courses
    prisma.course.create({
      data: {
        code: 'CMPUT 201',
        title: 'Practical Programming Methodology',
        credits: 3,
        description: 'Introduction to the software development process including version control, testing, and debugging.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [{ type: 'COURSE', code: 'CMPUT 175' }],
        },
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_200,
        subject: 'CMPUT',
      },
    }),
    prisma.course.create({
      data: {
        code: 'CMPUT 204',
        title: 'Algorithms I',
        credits: 3,
        description: 'Introduction to the analysis and design of algorithms.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [
            { type: 'COURSE', code: 'CMPUT 175' },
            { type: 'COURSE', code: 'MATH 125' },
          ],
        },
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_200,
        subject: 'CMPUT',
      },
    }),
    prisma.course.create({
      data: {
        code: 'CMPUT 272',
        title: 'Formal Systems and Logic in Computing Science',
        credits: 3,
        description: 'Propositional and predicate logic, formal proof systems, and applications to computing science.',
        prerequisiteFormula: {
          type: 'OR',
          conditions: [
            { type: 'COURSE', code: 'CMPUT 174' },
            { type: 'COURSE', code: 'MATH 122' },
          ],
        },
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_200,
        subject: 'CMPUT',
      },
    }),
    prisma.course.create({
      data: {
        code: 'CMPUT 229',
        title: 'Computer Organization and Architecture I',
        credits: 3,
        description: 'Computer architecture, assembly language programming, and machine organization.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [{ type: 'COURSE', code: 'CMPUT 175' }],
        },
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_200,
        subject: 'CMPUT',
      },
    }),

    // 300-level courses
    prisma.course.create({
      data: {
        code: 'CMPUT 301',
        title: 'Introduction to Software Engineering',
        credits: 3,
        description: 'An introduction to the principles and practices of software engineering.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [
            { type: 'COURSE', code: 'CMPUT 201' },
            { type: 'COURSE', code: 'CMPUT 204' },
          ],
        },
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_300,
        subject: 'CMPUT',
      },
    }),
    prisma.course.create({
      data: {
        code: 'CMPUT 304',
        title: 'Algorithms II',
        credits: 3,
        description: 'Advanced algorithm design and analysis techniques.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [
            { type: 'COURSE', code: 'CMPUT 204' },
            { type: 'COURSE', code: 'STAT 151' },
          ],
        },
        typicallyOffered: ['Fall'],
        level: CourseLevel.LEVEL_300,
        subject: 'CMPUT',
      },
    }),
    prisma.course.create({
      data: {
        code: 'CMPUT 328',
        title: 'Visual Recognition',
        credits: 3,
        description: 'Introduction to computer vision and visual recognition systems.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [
            { type: 'COURSE', code: 'CMPUT 204' },
            { type: 'OR', conditions: [
              { type: 'COURSE', code: 'MATH 125' },
              { type: 'COURSE', code: 'MATH 127' },
            ]},
          ],
        },
        typicallyOffered: ['Winter'],
        level: CourseLevel.LEVEL_300,
        subject: 'CMPUT',
      },
    }),

    // 400-level courses
    prisma.course.create({
      data: {
        code: 'CMPUT 401',
        title: 'Software Process and Product Management',
        credits: 3,
        description: 'Project management for software development.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [{ type: 'COURSE', code: 'CMPUT 301' }],
        },
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_400,
        subject: 'CMPUT',
      },
    }),
    prisma.course.create({
      data: {
        code: 'CMPUT 455',
        title: 'Search, Knowledge, and Simulations',
        credits: 3,
        description: 'Techniques for search, knowledge representation, and simulation in AI.',
        prerequisiteFormula: {
          type: 'AND',
          conditions: [
            { type: 'COURSE', code: 'CMPUT 204' },
            { type: 'COURSE', code: 'CMPUT 272' },
          ],
        },
        typicallyOffered: ['Fall'],
        level: CourseLevel.LEVEL_400,
        subject: 'CMPUT',
      },
    }),

    // Math courses
    prisma.course.create({
      data: {
        code: 'MATH 125',
        title: 'Linear Algebra I',
        credits: 3,
        description: 'Systems of linear equations, matrices, and vector spaces.',
        prerequisiteFormula: null,
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_100,
        subject: 'MATH',
      },
    }),
    prisma.course.create({
      data: {
        code: 'STAT 151',
        title: 'Introduction to Applied Statistics I',
        credits: 3,
        description: 'Introduction to probability and statistical inference.',
        prerequisiteFormula: null,
        typicallyOffered: ['Fall', 'Winter'],
        level: CourseLevel.LEVEL_100,
        subject: 'STAT',
      },
    }),
  ])

  console.log(`✅ Created ${courses.length} courses\n`)

  // ============================================================================
  // SEED PROGRAMS
  // ============================================================================
  console.log('🎓 Seeding programs...')

  const honorsCS = await prisma.program.create({
    data: {
      code: 'honors-cs',
      name: 'BSc Honors in Computing Science',
      totalCredits: 120,
      requirements: {
        minCredits: 120,
        minCMPUTCredits: 60,
        minSeniorLevel: 18, // 300/400 level
      },
      specialRules: {
        exclusions: [
          { courses: ['CMPUT 174', 'CMPUT 114'], rule: 'Cannot take both' },
        ],
        substitutions: [
          { original: 'MATH 125', alternatives: ['MATH 127'], note: 'For honors students' },
        ],
      },
    },
  })

  const specializationCS = await prisma.program.create({
    data: {
      code: 'specialization-cs',
      name: 'BSc Specialization in Computing Science',
      totalCredits: 120,
      requirements: {
        minCredits: 120,
        minCMPUTCredits: 48,
        minSeniorLevel: 15,
      },
      specialRules: {
        exclusions: [
          { courses: ['CMPUT 174', 'CMPUT 114'], rule: 'Cannot take both' },
        ],
      },
    },
  })

  console.log(`✅ Created ${2} programs\n`)

  // ============================================================================
  // SEED REQUIREMENTS
  // ============================================================================
  console.log('📋 Seeding requirements...')

  // Honors CS Requirements
  const honorsRequirements = await Promise.all([
    prisma.requirement.create({
      data: {
        programId: honorsCS.id,
        name: 'Core CS Foundation',
        requirementType: RequirementType.REQUIRED,
        courses: ['CMPUT 174', 'CMPUT 175', 'CMPUT 201'],
        creditsNeeded: 9,
        levelFilter: [],
        orderIndex: 1,
      },
    }),
    prisma.requirement.create({
      data: {
        programId: honorsCS.id,
        name: 'Core CS Theory',
        requirementType: RequirementType.REQUIRED,
        courses: ['CMPUT 204', 'CMPUT 272', 'CMPUT 229'],
        creditsNeeded: 9,
        levelFilter: [],
        orderIndex: 2,
      },
    }),
    prisma.requirement.create({
      data: {
        programId: honorsCS.id,
        name: 'Software Engineering',
        requirementType: RequirementType.REQUIRED,
        courses: ['CMPUT 301'],
        creditsNeeded: 3,
        levelFilter: [],
        orderIndex: 3,
      },
    }),
    prisma.requirement.create({
      data: {
        programId: honorsCS.id,
        name: 'Advanced Algorithms',
        requirementType: RequirementType.CHOICE,
        courses: ['CMPUT 304', 'CMPUT 328', 'CMPUT 455'],
        chooseCount: 2,
        creditsNeeded: 6,
        levelFilter: ['300', '400'],
        orderIndex: 4,
      },
    }),
    prisma.requirement.create({
      data: {
        programId: honorsCS.id,
        name: 'Senior CMPUT Electives',
        requirementType: RequirementType.LEVEL_REQUIREMENT,
        courses: [],
        creditsNeeded: 18,
        levelFilter: ['300', '400'],
        subjectFilter: 'CMPUT',
        orderIndex: 5,
      },
    }),
    prisma.requirement.create({
      data: {
        programId: honorsCS.id,
        name: 'Math Requirements',
        requirementType: RequirementType.REQUIRED,
        courses: ['MATH 125', 'STAT 151'],
        creditsNeeded: 6,
        levelFilter: [],
        orderIndex: 6,
      },
    }),
  ])

  // Specialization CS Requirements (simplified)
  const specRequirements = await Promise.all([
    prisma.requirement.create({
      data: {
        programId: specializationCS.id,
        name: 'Core CS Foundation',
        requirementType: RequirementType.REQUIRED,
        courses: ['CMPUT 174', 'CMPUT 175', 'CMPUT 201', 'CMPUT 204'],
        creditsNeeded: 12,
        levelFilter: [],
        orderIndex: 1,
      },
    }),
    prisma.requirement.create({
      data: {
        programId: specializationCS.id,
        name: 'Senior CMPUT Electives',
        requirementType: RequirementType.LEVEL_REQUIREMENT,
        courses: [],
        creditsNeeded: 15,
        levelFilter: ['300', '400'],
        subjectFilter: 'CMPUT',
        orderIndex: 2,
      },
    }),
  ])

  console.log(`✅ Created ${honorsRequirements.length + specRequirements.length} requirements\n`)

  // ============================================================================
  // SEED SAMPLE STUDENT AND ROADMAP
  // ============================================================================
  console.log('👤 Seeding sample student...')

  const sampleStudent = await prisma.student.create({
    data: {
      name: 'Alice Johnson',
      email: 'alice.johnson@ualberta.ca',
      startingYear: 2024,
      programCode: 'honors-cs',
      specialization: 'Artificial Intelligence',
    },
  })

  console.log('✅ Created sample student\n')

  console.log('🗺️  Seeding sample roadmap...')

  const sampleRoadmap = await prisma.roadmap.create({
    data: {
      studentId: sampleStudent.id,
      programId: honorsCS.id,
      name: 'My 4-Year CS Plan',
      isActive: true,
    },
  })

  // Year 1 - Fall
  await prisma.roadmapCourse.createMany({
    data: [
      {
        roadmapId: sampleRoadmap.id,
        courseCode: 'CMPUT 174',
        semester: 1,
        year: 1,
        term: Term.FALL,
        status: CourseStatus.COMPLETED,
        satisfiesRequirements: [honorsRequirements[0].id], // Core CS Foundation
      },
      {
        roadmapId: sampleRoadmap.id,
        courseCode: 'MATH 125',
        semester: 1,
        year: 1,
        term: Term.FALL,
        status: CourseStatus.COMPLETED,
        satisfiesRequirements: [honorsRequirements[5].id], // Math Requirements
      },
    ],
  })

  // Year 1 - Winter
  await prisma.roadmapCourse.createMany({
    data: [
      {
        roadmapId: sampleRoadmap.id,
        courseCode: 'CMPUT 175',
        semester: 2,
        year: 1,
        term: Term.WINTER,
        status: CourseStatus.IN_PROGRESS,
        satisfiesRequirements: [honorsRequirements[0].id],
      },
      {
        roadmapId: sampleRoadmap.id,
        courseCode: 'STAT 151',
        semester: 2,
        year: 1,
        term: Term.WINTER,
        status: CourseStatus.IN_PROGRESS,
        satisfiesRequirements: [honorsRequirements[5].id],
      },
    ],
  })

  // Year 2 - Fall (planned)
  await prisma.roadmapCourse.createMany({
    data: [
      {
        roadmapId: sampleRoadmap.id,
        courseCode: 'CMPUT 201',
        semester: 3,
        year: 2,
        term: Term.FALL,
        status: CourseStatus.PLANNED,
        satisfiesRequirements: [honorsRequirements[0].id],
      },
      {
        roadmapId: sampleRoadmap.id,
        courseCode: 'CMPUT 204',
        semester: 3,
        year: 2,
        term: Term.FALL,
        status: CourseStatus.PLANNED,
        satisfiesRequirements: [honorsRequirements[1].id], // Core CS Theory
      },
    ],
  })

  console.log('✅ Created sample roadmap with courses\n')

  // ============================================================================
  // SEED SAMPLE USER
  // ============================================================================
  console.log('🔐 Seeding sample user...')

  await prisma.user.create({
    data: {
      email: 'alice.johnson@ualberta.ca',
      name: 'Alice Johnson',
      password: '$2b$10$abcdefghijklmnopqrstuvwxyz', // Placeholder - use bcrypt in production
      role: 'STUDENT',
    },
  })

  console.log('✅ Created sample user\n')

  // ============================================================================
  // SUMMARY
  // ============================================================================
  console.log('📊 Seed Summary:')
  console.log('================')
  console.log(`Courses: ${courses.length}`)
  console.log(`Programs: 2`)
  console.log(`Requirements: ${honorsRequirements.length + specRequirements.length}`)
  console.log(`Students: 1`)
  console.log(`Roadmaps: 1`)
  console.log(`Users: 1`)
  console.log('\n✨ Database seeding complete!\n')
}

main()
  .catch((e) => {
    console.error('❌ Error seeding database:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
