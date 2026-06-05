# Module 12: Lead & Marketing Analytics — Frontend Integration Spec

> Lead tracking, marketing campaign management, and conversion analytics.
> Replicates the Excel "Аналитка по рекламе" and "Маркетинг" sheets.
> Requires new database tables for leads and marketing campaigns.

---

## Endpoints Overview

| # | Method | Path | Description |
|---|--------|------|-------------|
| 1 | POST | `/api/v1/leads` | Create a new lead |
| 2 | GET | `/api/v1/leads` | List leads with filters |
| 3 | GET | `/api/v1/leads/{lead_id}` | Get lead detail |
| 4 | PATCH | `/api/v1/leads/{lead_id}` | Update lead status/info |
| 5 | POST | `/api/v1/leads/{lead_id}/convert` | Convert lead to rental |
| 6 | POST | `/api/v1/marketing-campaigns` | Create marketing campaign |
| 7 | GET | `/api/v1/marketing-campaigns` | List campaigns |
| 8 | PATCH | `/api/v1/marketing-campaigns/{campaign_id}` | Update campaign |
| 9 | GET | `/api/v1/reports/lead-analytics` | Lead funnel & conversion analytics |
| 10 | GET | `/api/v1/reports/marketing-roi` | Marketing ROI by channel |

---

## New Database Tables

### `leads`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK | Organization |
| `source` | VARCHAR | `instagram_targeted`, `instagram_direct`, `website`, `olx`, `2gis`, `referral`, `returning_client`, `other` |
| `client_name` | VARCHAR | Client name from first contact |
| `phone` | VARCHAR | Phone number |
| `status` | VARCHAR | `new`, `contacted`, `no_answer`, `potential`, `junk`, `rejected`, `converted` |
| `rejection_reason` | VARCHAR | `blacklisted`, `no_documents`, `price`, `no_availability`, `no_answer`, `other` |
| `notes` | TEXT | Manager notes |
| `assigned_to` | UUID FK → users | Manager assigned |
| `campaign_id` | UUID FK → marketing_campaigns | Which campaign generated this lead |
| `client_id` | UUID FK → clients | Linked client (after conversion) |
| `rental_id` | UUID FK → rentals | Linked rental (after conversion) |
| `vehicle_category_requested` | VARCHAR | What category client wanted |
| `desired_start_date` | DATE | When client wants to rent |
| `desired_duration_days` | INT | How long |
| `contacted_at` | TIMESTAMPTZ | When first contacted |
| `converted_at` | TIMESTAMPTZ | When converted to rental |
| `created_at` | TIMESTAMPTZ | When lead was created |
| `updated_at` | TIMESTAMPTZ | |

### `marketing_campaigns`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK | Organization |
| `name` | VARCHAR | Campaign name (e.g., "Facebook April 2025") |
| `source` | VARCHAR | Channel: `instagram`, `facebook`, `google`, `yandex`, `olx`, `2gis`, `website` |
| `period_from` | DATE | Campaign start |
| `period_to` | DATE | Campaign end |
| `budget` | DECIMAL | Total spend |
| `actual_spend` | DECIMAL | Actual spend (may differ from budget) |
| `is_active` | BOOLEAN | Currently running |
| `notes` | TEXT | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

## New Entities

### Lead Entity

```python
LeadId = NewType("LeadId", UUID)
MarketingCampaignId = NewType("MarketingCampaignId", UUID)

class LeadSource(StrEnum):
    INSTAGRAM_TARGETED = "instagram_targeted"
    INSTAGRAM_DIRECT = "instagram_direct"
    WEBSITE = "website"
    OLX = "olx"
    TWO_GIS = "2gis"
    REFERRAL = "referral"
    RETURNING_CLIENT = "returning_client"
    OTHER = "other"

class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    NO_ANSWER = "no_answer"
    POTENTIAL = "potential"       # "На будущее, есть потенциал"
    JUNK = "junk"                # "Воздух"
    REJECTED = "rejected"         # "Отказ по базе"
    CONVERTED = "converted"       # "Лид" → became rental

class Lead(Entity[LeadId]):
    organization_id: OrganizationId
    source: LeadSource
    client_name: str
    phone: str
    status: LeadStatus
    rejection_reason: str | None
    notes: str | None
    assigned_to: UserId | None
    campaign_id: MarketingCampaignId | None
    client_id: ClientId | None
    rental_id: RentalId | None
    vehicle_category_requested: str | None
    desired_start_date: date | None
    desired_duration_days: int | None
    contacted_at: datetime | None
    converted_at: datetime | None
    created_at: UtcDatetime
    updated_at: UtcDatetime
```

### MarketingCampaign Entity

```python
class CampaignSource(StrEnum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YANDEX = "yandex"
    OLX = "olx"
    TWO_GIS = "2gis"
    WEBSITE = "website"
    OTHER = "other"

class MarketingCampaign(Entity[MarketingCampaignId]):
    organization_id: OrganizationId
    name: str
    source: CampaignSource
    period_from: date
    period_to: date
    budget: Decimal
    actual_spend: Decimal
    is_active: bool
    notes: str | None
    created_at: UtcDatetime
    updated_at: UtcDatetime
```

---

## 1. Create Lead

### Request

```
POST /api/v1/leads
```

```json
{
  "source": "instagram_targeted",
  "client_name": "Алмаз",
  "phone": "+77001234567",
  "assigned_to": "uuid",
  "campaign_id": "uuid",
  "vehicle_category_requested": "Комфорт",
  "desired_start_date": "2025-04-15",
  "desired_duration_days": 30,
  "notes": "Wants Toyota Camry"
}
```

### Response `201 Created`

```json
{
  "id": "uuid",
  "source": "instagram_targeted",
  "client_name": "Алмаз",
  "phone": "+77001234567",
  "status": "new",
  "assigned_to": "uuid",
  "campaign_id": "uuid",
  "vehicle_category_requested": "Комфорт",
  "desired_start_date": "2025-04-15",
  "desired_duration_days": 30,
  "notes": "Wants Toyota Camry",
  "created_at": "2025-04-10T12:00:00Z"
}
```

---

## 2. List Leads

### Request

```
GET /api/v1/leads?status=new&source=instagram_targeted&date_from=2025-04-01&date_to=2025-04-30
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `status` | string | No | all | Filter by lead status |
| `source` | string | No | all | Filter by lead source |
| `assigned_to` | UUID | No | all | Filter by assigned manager |
| `campaign_id` | UUID | No | all | Filter by campaign |
| `date_from` | date | No | — | Created after |
| `date_to` | date | No | — | Created before |
| `limit` | int | No | 50 | Page size (1-100) |
| `offset` | int | No | 0 | Pagination offset |

### Response `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "source": "instagram_targeted",
      "client_name": "Алмаз",
      "phone": "+77001234567",
      "status": "new",
      "assigned_to": "uuid",
      "assigned_to_name": "Исламбек",
      "campaign_id": "uuid",
      "campaign_name": "Instagram April",
      "vehicle_category_requested": "Комфорт",
      "desired_start_date": "2025-04-15",
      "notes": "Wants Toyota Camry",
      "created_at": "2025-04-10T12:00:00Z"
    }
  ],
  "total": 245
}
```

---

## 3. Get Lead Detail

### Request

```
GET /api/v1/leads/{lead_id}
```

### Response `200 OK`

Same as list item, plus:

```json
{
  "...": "...",
  "client_id": "uuid",
  "rental_id": "uuid",
  "contacted_at": "2025-04-10T14:00:00Z",
  "converted_at": null,
  "rejection_reason": null,
  "updated_at": "2025-04-10T14:00:00Z"
}
```

---

## 4. Update Lead

### Request

```
PATCH /api/v1/leads/{lead_id}
```

```json
{
  "status": "contacted",
  "notes": "Called, interested, will come tomorrow",
  "contacted_at": "2025-04-10T14:00:00Z"
}
```

### Status Transitions

```
new → contacted → potential → converted
                → no_answer
                → junk
                → rejected
potential → contacted (re-contacted)
          → converted
          → rejected
no_answer → contacted (re-contacted)
          → junk
```

### Response `204 No Content`

---

## 5. Convert Lead to Rental

### Request

```
POST /api/v1/leads/{lead_id}/convert
```

```json
{
  "client_id": "uuid",
  "rental_id": "uuid"
}
```

Links the lead to an existing client and rental. Sets `status = 'converted'` and `converted_at = now()`.

### Response `204 No Content`

---

## 6. Create Marketing Campaign

### Request

```
POST /api/v1/marketing-campaigns
```

```json
{
  "name": "Instagram Targeted April",
  "source": "instagram",
  "period_from": "2025-04-01",
  "period_to": "2025-04-30",
  "budget": 450000,
  "actual_spend": 450000,
  "notes": "Facebook Ads targeting Almaty"
}
```

### Response `201 Created`

```json
{
  "id": "uuid",
  "name": "Instagram Targeted April",
  "source": "instagram",
  "period_from": "2025-04-01",
  "period_to": "2025-04-30",
  "budget": 450000,
  "actual_spend": 450000,
  "is_active": true,
  "notes": "Facebook Ads targeting Almaty",
  "created_at": "2025-04-01T00:00:00Z"
}
```

---

## 7. List Campaigns

### Request

```
GET /api/v1/marketing-campaigns?is_active=true&source=instagram
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `is_active` | bool | No | all | Filter active/inactive |
| `source` | string | No | all | Filter by channel |
| `period` | string | No | — | Month `YYYY-MM`, returns campaigns overlapping this period |

### Response `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Instagram Targeted April",
      "source": "instagram",
      "period_from": "2025-04-01",
      "period_to": "2025-04-30",
      "budget": 450000,
      "actual_spend": 450000,
      "is_active": true,
      "leads_count": 380,
      "converted_count": 22,
      "conversion_rate": 0.0579,
      "cost_per_lead": 1184,
      "cost_per_conversion": 20455,
      "created_at": "2025-04-01T00:00:00Z"
    }
  ],
  "total": 4
}
```

---

## 8. Update Campaign

### Request

```
PATCH /api/v1/marketing-campaigns/{campaign_id}
```

```json
{
  "actual_spend": 480000,
  "is_active": false
}
```

### Response `204 No Content`

---

## 9. Lead Analytics Report

Replicates the Excel "Аналитка по рекламе" — daily lead funnel by source.

### Request

```
GET /api/v1/reports/lead-analytics?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month `YYYY-MM` |
| `source` | string | No | all | Filter by lead source |
| `assigned_to` | UUID | No | all | Filter by manager |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "summary": {
    "total_leads": 545,
    "by_status": {
      "new": 10,
      "contacted": 25,
      "no_answer": 174,
      "potential": 143,
      "junk": 51,
      "rejected": 18,
      "converted": 124
    },
    "conversion_rate": 0.2275,
    "avg_time_to_convert_hours": 48,
    "by_source": [
      {
        "source": "instagram_targeted",
        "total": 380,
        "no_answer": 164,
        "potential": 110,
        "junk": 46,
        "rejected": 18,
        "converted": 24,
        "conversion_rate": 0.0632
      },
      {
        "source": "instagram_direct",
        "total": 38,
        "no_answer": 5,
        "potential": 15,
        "junk": 2,
        "rejected": 5,
        "converted": 1,
        "conversion_rate": 0.0263
      },
      {
        "source": "website",
        "total": 75,
        "no_answer": 6,
        "potential": 28,
        "junk": 18,
        "rejected": 8,
        "converted": 19,
        "conversion_rate": 0.2533
      },
      {
        "source": "returning_client",
        "total": 61,
        "converted": 61,
        "conversion_rate": 1.0
      }
    ]
  },
  "daily": [
    {
      "date": "2025-04-01",
      "total_leads": 27,
      "by_source": {
        "instagram_targeted": 22,
        "instagram_direct": 1,
        "website": 4,
        "2gis": 0,
        "olx": 0
      },
      "converted": 4,
      "from_returning_clients": 2
    }
  ],
  "funnel": {
    "total_leads": 545,
    "contacted": 371,
    "qualified": 267,
    "converted": 124,
    "contact_rate": 0.6807,
    "qualification_rate": 0.4899,
    "conversion_rate": 0.2275
  }
}
```

### Data Source

- `leads` table grouped by `date(created_at)`, `source`, `status`
- Conversion = leads where `status = 'converted'`
- Returning clients: leads where `source = 'returning_client'`

---

## 10. Marketing ROI Report

Replicates "Маркетинг апрель" — spend vs results per channel.

### Request

```
GET /api/v1/reports/marketing-roi?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month `YYYY-MM` |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "channels": [
    {
      "source": "instagram",
      "campaigns": ["Instagram Targeted April"],
      "total_spend": 450000,
      "total_leads": 418,
      "converted_leads": 25,
      "conversion_rate": 0.0598,
      "cost_per_lead": 1077,
      "cost_per_conversion": 18000,
      "revenue_from_converted": 3750000,
      "roi": 7.33,
      "rentals_from_leads": 25
    },
    {
      "source": "google",
      "campaigns": ["Google Ads April"],
      "total_spend": 260330,
      "total_leads": 42,
      "converted_leads": 12,
      "conversion_rate": 0.2857,
      "cost_per_lead": 6198,
      "cost_per_conversion": 21694,
      "revenue_from_converted": 2100000,
      "roi": 7.07,
      "rentals_from_leads": 12
    },
    {
      "source": "yandex",
      "campaigns": ["Yandex Direct April"],
      "total_spend": 117600,
      "total_leads": 18,
      "converted_leads": 5,
      "conversion_rate": 0.2778,
      "cost_per_lead": 6533,
      "cost_per_conversion": 23520,
      "revenue_from_converted": 750000,
      "roi": 5.38,
      "rentals_from_leads": 5
    },
    {
      "source": "olx",
      "campaigns": ["OLX April"],
      "total_spend": 230000,
      "total_leads": 8,
      "converted_leads": 3,
      "conversion_rate": 0.375,
      "cost_per_lead": 28750,
      "cost_per_conversion": 76667,
      "revenue_from_converted": 480000,
      "roi": 1.09,
      "rentals_from_leads": 3
    }
  ],
  "totals": {
    "total_spend": 1057930,
    "total_leads": 486,
    "total_converted": 45,
    "avg_conversion_rate": 0.0926,
    "avg_cost_per_lead": 2177,
    "avg_cost_per_conversion": 23510,
    "total_revenue_from_leads": 7080000,
    "overall_roi": 5.69
  },
  "returning_clients": {
    "count": 61,
    "revenue": 9150000,
    "percentage_of_total_rentals": 0.575,
    "cost": 0
  }
}
```

### Data Source

- `marketing_campaigns` for spend per channel
- `leads` grouped by `source` and `campaign_id` for counts and statuses
- Revenue from converted leads: `leads.rental_id` → `cash_journal_entries` (income) for that rental
- ROI = revenue_from_converted / total_spend

---

## TypeScript Types

```typescript
// Lead types
interface Lead {
  id: string;
  source: LeadSource;
  client_name: string;
  phone: string;
  status: LeadStatus;
  rejection_reason: string | null;
  notes: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
  campaign_id: string | null;
  campaign_name: string | null;
  client_id: string | null;
  rental_id: string | null;
  vehicle_category_requested: string | null;
  desired_start_date: string | null;
  desired_duration_days: number | null;
  contacted_at: string | null;
  converted_at: string | null;
  created_at: string;
  updated_at: string;
}

type LeadSource =
  | 'instagram_targeted'
  | 'instagram_direct'
  | 'website'
  | 'olx'
  | '2gis'
  | 'referral'
  | 'returning_client'
  | 'other';

type LeadStatus =
  | 'new'
  | 'contacted'
  | 'no_answer'
  | 'potential'
  | 'junk'
  | 'rejected'
  | 'converted';

interface LeadCreateBody {
  source: LeadSource;
  client_name: string;
  phone: string;
  assigned_to?: string;
  campaign_id?: string;
  vehicle_category_requested?: string;
  desired_start_date?: string;
  desired_duration_days?: number;
  notes?: string;
}

interface LeadUpdateBody {
  status?: LeadStatus;
  notes?: string;
  rejection_reason?: string;
  assigned_to?: string;
  contacted_at?: string;
}

// Campaign types
interface MarketingCampaign {
  id: string;
  name: string;
  source: CampaignSource;
  period_from: string;
  period_to: string;
  budget: number;
  actual_spend: number;
  is_active: boolean;
  notes: string | null;
  leads_count: number;
  converted_count: number;
  conversion_rate: number;
  cost_per_lead: number;
  cost_per_conversion: number;
  created_at: string;
}

type CampaignSource =
  | 'instagram'
  | 'facebook'
  | 'google'
  | 'yandex'
  | 'olx'
  | '2gis'
  | 'website'
  | 'other';

interface CampaignCreateBody {
  name: string;
  source: CampaignSource;
  period_from: string;
  period_to: string;
  budget: number;
  actual_spend?: number;
  notes?: string;
}

// Analytics types
interface LeadSourceBreakdown {
  source: string;
  total: number;
  no_answer: number;
  potential: number;
  junk: number;
  rejected: number;
  converted: number;
  conversion_rate: number;
}

interface DailyLeadData {
  date: string;
  total_leads: number;
  by_source: Record<string, number>;
  converted: number;
  from_returning_clients: number;
}

interface LeadFunnel {
  total_leads: number;
  contacted: number;
  qualified: number;
  converted: number;
  contact_rate: number;
  qualification_rate: number;
  conversion_rate: number;
}

interface LeadAnalyticsResponse {
  period: string;
  summary: {
    total_leads: number;
    by_status: Record<LeadStatus, number>;
    conversion_rate: number;
    avg_time_to_convert_hours: number;
    by_source: LeadSourceBreakdown[];
  };
  daily: DailyLeadData[];
  funnel: LeadFunnel;
}

// Marketing ROI types
interface ChannelROI {
  source: string;
  campaigns: string[];
  total_spend: number;
  total_leads: number;
  converted_leads: number;
  conversion_rate: number;
  cost_per_lead: number;
  cost_per_conversion: number;
  revenue_from_converted: number;
  roi: number;
  rentals_from_leads: number;
}

interface MarketingROIResponse {
  period: string;
  channels: ChannelROI[];
  totals: {
    total_spend: number;
    total_leads: number;
    total_converted: number;
    avg_conversion_rate: number;
    avg_cost_per_lead: number;
    avg_cost_per_conversion: number;
    total_revenue_from_leads: number;
    overall_roi: number;
  };
  returning_clients: {
    count: number;
    revenue: number;
    percentage_of_total_rentals: number;
    cost: number;
  };
}
```

---

## Vue Composables

### `useLeads`

```typescript
export function useLeads() {
  const leads = ref<Lead[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch(filters?: {
    status?: string;
    source?: string;
    assigned_to?: string;
    campaign_id?: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
    offset?: number;
  }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (filters) {
        Object.entries(filters).forEach(([k, v]) => {
          if (v !== undefined) params.set(k, String(v))
        })
      }
      const res = await api.get(`/leads?${params}`)
      leads.value = res.data.items
      total.value = res.data.total
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load leads'
    } finally {
      loading.value = false
    }
  }

  async function create(body: LeadCreateBody) {
    const res = await api.post('/leads', body)
    return res.data
  }

  async function update(leadId: string, body: LeadUpdateBody) {
    await api.patch(`/leads/${leadId}`, body)
  }

  async function convert(leadId: string, clientId: string, rentalId: string) {
    await api.post(`/leads/${leadId}/convert`, {
      client_id: clientId,
      rental_id: rentalId,
    })
  }

  return { leads, total, loading, error, fetch, create, update, convert }
}
```

### `useMarketingCampaigns`

```typescript
export function useMarketingCampaigns() {
  const campaigns = ref<MarketingCampaign[]>([])
  const loading = ref(false)

  async function fetch(filters?: { is_active?: boolean; source?: string; period?: string }) {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (filters) {
        Object.entries(filters).forEach(([k, v]) => {
          if (v !== undefined) params.set(k, String(v))
        })
      }
      const res = await api.get(`/marketing-campaigns?${params}`)
      campaigns.value = res.data.items
    } finally {
      loading.value = false
    }
  }

  async function create(body: CampaignCreateBody) {
    const res = await api.post('/marketing-campaigns', body)
    campaigns.value.push(res.data)
    return res.data
  }

  async function update(campaignId: string, body: Partial<CampaignCreateBody>) {
    await api.patch(`/marketing-campaigns/${campaignId}`, body)
    await fetch()
  }

  return { campaigns, loading, fetch, create, update }
}
```

### `useLeadAnalytics`

```typescript
export function useLeadAnalytics() {
  const data = ref<LeadAnalyticsResponse | null>(null)
  const loading = ref(false)

  async function fetch(period: string, filters?: { source?: string; assigned_to?: string }) {
    loading.value = true
    try {
      const params = new URLSearchParams({ period })
      if (filters?.source) params.set('source', filters.source)
      if (filters?.assigned_to) params.set('assigned_to', filters.assigned_to)
      const res = await api.get(`/reports/lead-analytics?${params}`)
      data.value = res.data
    } finally {
      loading.value = false
    }
  }

  return { data, loading, fetch }
}
```

### `useMarketingROI`

```typescript
export function useMarketingROI() {
  const data = ref<MarketingROIResponse | null>(null)
  const loading = ref(false)

  async function fetch(period: string) {
    loading.value = true
    try {
      const res = await api.get(`/reports/marketing-roi?period=${period}`)
      data.value = res.data
    } finally {
      loading.value = false
    }
  }

  return { data, loading, fetch }
}
```

---

## UI Screens

### Screen 1: Lead List / CRM Board

```
+------------------------------------------------------------------+
| Leads                    [April 2025 v] [All Sources v] [+ Lead]  |
+------------------------------------------------------------------+
| View: [List] [Kanban]                                             |
+------------------------------------------------------------------+

Kanban View:
+------------+------------+------------+------------+------------+
| New (10)   | Contacted  | Potential  | Converted  | Junk/Rej   |
|            | (25)       | (143)      | (124)      | (69)       |
+------------+------------+------------+------------+------------+
| Алмаз      | Бекжан     | Нурлан     | Серик      | Дос        |
| inst_targ  | website    | inst_targ  | inst_targ  | no docs    |
| Комфорт    | +7700...   | Бизнес     | Camry 70   | blacklisted|
| 15 Apr     | 14 Apr     | 10 Apr     | 8 Apr      | 5 Apr      |
| [Исламбек] |            | [Айдар]    | [Исламбек] |            |
+------------+------------+------------+------------+------------+

List View:
| Date       | Name   | Phone      | Source    | Category | Status    | Manager  |
|------------|--------|------------|-----------|----------|-----------|----------|
| 10.04.2025 | Алмаз  | +7700...   | Таргет IG | Комфорт  | Новый     | Исламбек |
| 10.04.2025 | Бекжан | +7701...   | Сайт      | Эконом   | Контакт   | —        |
```

### Screen 2: Lead Analytics Dashboard

```
+------------------------------------------------------------------+
| Lead Analytics                            [April 2025 v]          |
+------------------------------------------------------------------+
| Funnel:                                                           |
| Total Leads    ████████████████████████████████████████ 545       |
| Contacted      ██████████████████████████████          371 (68%)  |
| Qualified      ████████████████████                    267 (49%)  |
| Converted      █████████                               124 (23%) |
+------------------------------------------------------------------+
| Daily Leads (bar chart):                                          |
| [Stacked bars by source, x-axis = days 1-30]                     |
+------------------------------------------------------------------+
| By Source:                                                        |
| Source           | Leads | No Ans | Potential | Junk | Conv | CR  |
|------------------|-------|--------|-----------|------|------|-----|
| IG Targeted      | 380   | 164    | 110       | 46   | 24   | 6.3%|
| IG Direct        | 38    | 5      | 15        | 2    | 1    | 2.6%|
| Website          | 75    | 6      | 28        | 18   | 19   | 25% |
| 2GIS             | 6     | 0      | 3         | 1    | 1    | 17% |
| Returning Client | 61    | 0      | 0         | 0    | 61   | 100%|
+------------------------------------------------------------------+
```

### Screen 3: Marketing ROI Dashboard

```
+------------------------------------------------------------------+
| Marketing ROI                             [April 2025 v]          |
+------------------------------------------------------------------+
| Total Spend: 1,057,930 | Total Leads: 486 | Converted: 45        |
| Revenue from Leads: 7,080,000 | Overall ROI: 5.69x               |
+------------------------------------------------------------------+
| [Bar Chart: spend vs revenue per channel]                         |
+------------------------------------------------------------------+
| Channel   | Spend   | Leads | Conv | CR    | CPL   | CPC    | ROI |
|-----------|---------|-------|------|-------|-------|--------|-----|
| Instagram | 450,000 | 418   | 25   | 6.0%  | 1,077 | 18,000 | 7.3x|
| Google    | 260,330 | 42    | 12   | 28.6% | 6,198 | 21,694 | 7.1x|
| Yandex    | 117,600 | 18    | 5    | 27.8% | 6,533 | 23,520 | 5.4x|
| OLX       | 230,000 | 8     | 3    | 37.5% | 28,750| 76,667 | 1.1x|
+------------------------------------------------------------------+
| Returning Clients: 61 rentals (57.5% of total) — zero cost       |
+------------------------------------------------------------------+
| Recommendations:                                                  |
| - Best ROI: Instagram (7.3x) — consider increasing budget        |
| - Worst ROI: OLX (1.1x) — high cost per conversion               |
| - Website has best conversion rate (25%) with moderate cost       |
+------------------------------------------------------------------+
```

### Screen 4: Campaign Management

```
+------------------------------------------------------------------+
| Marketing Campaigns                               [+ New Campaign]|
+------------------------------------------------------------------+
| Campaign              | Channel | Period     | Budget | Spend | Active|
|-----------------------|---------|------------|--------|-------|-------|
| Instagram Targeted Apr| IG      | 01-30 Apr  | 450k   | 450k  | Yes   |
| Google Ads April      | Google  | 01-30 Apr  | 260k   | 260k  | Yes   |
| Yandex Direct April   | Yandex  | 01-30 Apr  | 118k   | 118k  | Yes   |
| OLX Premium April     | OLX     | 01-30 Apr  | 230k   | 230k  | Yes   |
+------------------------------------------------------------------+
| Click campaign to see linked leads and performance metrics        |
+------------------------------------------------------------------+
```

---

## Permissions

| Endpoint | Required Permission |
|----------|-------------------|
| Create/update leads | `lead.manage` |
| List/view leads | `lead.view` |
| Convert lead | `lead.manage` |
| Create/update campaigns | `marketing.manage` or `admin` |
| List campaigns | `marketing.view` |
| Lead analytics report | `report.view` |
| Marketing ROI report | `report.view` or `admin` |

---

## Error Responses

| Status | When |
|--------|------|
| `400` | Invalid status transition, missing required fields |
| `401` | Not authenticated |
| `403` | Insufficient permissions |
| `404` | Lead or campaign not found |
| `409` | Lead already converted, duplicate phone in same period |
| `503` | Database unavailable |
