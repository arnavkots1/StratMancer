// Test champion name transformation
const names = ['Mel', 'Yunara', 'Aurora', 'Smolder', 'Fiddlesticks'];

function getChampionImageName(championName) {
  // Remove all non-alphanumeric characters and spaces
  return championName.replace(/[^a-zA-Z0-9]/g, '');
}

names.forEach(name => {
  const transformed = getChampionImageName(name);
  console.log(`${name} -> ${transformed}`);
  console.log(`URL: https://ddragon.leagueoflegends.com/cdn/15.20.1/img/champion/${transformed}.png`);
});

