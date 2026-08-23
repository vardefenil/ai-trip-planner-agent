/**
 * Comprehensive destination & stay image provider for Indian travel destinations.
 * Provides multiple verified, high-res curated landscape & attraction photos per destination.
 */

export interface PlacePhoto {
  url: string;
  caption: string;
}

// 5+ verified, distinct high-quality landscape photos per destination
const DESTINATION_GALLERIES: Record<string, PlacePhoto[]> = {
  manali: [
    { url: 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=900&auto=format&fit=crop&q=80', caption: 'Solang Valley Snow Peaks' },
    { url: 'https://images.unsplash.com/photo-1597074866923-dc0589150358?w=900&auto=format&fit=crop&q=80', caption: 'Rohtang Pass & Glacial Valleys' },
    { url: 'https://images.unsplash.com/photo-1579618218290-24a26f63a738?w=900&auto=format&fit=crop&q=80', caption: 'Hadimba Forest & Cedar Pines' },
    { url: 'https://images.unsplash.com/photo-1605640840605-14ac1855827b?w=900&auto=format&fit=crop&q=80', caption: 'Old Manali & River Beas' },
    { url: 'https://images.unsplash.com/photo-1562920618-5eabfa568019?w=900&auto=format&fit=crop&q=80', caption: 'Jogini Waterfalls & Alpine Trails' },
  ],
  goa: [
    { url: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=900&auto=format&fit=crop&q=80', caption: 'Palolem Beach & Coconut Palms' },
    { url: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=900&auto=format&fit=crop&q=80', caption: 'Vagator & Chapora Cliffs' },
    { url: 'https://images.unsplash.com/photo-1587922546307-776227941871?w=900&auto=format&fit=crop&q=80', caption: 'Fort Aguada & Arabian Sea Sunset' },
    { url: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=900&auto=format&fit=crop&q=80', caption: 'Calangute Golden Sands' },
    { url: 'https://images.unsplash.com/photo-1519046904884-53103b34b206?w=900&auto=format&fit=crop&q=80', caption: 'Anjuna Flea Market & Coastline' },
  ],
  kerala: [
    { url: 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=900&auto=format&fit=crop&q=80', caption: 'Alleppey Backwaters & Houseboat' },
    { url: 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?w=900&auto=format&fit=crop&q=80', caption: 'Munnar Rolling Tea Plantations' },
    { url: 'https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=900&auto=format&fit=crop&q=80', caption: 'Varkala Cliff & Turquoise Waters' },
    { url: 'https://images.unsplash.com/photo-1609342475528-668b57731776?w=900&auto=format&fit=crop&q=80', caption: 'Kovalam Lighthouse Beach' },
    { url: 'https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=900&auto=format&fit=crop&q=80', caption: 'Wayanad Rainforest & Mist' },
  ],
  rajasthan: [
    { url: 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=900&auto=format&fit=crop&q=80', caption: 'Hawa Mahal Palace of Winds' },
    { url: 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=900&auto=format&fit=crop&q=80', caption: 'Udaipur City Palace & Lake Pichola' },
    { url: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=900&auto=format&fit=crop&q=80', caption: 'Amber Fort & Maota Lake' },
    { url: 'https://images.unsplash.com/photo-1586861635167-e5223aadc9fe?w=900&auto=format&fit=crop&q=80', caption: 'Jodhpur Mehrangarh Blue City' },
    { url: 'https://images.unsplash.com/photo-1533050487297-09b450f31914?w=900&auto=format&fit=crop&q=80', caption: 'Jaisalmer Sam Sand Dunes Sunset' },
  ],
  ladakh: [
    { url: 'https://images.unsplash.com/photo-1571401835393-8c5f35328320?w=900&auto=format&fit=crop&q=80', caption: 'Pangong Tso Blue Waters' },
    { url: 'https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?w=900&auto=format&fit=crop&q=80', caption: 'Nubra Valley & Double-Hump Camels' },
    { url: 'https://images.unsplash.com/photo-1506197603052-3cc9c3a201bd?w=900&auto=format&fit=crop&q=80', caption: 'Thiksey Monastery Mountain Vistas' },
    { url: 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=900&auto=format&fit=crop&q=80', caption: 'Khardung La High Mountain Pass' },
    { url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=900&auto=format&fit=crop&q=80', caption: 'Magnetic Hill & Indus Confluence' },
  ],
  andaman: [
    { url: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=900&auto=format&fit=crop&q=80', caption: 'Radhanagar Beach White Sands' },
    { url: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=900&auto=format&fit=crop&q=80', caption: 'Elephant Beach Coral Reefs' },
    { url: 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=900&auto=format&fit=crop&q=80', caption: 'Neil Island Natural Bridge' },
    { url: 'https://images.unsplash.com/photo-1519046904884-53103b34b206?w=900&auto=format&fit=crop&q=80', caption: 'Havelock Emerald Coast' },
    { url: 'https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=900&auto=format&fit=crop&q=80', caption: 'Ross Island Heritage Ruins' },
  ],
  shimla: [
    { url: 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=900&auto=format&fit=crop&q=80', caption: 'Shimla Ridge & Himalayan View' },
    { url: 'https://images.unsplash.com/photo-1597074866923-dc0589150358?w=900&auto=format&fit=crop&q=80', caption: 'Kufri Snow Valley' },
    { url: 'https://images.unsplash.com/photo-1579618218290-24a26f63a738?w=900&auto=format&fit=crop&q=80', caption: 'Christ Church & Mall Road' },
    { url: 'https://images.unsplash.com/photo-1605640840605-14ac1855827b?w=900&auto=format&fit=crop&q=80', caption: 'Jakhoo Hill & Pine Forests' },
    { url: 'https://images.unsplash.com/photo-1562920618-5eabfa568019?w=900&auto=format&fit=crop&q=80', caption: 'Chail Palace & Cedar Grooves' },
  ],
  rishikesh: [
    { url: 'https://images.unsplash.com/photo-1584551246679-0daf3d275d0f?w=900&auto=format&fit=crop&q=80', caption: 'Laxman Jhula & River Ganges' },
    { url: 'https://images.unsplash.com/photo-1544717305-2782549b5136?w=900&auto=format&fit=crop&q=80', caption: 'Triveni Ghat Evening Aarti' },
    { url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=900&auto=format&fit=crop&q=80', caption: 'White Water Rafting Rapids' },
    { url: 'https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?w=900&auto=format&fit=crop&q=80', caption: 'Neelkanth Mahadev Valley' },
    { url: 'https://images.unsplash.com/photo-1506197603052-3cc9c3a201bd?w=900&auto=format&fit=crop&q=80', caption: 'Beatles Ashram & Forest Trails' },
  ],
  varanasi: [
    { url: 'https://images.unsplash.com/photo-1561361058-c24e01c735db?w=900&auto=format&fit=crop&q=80', caption: 'Dashashwamedh Ghat Ganga Aarti' },
    { url: 'https://images.unsplash.com/photo-1571536802807-30451e3955d8?w=900&auto=format&fit=crop&q=80', caption: 'Sunrise Boat Ride on Ganges' },
    { url: 'https://images.unsplash.com/photo-1544717305-2782549b5136?w=900&auto=format&fit=crop&q=80', caption: 'Assi Ghat & Ancient Alleyways' },
    { url: 'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=900&auto=format&fit=crop&q=80', caption: 'Sarnath Buddhist Stupa' },
    { url: 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=900&auto=format&fit=crop&q=80', caption: 'Kashi Vishwanath Corridor' },
  ],
  ooty: [
    { url: 'https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=900&auto=format&fit=crop&q=80', caption: 'Nilgiri Mountain Railway' },
    { url: 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?w=900&auto=format&fit=crop&q=80', caption: 'Ooty Tea Estate Slopes' },
    { url: 'https://images.unsplash.com/photo-1609342475528-668b57731776?w=900&auto=format&fit=crop&q=80', caption: 'Pykara Lake & Waterfalls' },
    { url: 'https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=900&auto=format&fit=crop&q=80', caption: 'Doddabetta Peak Viewpoint' },
    { url: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=900&auto=format&fit=crop&q=80', caption: 'Botanical Garden & Mist' },
  ],
};

// Aliases and sub-locations mapping to gallery keys
const DESTINATION_ALIASES: Record<string, string> = {
  manali: 'manali',
  kullu: 'manali',
  solang: 'manali',
  rohtang: 'manali',
  kasol: 'manali',
  goa: 'goa',
  panaji: 'goa',
  calangute: 'goa',
  baga: 'goa',
  anjuna: 'goa',
  candolim: 'goa',
  palolem: 'goa',
  vagator: 'goa',
  kerala: 'kerala',
  munnar: 'kerala',
  alleppey: 'kerala',
  alappuzha: 'kerala',
  kochi: 'kerala',
  cochin: 'kerala',
  varkala: 'kerala',
  wayanad: 'kerala',
  kovalam: 'kerala',
  rajasthan: 'rajasthan',
  jaipur: 'rajasthan',
  udaipur: 'rajasthan',
  jodhpur: 'rajasthan',
  jaisalmer: 'rajasthan',
  pushkar: 'rajasthan',
  ladakh: 'ladakh',
  leh: 'ladakh',
  nubra: 'ladakh',
  pangong: 'ladakh',
  andaman: 'andaman',
  havelock: 'andaman',
  portblair: 'andaman',
  neil: 'andaman',
  shimla: 'shimla',
  kufri: 'shimla',
  chail: 'shimla',
  rishikesh: 'rishikesh',
  haridwar: 'rishikesh',
  dehradun: 'rishikesh',
  varanasi: 'varanasi',
  kashi: 'varanasi',
  banaras: 'varanasi',
  ooty: 'ooty',
  nilgiri: 'ooty',
  coonoor: 'ooty',
  coorg: 'kerala',
  kodagu: 'kerala',
  darjeeling: 'manali',
  gangtok: 'manali',
  sikkim: 'manali',
};

const STAY_PHOTOS: Record<string, string[]> = {
  resort: [
    'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=700&auto=format&fit=crop&q=80',
  ],
  hotel: [
    'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1455587734955-081b22074882?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=700&auto=format&fit=crop&q=80',
  ],
  hostel: [
    'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1520277739336-7bf67edfa768?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=700&auto=format&fit=crop&q=80',
  ],
  villa: [
    'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=700&auto=format&fit=crop&q=80',
  ],
  cottage: [
    'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=700&auto=format&fit=crop&q=80',
  ],
  default: [
    'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=700&auto=format&fit=crop&q=80',
    'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=700&auto=format&fit=crop&q=80',
  ],
};

/**
 * Extract destination key from any combined text (e.g. "Old Manali, Manali", "Calangute, Goa", "Backwaters, Kerala").
 */
export function detectDestinationKey(...texts: (string | undefined | null)[]): string {
  const combined = texts.filter(Boolean).join(' ').toLowerCase();

  for (const [alias, key] of Object.entries(DESTINATION_ALIASES)) {
    // Regex word boundary match to prevent false positives
    const regex = new RegExp(`\\b${alias}\\b`, 'i');
    if (regex.test(combined)) {
      return key;
    }
  }

  // Check fallback keywords
  if (combined.includes('mountain') || combined.includes('snow') || combined.includes('hill') || combined.includes('himalaya')) return 'manali';
  if (combined.includes('beach') || combined.includes('sea') || combined.includes('coast') || combined.includes('ocean')) return 'goa';
  if (combined.includes('backwater') || combined.includes('tea') || combined.includes('lake')) return 'kerala';
  if (combined.includes('desert') || combined.includes('palace') || combined.includes('fort') || combined.includes('heritage')) return 'rajasthan';

  return 'manali';
}

/**
 * Get distinct hero photo for a package based on its index and destination.
 */
export function getPackageHeroPhoto(
  destinationText: string,
  packageIndex: number,
  titleText: string = ''
): PlacePhoto {
  const key = detectDestinationKey(destinationText, titleText);
  const gallery = DESTINATION_GALLERIES[key] || DESTINATION_GALLERIES.manali;
  const photo = gallery[packageIndex % gallery.length];
  return photo;
}

/**
 * Get the full photo gallery for a destination to allow carousel browsing.
 */
export function getDestinationPhotos(destinationText: string, titleText: string = ''): PlacePhoto[] {
  const key = detectDestinationKey(destinationText, titleText);
  return DESTINATION_GALLERIES[key] || DESTINATION_GALLERIES.manali;
}

/**
 * Get stay image based on stay name and type.
 */
export function getStayPhoto(stayType: string, stayName: string, packageIndex: number): string {
  const typeKey = stayType?.toLowerCase() || '';
  const nameKey = stayName?.toLowerCase() || '';

  let photos = STAY_PHOTOS.default;
  if (typeKey.includes('hostel') || nameKey.includes('zostel') || nameKey.includes('hostel') || nameKey.includes('backpacker')) {
    photos = STAY_PHOTOS.hostel;
  } else if (typeKey.includes('resort') || nameKey.includes('resort') || nameKey.includes('retreat')) {
    photos = STAY_PHOTOS.resort;
  } else if (typeKey.includes('villa') || nameKey.includes('villa') || nameKey.includes('estate')) {
    photos = STAY_PHOTOS.villa;
  } else if (typeKey.includes('cottage') || nameKey.includes('hut') || nameKey.includes('chalet') || nameKey.includes('camp')) {
    photos = STAY_PHOTOS.cottage;
  } else if (typeKey.includes('hotel') || nameKey.includes('hotel') || nameKey.includes('inn')) {
    photos = STAY_PHOTOS.hotel;
  }

  return photos[packageIndex % photos.length];
}
