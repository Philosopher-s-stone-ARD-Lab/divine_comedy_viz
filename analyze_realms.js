const fs = require('fs');
const data = JSON.parse(fs.readFileSync('src/data/network-data.json', 'utf-8'));

// 1. Check link object fields
console.log('=== LINK OBJECT FIELDS ===');
console.log('Fields in link objects:', Object.keys(data.links[0]));
console.log('\nExample links:');
console.log(JSON.stringify(data.links.slice(0, 5), null, 2));

// 2. Check if links have realm_association
console.log('\n=== REALM ASSOCIATION IN LINKS ===');
const linksWithRealm = data.links.filter(l => l.realm_association);
console.log(`Links with realm_association: ${linksWithRealm.length} out of ${data.links.length}`);

// 3. Count characters by realm_association combinations
console.log('\n=== CHARACTERS BY REALM ASSOCIATIONS ===');

// Create a map of realm combinations
const realmCombinations = {};
data.nodes.forEach(node => {
  const key = JSON.stringify(node.realm_association.sort());
  if (!realmCombinations[key]) {
    realmCombinations[key] = [];
  }
  realmCombinations[key].push(node.id);
});

// Sort by combination and display
const combinations = Object.entries(realmCombinations)
  .sort((a, b) => b[1].length - a[1].length);

combinations.forEach(([key, characters]) => {
  const realms = JSON.parse(key);
  console.log(`\n${realms.join(' + ')} (${characters.length} characters):`);
  characters.forEach(c => console.log(`  - ${c}`));
});

// 4. Summary statistics
console.log('\n=== SUMMARY STATISTICS ===');
console.log(`Total nodes: ${data.nodes.length}`);
console.log(`Total links: ${data.links.length}`);

// Count specific combinations
const onlyInferno = data.nodes.filter(n => 
  n.realm_association.length === 1 && n.realm_association[0] === 'Inferno'
).length;
const onlyPurgatorio = data.nodes.filter(n => 
  n.realm_association.length === 1 && n.realm_association[0] === 'Purgatorio'
).length;
const onlyParadiso = data.nodes.filter(n => 
  n.realm_association.length === 1 && n.realm_association[0] === 'Paradiso'
).length;
const multipleRealms = data.nodes.filter(n => 
  n.realm_association.length > 1
).length;

console.log(`\nCharacters with ONLY Inferno: ${onlyInferno}`);
console.log(`Characters with ONLY Purgatorio: ${onlyPurgatorio}`);
console.log(`Characters with ONLY Paradiso: ${onlyParadiso}`);
console.log(`Characters with MULTIPLE realms: ${multipleRealms}`);
