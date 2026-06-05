# Module 11: Manager Bonus System — Frontend Integration Spec

> Automated bonus calculation for managers based on revenue contribution
> and vehicle count. Replicates the Excel "Бонусы" sheet logic.
> Requires new database tables for bonus rules and calculated payouts.

---

## Endpoints Overview

| # | Method | Path | Description |
|---|--------|------|-------------|
| 1 | GET | `/api/v1/bonus-rules` | List bonus rules configuration |
| 2 | POST | `/api/v1/bonus-rules` | Create/update bonus rules |
| 3 | PATCH | `/api/v1/bonus-rules/{rule_id}` | Update a bonus rule |
| 4 | GET | `/api/v1/manager-bonuses` | Get calculated bonuses for a period |
| 5 | GET | `/api/v1/manager-bonuses/{manager_id}` | Detailed bonus breakdown for a manager |
| 6 | POST | `/api/v1/manager-bonuses/calculate` | Trigger bonus calculation for a period |
| 7 | POST | `/api/v1/manager-bonuses/{bonus_id}/approve` | Approve calculated bonus for payout |

---

## Bonus Calculation Logic (from Excel)

The Excel uses this formula per manager per day:

```
daily_fleet_revenue = SUM(all vehicle revenues for day)
manager_daily_revenue = SUM(revenues of vehicles managed by this manager for day)

revenue_coefficient = manager_daily_revenue / daily_fleet_revenue
vehicle_coefficient = manager_vehicle_count / total_vehicles_in_fleet

daily_bonus_base = bonus_pool / days_in_month  (e.g., 1,200,000 / 30 = 40,000)

revenue_bonus = revenue_coefficient * daily_bonus_base * revenue_weight  (weight = 0.7)
vehicle_bonus = vehicle_coefficient * daily_bonus_base * vehicle_weight  (weight = 0.3)

daily_total_bonus = revenue_bonus + vehicle_bonus
monthly_bonus = SUM(daily_total_bonus for all days) + fixed_salary
```

---

## New Database Tables

### `bonus_rules`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK | Organization |
| `name` | VARCHAR | Rule name (e.g., "Standard Manager Bonus") |
| `bonus_pool` | DECIMAL | Total monthly bonus pool (e.g., 1,200,000) |
| `fixed_salary` | DECIMAL | Fixed base salary per manager (e.g., 100,000) |
| `revenue_weight` | DECIMAL | Weight for revenue-based bonus (e.g., 0.7) |
| `vehicle_count_weight` | DECIMAL | Weight for vehicle-count bonus (e.g., 0.3) |
| `exclude_statuses` | JSONB | Vehicle statuses to exclude from pool (e.g., ["decommissioned", "sold"]) |
| `is_active` | BOOLEAN | Whether this rule is active |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### `manager_bonuses`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID PK | |
| `organization_id` | UUID FK | Organization |
| `manager_id` | UUID FK → users | Manager user |
| `bonus_rule_id` | UUID FK → bonus_rules | Rule used for calculation |
| `period` | DATE | First day of the month (e.g., 2025-04-01) |
| `fixed_salary` | DECIMAL | Fixed component |
| `revenue_bonus` | DECIMAL | Calculated revenue-based bonus |
| `vehicle_bonus` | DECIMAL | Calculated vehicle-count bonus |
| `total_bonus` | DECIMAL | fixed + revenue + vehicle |
| `vehicles_managed` | INT | Number of vehicles managed |
| `total_revenue` | DECIMAL | Total revenue from managed vehicles |
| `revenue_coefficient_avg` | DECIMAL | Average daily revenue coefficient |
| `status` | VARCHAR | `calculated`, `approved`, `paid` |
| `approved_by` | UUID FK → users | Who approved |
| `approved_at` | TIMESTAMPTZ | |
| `daily_breakdown` | JSONB | Per-day calculation details |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### `daily_breakdown` JSONB structure

```json
{
  "1": {
    "fleet_revenue": 1116002,
    "manager_revenue": 456000,
    "revenue_coefficient": 0.4086,
    "active_vehicles": 20,
    "total_fleet_vehicles": 44,
    "vehicle_coefficient": 0.4545,
    "daily_bonus_base": 40000,
    "revenue_bonus": 11441,
    "vehicle_bonus": 5454,
    "total": 16895
  },
  "2": { ... }
}
```

---

## 1. List Bonus Rules

### Request

```
GET /api/v1/bonus-rules
```

### Response `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Standard Manager Bonus",
      "bonus_pool": 1200000,
      "fixed_salary": 100000,
      "revenue_weight": 0.7,
      "vehicle_count_weight": 0.3,
      "exclude_statuses": ["decommissioned", "sold"],
      "is_active": true,
      "created_at": "2025-04-01T00:00:00Z",
      "updated_at": "2025-04-01T00:00:00Z"
    }
  ]
}
```

---

## 2. Create Bonus Rule

### Request

```
POST /api/v1/bonus-rules
```

```json
{
  "name": "Standard Manager Bonus",
  "bonus_pool": 1200000,
  "fixed_salary": 100000,
  "revenue_weight": 0.7,
  "vehicle_count_weight": 0.3,
  "exclude_statuses": ["decommissioned", "sold"]
}
```

### Validation

- `revenue_weight + vehicle_count_weight` must equal `1.0`
- `bonus_pool` must be `> 0`
- `fixed_salary` must be `>= 0`

### Response `201 Created`

```json
{
  "id": "uuid",
  "name": "Standard Manager Bonus",
  "bonus_pool": 1200000,
  "fixed_salary": 100000,
  "revenue_weight": 0.7,
  "vehicle_count_weight": 0.3,
  "exclude_statuses": ["decommissioned", "sold"],
  "is_active": true,
  "created_at": "2025-04-01T00:00:00Z",
  "updated_at": "2025-04-01T00:00:00Z"
}
```

---

## 3. Update Bonus Rule

### Request

```
PATCH /api/v1/bonus-rules/{rule_id}
```

```json
{
  "bonus_pool": 1500000,
  "revenue_weight": 0.6,
  "vehicle_count_weight": 0.4
}
```

### Response `204 No Content`

---

## 4. Get Manager Bonuses

### Request

```
GET /api/v1/manager-bonuses?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month `YYYY-MM` |
| `status` | string | No | all | Filter: `calculated`, `approved`, `paid` |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "bonus_rule": {
    "id": "uuid",
    "name": "Standard Manager Bonus",
    "bonus_pool": 1200000,
    "revenue_weight": 0.7,
    "vehicle_count_weight": 0.3
  },
  "fleet_summary": {
    "total_revenue": 37466068,
    "total_vehicles": 59,
    "days_in_month": 30,
    "daily_bonus_base": 40000
  },
  "managers": [
    {
      "bonus_id": "uuid",
      "manager_id": "uuid",
      "manager_name": "Тима",
      "vehicles_managed": 13,
      "total_revenue": 15200000,
      "revenue_coefficient_avg": 0.41,
      "fixed_salary": 100000,
      "revenue_bonus": 266122,
      "vehicle_bonus": 100000,
      "total_bonus": 466122,
      "status": "calculated"
    },
    {
      "bonus_id": "uuid",
      "manager_id": "uuid",
      "manager_name": "Канат",
      "vehicles_managed": 10,
      "total_revenue": 8700000,
      "revenue_coefficient_avg": 0.23,
      "fixed_salary": 100000,
      "revenue_bonus": 207714,
      "vehicle_bonus": 75000,
      "total_bonus": 382714,
      "status": "calculated"
    },
    {
      "bonus_id": "uuid",
      "manager_id": "uuid",
      "manager_name": "Арнат",
      "vehicles_managed": 6,
      "total_revenue": 5200000,
      "revenue_coefficient_avg": 0.14,
      "fixed_salary": 100000,
      "revenue_bonus": 114576,
      "vehicle_bonus": 50000,
      "total_bonus": 264576,
      "status": "calculated"
    }
  ],
  "totals": {
    "total_fixed": 300000,
    "total_revenue_bonus": 588412,
    "total_vehicle_bonus": 225000,
    "grand_total": 1113412,
    "remaining_pool": 86588
  },
  "validation": {
    "bonus_pool_check": true,
    "total_distributed": 1113412,
    "pool_amount": 1200000,
    "within_budget": true
  }
}
```

---

## 5. Manager Bonus Detail

### Request

```
GET /api/v1/manager-bonuses/{manager_id}?period=2025-04
```

### Response `200 OK`

```json
{
  "bonus_id": "uuid",
  "manager_id": "uuid",
  "manager_name": "Тима",
  "period": "2025-04",
  "status": "calculated",
  "summary": {
    "vehicles_managed": 13,
    "total_revenue": 15200000,
    "revenue_coefficient_avg": 0.41,
    "fixed_salary": 100000,
    "revenue_bonus": 266122,
    "vehicle_bonus": 100000,
    "total_bonus": 466122
  },
  "daily_breakdown": [
    {
      "day": 1,
      "date": "2025-04-01",
      "fleet_revenue": 1116002,
      "manager_revenue": 456000,
      "revenue_coefficient": 0.4086,
      "active_vehicles": 20,
      "total_fleet_vehicles": 44,
      "vehicle_coefficient": 0.4545,
      "daily_bonus_base": 40000,
      "revenue_bonus": 11441,
      "vehicle_bonus": 5454,
      "total": 16895
    }
  ],
  "vehicles": [
    {
      "vehicle_id": "uuid",
      "nickname": "Акцент 066",
      "category": "Эконом",
      "total_revenue": 405000,
      "active_days": 27
    }
  ]
}
```

---

## 6. Trigger Bonus Calculation

### Request

```
POST /api/v1/manager-bonuses/calculate
```

```json
{
  "period": "2025-04",
  "bonus_rule_id": "uuid"
}
```

### Behavior

1. Fetch the bonus rule configuration
2. For each day in the period:
   - Query `cash_journal_entries` (income) grouped by vehicle → get daily fleet revenue
   - Map vehicles to managers via active rentals for that day
   - Calculate coefficients and bonus amounts per formula
3. Aggregate daily values into monthly totals per manager
4. Store results in `manager_bonuses` with `status = 'calculated'`
5. If bonuses already exist for this period, **recalculate** (overwrite if status = 'calculated', reject if 'approved'/'paid')

### Response `201 Created`

```json
{
  "period": "2025-04",
  "managers_calculated": 3,
  "grand_total": 1113412,
  "status": "calculated"
}
```

---

## 7. Approve Bonus

### Request

```
POST /api/v1/manager-bonuses/{bonus_id}/approve
```

### Response `204 No Content`

Changes status from `calculated` → `approved`. Only `admin` or `financial_manager` can approve.

---

## New Entities

### BonusRule Entity

```python
class BonusRule(Entity[BonusRuleId]):
    organization_id: OrganizationId
    name: str
    bonus_pool: Decimal
    fixed_salary: Decimal
    revenue_weight: Decimal          # 0.7
    vehicle_count_weight: Decimal    # 0.3
    exclude_statuses: list[str]
    is_active: bool
    created_at: UtcDatetime
    updated_at: UtcDatetime
```

### ManagerBonus Entity

```python
class ManagerBonus(Entity[ManagerBonusId]):
    organization_id: OrganizationId
    manager_id: UserId
    bonus_rule_id: BonusRuleId
    period: date
    fixed_salary: Decimal
    revenue_bonus: Decimal
    vehicle_bonus: Decimal
    total_bonus: Decimal
    vehicles_managed: int
    total_revenue: Decimal
    revenue_coefficient_avg: Decimal
    status: BonusStatus              # calculated, approved, paid
    approved_by: UserId | None
    approved_at: datetime | None
    daily_breakdown: dict[str, Any]  # JSONB
    created_at: UtcDatetime
    updated_at: UtcDatetime
```

### New Types

```python
BonusRuleId = NewType("BonusRuleId", UUID)
ManagerBonusId = NewType("ManagerBonusId", UUID)

class BonusStatus(StrEnum):
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"
```

---

## TypeScript Types

```typescript
interface BonusRule {
  id: string;
  name: string;
  bonus_pool: number;
  fixed_salary: number;
  revenue_weight: number;
  vehicle_count_weight: number;
  exclude_statuses: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface BonusRuleCreateBody {
  name: string;
  bonus_pool: number;
  fixed_salary: number;
  revenue_weight: number;
  vehicle_count_weight: number;
  exclude_statuses?: string[];
}

interface ManagerBonusSummary {
  bonus_id: string;
  manager_id: string;
  manager_name: string;
  vehicles_managed: number;
  total_revenue: number;
  revenue_coefficient_avg: number;
  fixed_salary: number;
  revenue_bonus: number;
  vehicle_bonus: number;
  total_bonus: number;
  status: 'calculated' | 'approved' | 'paid';
}

interface DailyBonusBreakdown {
  day: number;
  date: string;
  fleet_revenue: number;
  manager_revenue: number;
  revenue_coefficient: number;
  active_vehicles: number;
  total_fleet_vehicles: number;
  vehicle_coefficient: number;
  daily_bonus_base: number;
  revenue_bonus: number;
  vehicle_bonus: number;
  total: number;
}

interface ManagerBonusDetail {
  bonus_id: string;
  manager_id: string;
  manager_name: string;
  period: string;
  status: string;
  summary: {
    vehicles_managed: number;
    total_revenue: number;
    revenue_coefficient_avg: number;
    fixed_salary: number;
    revenue_bonus: number;
    vehicle_bonus: number;
    total_bonus: number;
  };
  daily_breakdown: DailyBonusBreakdown[];
  vehicles: {
    vehicle_id: string;
    nickname: string | null;
    category: string;
    total_revenue: number;
    active_days: number;
  }[];
}

interface BonusCalculationTotals {
  total_fixed: number;
  total_revenue_bonus: number;
  total_vehicle_bonus: number;
  grand_total: number;
  remaining_pool: number;
}

interface ManagerBonusesResponse {
  period: string;
  bonus_rule: BonusRule;
  fleet_summary: {
    total_revenue: number;
    total_vehicles: number;
    days_in_month: number;
    daily_bonus_base: number;
  };
  managers: ManagerBonusSummary[];
  totals: BonusCalculationTotals;
  validation: {
    bonus_pool_check: boolean;
    total_distributed: number;
    pool_amount: number;
    within_budget: boolean;
  };
}
```

---

## Vue Composables

### `useBonusRules`

```typescript
export function useBonusRules() {
  const rules = ref<BonusRule[]>([])
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const res = await api.get('/bonus-rules')
      rules.value = res.data.items
    } finally {
      loading.value = false
    }
  }

  async function create(body: BonusRuleCreateBody) {
    const res = await api.post('/bonus-rules', body)
    rules.value.push(res.data)
    return res.data
  }

  async function update(ruleId: string, body: Partial<BonusRuleCreateBody>) {
    await api.patch(`/bonus-rules/${ruleId}`, body)
    await fetch()
  }

  return { rules, loading, fetch, create, update }
}
```

### `useManagerBonuses`

```typescript
export function useManagerBonuses() {
  const data = ref<ManagerBonusesResponse | null>(null)
  const detail = ref<ManagerBonusDetail | null>(null)
  const loading = ref(false)

  async function fetch(period: string) {
    loading.value = true
    try {
      const res = await api.get(`/manager-bonuses?period=${period}`)
      data.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(managerId: string, period: string) {
    loading.value = true
    try {
      const res = await api.get(`/manager-bonuses/${managerId}?period=${period}`)
      detail.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function calculate(period: string, bonusRuleId: string) {
    const res = await api.post('/manager-bonuses/calculate', {
      period,
      bonus_rule_id: bonusRuleId,
    })
    await fetch(period)
    return res.data
  }

  async function approve(bonusId: string) {
    await api.post(`/manager-bonuses/${bonusId}/approve`)
  }

  return { data, detail, loading, fetch, fetchDetail, calculate, approve }
}
```

---

## UI Screens

### Screen 1: Bonus Rules Configuration

```
+------------------------------------------------------------------+
| Bonus Rules                                          [+ New Rule] |
+------------------------------------------------------------------+
| Rule Name                | Pool     | Fixed  | Rev% | Veh% | Act |
|--------------------------|----------|--------|------|------|-----|
| Standard Manager Bonus   | 1,200,000| 100,000| 70%  | 30%  | Yes |
+------------------------------------------------------------------+
| [Edit] [Deactivate]                                               |
+------------------------------------------------------------------+

Edit Modal:
+-------------------------------------+
| Edit Bonus Rule                     |
|-------------------------------------|
| Name:    [Standard Manager Bonus  ] |
| Pool:    [1,200,000              ] |
| Fixed:   [100,000                ] |
| Rev %:   [70 ]  Veh %: [30 ]       |
|          (must sum to 100%)         |
| Exclude: [x] Decommissioned        |
|          [x] Sold                   |
|-------------------------------------|
|              [Cancel] [Save]        |
+-------------------------------------+
```

### Screen 2: Monthly Bonus Overview

```
+------------------------------------------------------------------+
| Manager Bonuses                  [April 2025 v] [Calculate]       |
+------------------------------------------------------------------+
| Rule: Standard Manager Bonus | Pool: 1,200,000 | Base: 40,000/day|
+------------------------------------------------------------------+
| Manager  | Cars | Revenue  | Coeff | Fixed | Rev$  | Veh$  | Total   | Status     |
|----------|------|----------|-------|-------|-------|-------|---------|------------|
| Тима     | 13   | 15.2M    | 0.41  | 100k  | 266k  | 100k  | 466,122 | Calculated |
| Канат    | 10   | 8.7M     | 0.23  | 100k  | 208k  | 75k   | 382,714 | Calculated |
| Арнат    | 6    | 5.2M     | 0.14  | 100k  | 115k  | 50k   | 264,576 | Calculated |
|----------|------|----------|-------|-------|-------|-------|---------|------------|
| TOTAL    | 29   | 29.1M    |       | 300k  | 588k  | 225k  | 1,113k  |            |
+------------------------------------------------------------------+
| Pool: 1,200,000 | Distributed: 1,113,412 | Remaining: 86,588     |
| [Approve All] [Export to PDF]                                     |
+------------------------------------------------------------------+
```

### Screen 3: Manager Bonus Detail

```
+------------------------------------------------------------------+
| Тима — April 2025 Bonus Detail                          [<- Back]|
+------------------------------------------------------------------+
| Summary:                                                          |
| Vehicles: 13 | Revenue: 15.2M | Avg Coefficient: 0.41            |
| Fixed: 100,000 | Revenue Bonus: 266,122 | Vehicle Bonus: 100,000 |
| TOTAL BONUS: 466,122                                              |
+------------------------------------------------------------------+
| Daily Breakdown:                                                  |
| Day | Fleet Rev | Mgr Rev | Coeff | Cars | Base  | Bonus         |
|-----|-----------|---------|-------|------|-------|---------------|
| 1   | 1,116,002 | 456,000 | 0.409 | 20   | 40,000| 16,895        |
| 2   | 1,093,003 | 448,000 | 0.410 | 19   | 40,000| 16,440        |
| ... |           |         |       |      |       |               |
+------------------------------------------------------------------+
| Vehicles Managed:                                                 |
| Акцент 066 (Эконом) — 405,000 — 27 active days                  |
| Акцент 399 (Эконом) — 450,000 — 30 active days                  |
| ...                                                               |
+------------------------------------------------------------------+
```

---

## Permissions

| Endpoint | Required Permission |
|----------|-------------------|
| List bonus rules | `bonus.view` |
| Create/update bonus rule | `bonus.manage` or `admin` |
| View bonuses | `bonus.view` |
| Calculate bonuses | `bonus.manage` or `admin` |
| Approve bonuses | `bonus.approve` or `admin` |

---

## Error Responses

| Status | When |
|--------|------|
| `400` | Invalid period, weights don't sum to 1.0 |
| `401` | Not authenticated |
| `403` | Insufficient permissions |
| `404` | Bonus rule or manager bonus not found |
| `409` | Cannot recalculate approved/paid bonuses |
| `503` | Database unavailable |
