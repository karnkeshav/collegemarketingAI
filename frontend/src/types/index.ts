export interface State {
  id: number
  name: string
  code: string
}

export interface College {
  id: number
  name: string
  state_id: number
  state_name: string
  city: string
  college_type: string
  streams: string
  website: string
  address: string
  aicte_code: string
  naac_grade: string
  scrape_status: 'pending' | 'scraping' | 'done' | 'failed'
  last_scraped: string | null
  contact_count: number
  created_at: string
}

export interface Contact {
  id: number
  college_id: number
  college_name: string
  state_name: string
  city: string
  college_type: string
  name: string
  role: string
  email: string
  department: string
  phone: string
  source_url: string
  validation_status: 'unvalidated' | 'valid' | 'invalid'
  mx_valid: boolean
  is_unsubscribed: boolean
  campaigns_sent: number
  created_at: string
}

export interface Campaign {
  id: number
  name: string
  subject: string
  template_filename: string
  template_html?: string
  status: 'draft' | 'sending' | 'sent' | 'paused'
  created_at: string
  sent_at: string | null
  total_recipients: number
  sent_count: number
  bounced_count: number
  failed_count: number
}

export interface CampaignSend {
  id: number
  campaign_id: number
  contact_id: number
  contact_email: string
  contact_name: string
  college_name: string
  role: string
  status: 'pending' | 'sent' | 'bounced' | 'failed'
  sent_at: string | null
  error_message: string
  bounce_detected_at: string | null
}

export interface OverviewStats {
  total_colleges: number
  total_contacts: number
  validated_contacts: number
  invalid_contacts: number
  total_campaigns: number
  emails_sent: number
  emails_bounced: number
  by_state: Array<{ state: string; code: string; colleges: number; contacts: number }>
  by_role: Array<{ role: string; count: number }>
}

export interface ScrapeProgress {
  status: 'idle' | 'running' | 'done' | 'failed'
  done: number
  total: number
  log: string[]
}
