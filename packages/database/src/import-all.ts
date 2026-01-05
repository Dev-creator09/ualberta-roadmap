/**
 * Import all data from JSON files
 *
 * Orchestrates the import of courses and programs in the correct order.
 * Courses must be imported first since programs reference them.
 */

import { importCourses } from './import-courses'
import { importPrograms } from './import-programs'

async function importAll() {
  console.log('=' .repeat(70))
  console.log('🚀 Starting complete data import')
  console.log('='.repeat(70))
  console.log()

  const startTime = Date.now()
  let coursesImported = false
  let programsImported = false

  try {
    // Step 1: Import courses
    console.log('Step 1/2: Importing courses...')
    console.log('-'.repeat(70))
    await importCourses()
    coursesImported = true
    console.log()

    // Step 2: Import programs
    console.log('Step 2/2: Importing programs...')
    console.log('-'.repeat(70))
    await importPrograms()
    programsImported = true
    console.log()

    // Final summary
    const duration = ((Date.now() - startTime) / 1000).toFixed(2)

    console.log('=' .repeat(70))
    console.log('✨ Complete Import Summary')
    console.log('='.repeat(70))
    console.log(`✅ Courses: ${coursesImported ? 'SUCCESS' : 'FAILED'}`)
    console.log(`✅ Programs: ${programsImported ? 'SUCCESS' : 'FAILED'}`)
    console.log(`⏱️  Total time: ${duration}s`)
    console.log('='.repeat(70))
    console.log()
    console.log('🎉 All data imported successfully!')
    console.log()
  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2)

    console.log()
    console.log('=' .repeat(70))
    console.log('❌ Import Failed')
    console.log('='.repeat(70))
    console.log(`Courses: ${coursesImported ? 'SUCCESS' : 'FAILED'}`)
    console.log(`Programs: ${programsImported ? 'FAILED' : 'NOT ATTEMPTED'}`)
    console.log(`Total time: ${duration}s`)
    console.log('='.repeat(70))
    console.log()

    if (error instanceof Error) {
      console.error('Error:', error.message)
    } else {
      console.error('Error:', error)
    }

    console.log()
    console.log('💡 Troubleshooting tips:')
    console.log('  1. Make sure course-data.json and degree-requirements.json exist in the project root')
    console.log('  2. Verify the JSON files have valid structure')
    console.log('  3. Check that the database is running and accessible')
    console.log('  4. Ensure DATABASE_URL is set correctly in .env')
    console.log()

    process.exit(1)
  }
}

// Run import if this file is executed directly
if (require.main === module) {
  importAll()
    .then(() => process.exit(0))
    .catch(() => process.exit(1))
}

export { importAll }
