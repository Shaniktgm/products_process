const fs = require('fs')
const path = require('path')
const sqlite3 = require('sqlite3').verbose()

const db = new sqlite3.Database('./multi_platform_products.db')

// Safe color keywords to extract from title/description
const SAFE_COLORS = [
  'white', 'black', 'gray', 'grey', 'beige', 'ivory', 'cream', 'tan', 'brown',
  'navy', 'blue', 'light blue', 'dark blue', 'royal blue', 'sky blue',
  'red', 'burgundy', 'maroon', 'pink', 'rose', 'coral',
  'green', 'sage', 'mint', 'forest green', 'olive', 'emerald',
  'purple', 'lavender', 'violet', 'plum',
  'yellow', 'gold', 'champagne', 'silver', 'charcoal'
]

// Material keywords to extract
const MATERIAL_KEYWORDS = {
  'cotton': ['cotton', '100% cotton'],
  'egyptian cotton': ['egyptian cotton', 'egyptian'],
  'bamboo': ['bamboo', 'viscose made from bamboo', 'bamboo viscose'],
  'lyocell': ['lyocell', 'tencel', 'eucalyptus'],
  'linen': ['linen', 'flax', 'belgian linen'],
  'flannel': ['flannel', 'brushed cotton'],
  'microfiber': ['microfiber', 'microfiber'],
  'silk': ['silk', 'mulberry silk'],
  'polyester': ['polyester', 'poly'],
  'modal': ['modal']
}

// Weave keywords to extract
const WEAVE_KEYWORDS = {
  'percale': ['percale'],
  'sateen': ['sateen'],
  'flannel': ['flannel', 'brushed'],
  'linen': ['linen weave'],
  'jersey': ['jersey', 'knit'],
  'twill': ['twill']
}

function extractMaterial(text) {
  if (!text) return null
  
  const lowerText = text.toLowerCase()
  
  for (const [material, keywords] of Object.entries(MATERIAL_KEYWORDS)) {
    for (const keyword of keywords) {
      if (lowerText.includes(keyword)) {
        return material
      }
    }
  }
  
  return null
}

function extractWeave(text) {
  if (!text) return null
  
  const lowerText = text.toLowerCase()
  
  for (const [weave, keywords] of Object.entries(WEAVE_KEYWORDS)) {
    for (const keyword of keywords) {
      if (lowerText.includes(keyword)) {
        return weave
      }
    }
  }
  
  return null
}

function extractColor(text) {
  if (!text) return null
  
  const lowerText = text.toLowerCase()
  
  for (const color of SAFE_COLORS) {
    if (lowerText.includes(color)) {
      return color
    }
  }
  
  return null
}

function extractDimensions(text) {
  if (!text) return null
  
  // Look for patterns like "90x104", "102 x 108", "90 x 104 inches"
  const dimensionPattern = /(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)/i
  const match = text.match(dimensionPattern)
  
  if (match) {
    const width = parseFloat(match[1])
    const length = parseFloat(match[2])
    return JSON.stringify({ width, length })
  }
  
  return null
}

async function fillMissingFields() {
  try {
    console.log('Starting to fill missing fields...')
    
    // Get all products
    const products = await new Promise((resolve, reject) => {
      db.all(`
        SELECT id, title, description, ingredients, material, color, dimensions, weight
        FROM products 
        WHERE is_active = 1
      `, [], (err, rows) => {
        if (err) reject(err)
        else resolve(rows)
      })
    })
    
    console.log(`Found ${products.length} products to process`)
    
    const changes = []
    
    for (const product of products) {
      const updates = {}
      const changeLog = { id: product.id, title: product.title, changes: [] }
      
      // Combine text sources for analysis
      const combinedText = [
        product.title,
        product.description,
        product.ingredients
      ].filter(Boolean).join(' ')
      
      // Fill material if missing
      if (!product.material || product.material.trim() === '') {
        const extractedMaterial = extractMaterial(combinedText)
        if (extractedMaterial) {
          updates.material = extractedMaterial
          changeLog.changes.push(`material: null -> "${extractedMaterial}"`)
        }
      }
      
      // Fill color if missing
      if (!product.color || product.color.trim() === '') {
        const extractedColor = extractColor(combinedText)
        if (extractedColor) {
          updates.color = extractedColor
          changeLog.changes.push(`color: null -> "${extractedColor}"`)
        }
      }
      
      // Fill dimensions if missing
      if (!product.dimensions || product.dimensions.trim() === '' || product.dimensions === '{}') {
        const extractedDimensions = extractDimensions(combinedText)
        if (extractedDimensions) {
          updates.dimensions = extractedDimensions
          changeLog.changes.push(`dimensions: null -> "${extractedDimensions}"`)
        }
      }
      
      // Fill ingredients if missing (copy from material)
      if (!product.ingredients || product.ingredients.trim() === '') {
        const materialToUse = updates.material || product.material
        if (materialToUse) {
          updates.ingredients = materialToUse
          changeLog.changes.push(`ingredients: null -> "${materialToUse}"`)
        }
      }
      
      // Apply updates if any
      if (Object.keys(updates).length > 0) {
        const setClause = Object.keys(updates).map(key => `${key} = ?`).join(', ')
        const values = Object.values(updates)
        
        await new Promise((resolve, reject) => {
          db.run(`
            UPDATE products 
            SET ${setClause}
            WHERE id = ?
          `, [...values, product.id], function(err) {
            if (err) reject(err)
            else resolve()
          })
        })
        
        changes.push(changeLog)
        console.log(`Updated product ${product.id}: ${changeLog.changes.join(', ')}`)
      }
    }
    
    // Save change log
    const changeLogPath = path.join(__dirname, 'field-fill-changes.json')
    fs.writeFileSync(changeLogPath, JSON.stringify(changes, null, 2))
    
    console.log(`\n✅ Completed filling missing fields`)
    console.log(`📊 Summary:`)
    console.log(`  - Products processed: ${products.length}`)
    console.log(`  - Products updated: ${changes.length}`)
    console.log(`  - Change log saved to: ${changeLogPath}`)
    
    // Show summary by field
    const fieldSummary = {}
    changes.forEach(change => {
      change.changes.forEach(changeStr => {
        const field = changeStr.split(':')[0]
        fieldSummary[field] = (fieldSummary[field] || 0) + 1
      })
    })
    
    console.log(`\n📈 Fields updated:`)
    Object.entries(fieldSummary).forEach(([field, count]) => {
      console.log(`  - ${field}: ${count} products`)
    })
    
  } catch (error) {
    console.error('Error filling missing fields:', error)
  } finally {
    db.close()
  }
}

fillMissingFields()
