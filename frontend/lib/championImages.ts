const CDN_BASE = 'https://ddragon.leagueoflegends.com/cdn/img/champion/loading'

const SPECIAL_SLUGS: Record<string, string> = {
  "Cho'Gath": 'Chogath',
  'Dr. Mundo': 'DrMundo',
  "Kha'Zix": 'Khazix',
  "Kog'Maw": 'KogMaw',
  "LeBlanc": 'Leblanc',
  "Master Yi": 'MasterYi',
  "Miss Fortune": 'MissFortune',
  "Nunu & Willump": 'Nunu',
  "Rek'Sai": 'RekSai',
  "Tahm Kench": 'TahmKench',
  "Twisted Fate": 'TwistedFate',
  "Vel'Koz": 'Velkoz',
  "Wukong": 'MonkeyKing',
  "Xin Zhao": 'XinZhao',
  "Aurelion Sol": 'AurelionSol',
  'Jarvan IV': 'JarvanIV',
  'Renata Glasc': 'Renata',
  'Lee Sin': 'LeeSin',
  'Lucian': 'Lucian',
  "Kai'Sa": 'Kaisa',
  "Bel'Veth": 'Belveth',
}

function toDataDragonSlug(name: string): string {
  if (!name) return 'Aatrox'
  const trimmed = name.trim()
  if (SPECIAL_SLUGS[trimmed]) {
    return SPECIAL_SLUGS[trimmed]
  }
  // Remove non-letter characters and capitalize each word
  const lettersOnly = trimmed.replace(/[^a-zA-Z0-9 ]/g, ' ')
  const words = lettersOnly
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
  return words.join('')
}

export function getChampionImageUrl(name: string, variant: 'splash' | 'loading' = 'loading'): string {
  const slug = toDataDragonSlug(name)
  const base =
    variant === 'splash'
      ? 'https://ddragon.leagueoflegends.com/cdn/img/champion/splash'
      : CDN_BASE
  return `${base}/${slug}_0.jpg`
}

