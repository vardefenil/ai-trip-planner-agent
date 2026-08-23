// Types for the travel planner

export interface ParsedTrip {
  origin: string;
  destination: string;
  budget_total: number;
  duration_days: number;
  traveler_count: number;
  vibe: string;
  travel_dates: string | null;
}

export interface BudgetAllocation {
  stay: number;
  transport: number;
  food: number;
  local_rental: number;
  buffer: number;
  destination_type: string;
}

export interface StayOption {
  name: string;
  type: string;
  price_per_night: number;
  total_stay_cost: number;
  rating: number;
  address: string;
  booking_url: string;
  image_url: string | null;
  amenities: string[];
  review_summary: string | null;
}

export interface TransportOption {
  mode: string;
  provider: string;
  from_city: string;
  to_city: string;
  price_per_person: number;
  total_transport_cost: number;
  duration: string;
  booking_url: string;
  departure_time: string | null;
}

export interface RentalOption {
  name: string;
  type: string;
  price_per_day: number;
  total_rental_cost: number;
  rating: number;
  address: string;
  phone: string | null;
  maps_url: string | null;
}

export interface DayPlan {
  day: number;
  title: string;
  activities: string[];
  meals: string[];
  estimated_cost: number;
}

export interface TripPackage {
  package_id: number;
  title: string;
  tagline: string;
  stay: StayOption;
  transport: TransportOption;
  rental: RentalOption | null;
  itinerary: DayPlan[];
  total_cost: number;
  budget_utilisation_pct: number;
  highlights: string[];
  why_this_one: string;
  tier: string;
}

export interface BookingLink {
  label: string;
  url: string;
  provider: string;
}

export interface BookingSummary {
  selected_package: TripPackage;
  confirmation_message: string;
  booking_links: BookingLink[];
  tips: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type?: 'text' | 'packages' | 'booking' | 'progress';
  packages?: TripPackage[];
  bookingSummary?: BookingSummary;
  parsedTrip?: ParsedTrip;
  budgetAllocation?: BudgetAllocation;
}

export interface PipelineStage {
  id: string;
  label: string;
  icon: string;
  status: 'idle' | 'running' | 'done' | 'error';
  message?: string;
}

export interface SSEEvent {
  type: string;
  stage?: string;
  message?: string;
  data?: Record<string, unknown>;
  logs?: string[];
  session_id?: string;
  full_state?: Record<string, unknown>;
}

export interface SavedSession {
  id: string;
  title: string;
  destination?: string;
  created_at: string;
  updated_at: string;
}
