const fs = require('fs');
const path = require('path');

// Function to convert @/lib imports to relative imports
function fixImports(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Find all @/lib imports
  const libImportRegex = /import\s+.*?\s+from\s+['"]@\/lib\/([^'"]+)['"]/g;
  const matches = [...content.matchAll(libImportRegex)];
  
  if (matches.length === 0) return false;
  
  let newContent = content;
  
  // Calculate relative path from file to lib folder
  const fileDir = path.dirname(filePath);
  const libPath = path.resolve(__dirname, 'lib');
  const relativePath = path.relative(fileDir, libPath).replace(/\\/g, '/');
  
  // Replace all @/lib imports with relative imports
  newContent = newContent.replace(libImportRegex, (match, libFile) => {
    const relativeImport = `import ${match.match(/import\s+(.*?)\s+from/)[1]} from '${relativePath}/${libFile}'`;
    return relativeImport;
  });
  
  fs.writeFileSync(filePath, newContent);
  console.log(`Fixed imports in: ${filePath}`);
  return true;
}

// Function to recursively find all TypeScript/JavaScript files
function findFiles(dir, extensions = ['.ts', '.tsx', '.js', '.jsx']) {
  const files = [];
  
  function traverse(currentDir) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        traverse(fullPath);
      } else if (stat.isFile() && extensions.some(ext => item.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  }
  
  traverse(dir);
  return files;
}

// Main execution
const frontendDir = __dirname;
const files = findFiles(frontendDir);

let fixedCount = 0;
for (const file of files) {
  if (fixImports(file)) {
    fixedCount++;
  }
}

console.log(`Fixed imports in ${fixedCount} files`);
