# Module 10: Analytics & Reports — Frontend Integration Spec

> Backend endpoints for vehicle revenue grid, fleet utilization, vehicle expenses,
> manager performance, and enhanced P&L with investor splits.
> All data is computed from existing tables — no schema changes required.

---

## Endpoints Overview

| # | Method | Path | Description |
|---|--------|------|-------------|
| 1 | GET | `/api/v1/reports/vehicle-revenue-grid` | Daily revenue per vehicle (monthly grid) |
| 2 | GET | `/api/v1/reports/fleet-utilization` | Daily fleet utilization rate |
| 3 | GET | `/api/v1/reports/vehicle-expenses` | Expense breakdown by vehicle |
| 4 | GET | `/api/v1/reports/manager-performance` | Revenue & vehicle stats per manager |
| 5 | GET | `/api/v1/reports/pnl-by-investor` | P&L split by investor/partner |

---

## 1. Vehicle Revenue Grid

Replicates the Excel monthly sheets — a grid of vehicles (rows) × days (columns)
showing daily revenue per vehicle.

### Request

```
GET /api/v1/reports/vehicle-revenue-grid?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month in `YYYY-MM` format |
| `category` | string | No | all | Filter by vehicle category slug |
| `branch_id` | UUID | No | all | Filter by branch |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "days_in_month": 30,
  "vehicles": [
    {
      "vehicle_id": "uuid",
      "nickname": "Акцент 066",
      "license_plate": "066 ABC 01",
      "make": "Hyundai",
      "model": "Accent",
      "category": "Эконом",
      "manager_id": "uuid",
      "manager_name": "Исламбек",
      "daily_rate": 18000,
      "daily_revenue": {
        "1": 15000,
        "2": 15000,
        "3": 15000,
        "4": 0,
        "5": 15000
      },
      "total_revenue": 405000,
      "active_days": 27,
      "idle_days": 3
    }
  ],
  "totals": {
    "daily_totals": {
      "1": 1116002,
      "2": 1093003,
      "3": 1187003
    },
    "grand_total": 37466068,
    "active_vehicle_counts": {
      "1": 44,
      "2": 46,
      "3": 49
    }
  },
  "summary": {
    "total_vehicles": 59,
    "avg_daily_revenue": 1248869,
    "avg_utilization": 0.85,
    "top_vehicle": {
      "vehicle_id": "uuid",
      "nickname": "Акцент 095",
      "total_revenue": 450000
    },
    "bottom_vehicle": {
      "vehicle_id": "uuid",
      "nickname": "Акцент 494",
      "total_revenue": 330000
    }
  }
}
```

### Data Source

Revenue per vehicle per day is computed from:
- `cash_journal_entries` where `operation_type = 'income'` and `vehicle_id IS NOT NULL`,
  grouped by `vehicle_id` and `date`
- Joined with `vehicles` for nickname, category, make/model
- Joined with `rentals` (via `rental_id`) for `manager_id`
- Manager name from `users` table

### TypeScript Types

```typescript
interface DailyRevenueMap {
  [day: string]: number; // "1" through "31"
}

interface VehicleRevenueRow {
  vehicle_id: string;
  nickname: string | null;
  license_plate: string;
  make: string;
  model: string;
  category: string;
  manager_id: string | null;
  manager_name: string | null;
  daily_rate: number;
  daily_revenue: DailyRevenueMap;
  total_revenue: number;
  active_days: number;
  idle_days: number;
}

interface RevenueGridTotals {
  daily_totals: DailyRevenueMap;
  grand_total: number;
  active_vehicle_counts: DailyRevenueMap;
}

interface RevenueGridSummary {
  total_vehicles: number;
  avg_daily_revenue: number;
  avg_utilization: number;
  top_vehicle: { vehicle_id: string; nickname: string; total_revenue: number };
  bottom_vehicle: { vehicle_id: string; nickname: string; total_revenue: number };
}

interface VehicleRevenueGridResponse {
  period: string;
  days_in_month: number;
  vehicles: VehicleRevenueRow[];
  totals: RevenueGridTotals;
  summary: RevenueGridSummary;
}
```

---

## 2. Fleet Utilization Report

Daily utilization rate — what percentage of the fleet was earning revenue each day.
Replicates the `Загруженность` row from Excel.

### Request

```
GET /api/v1/reports/fleet-utilization?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month `YYYY-MM` |
| `category` | string | No | all | Filter by vehicle category |
| `branch_id` | UUID | No | all | Filter by branch |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "total_vehicles": 59,
  "days": [
    {
      "day": 1,
      "date": "2025-04-01",
      "active_vehicles": 44,
      "total_vehicles": 59,
      "utilization_rate": 0.7458,
      "total_revenue": 1116002
    }
  ],
  "summary": {
    "avg_utilization": 0.8503,
    "min_utilization": { "day": 1, "rate": 0.7458 },
    "max_utilization": { "day": 5, "rate": 0.9322 },
    "total_active_vehicle_days": 1504,
    "total_possible_vehicle_days": 1770,
    "total_revenue": 37466068
  },
  "by_category": [
    {
      "category": "Эконом",
      "vehicle_count": 12,
      "avg_utilization": 0.91,
      "total_revenue": 5400000
    },
    {
      "category": "Комфорт",
      "vehicle_count": 19,
      "avg_utilization": 0.84,
      "total_revenue": 14200000
    },
    {
      "category": "Бизнес",
      "vehicle_count": 28,
      "avg_utilization": 0.82,
      "total_revenue": 17866068
    }
  ]
}
```

### Data Source

- Active vehicles per day: `COUNTIF` equivalent — count vehicles that have `> 0` revenue
  in `cash_journal_entries` for that day
- Total vehicles: count of vehicles where `status NOT IN ('decommissioned', 'sold')`
  and `created_at <= end_of_period`
- Utilization = active_vehicles / total_vehicles

### TypeScript Types

```typescript
interface UtilizationDay {
  day: number;
  date: string;
  active_vehicles: number;
  total_vehicles: number;
  utilization_rate: number;
  total_revenue: number;
}

interface UtilizationSummary {
  avg_utilization: number;
  min_utilization: { day: number; rate: number };
  max_utilization: { day: number; rate: number };
  total_active_vehicle_days: number;
  total_possible_vehicle_days: number;
  total_revenue: number;
}

interface CategoryUtilization {
  category: string;
  vehicle_count: number;
  avg_utilization: number;
  total_revenue: number;
}

interface FleetUtilizationResponse {
  period: string;
  total_vehicles: number;
  days: UtilizationDay[];
  summary: UtilizationSummary;
  by_category: CategoryUtilization[];
}
```

---

## 3. Vehicle Expenses Report

Expense breakdown per vehicle — repairs, fines, wash, fuel, insurance.
Replicates the `Расходы` sheets from Excel.

### Request

```
GET /api/v1/reports/vehicle-expenses?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month `YYYY-MM` |
| `vehicle_id` | UUID | No | all | Single vehicle detail |
| `category` | string | No | all | Filter by expense category slug |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "vehicles": [
    {
      "vehicle_id": "uuid",
      "nickname": "Акцент 131",
      "license_plate": "131 ABC 01",
      "total_expenses": 147000,
      "total_revenue": 420000,
      "profit": 273000,
      "expense_ratio": 0.35,
      "expenses_by_category": [
        {
          "category_id": "uuid",
          "category_name": "Ремонт",
          "category_type": "direct",
          "amount": 147000,
          "entries_count": 3
        }
      ],
      "expense_entries": [
        {
          "id": "uuid",
          "date": "2025-04-05",
          "description": "Ремонт 131",
          "category_name": "Ремонт",
          "amount": 147000,
          "payment_method": "kaspi"
        }
      ]
    }
  ],
  "totals": {
    "total_expenses": 2730628,
    "total_revenue": 37466068,
    "total_profit": 34735440,
    "avg_expense_ratio": 0.073
  },
  "by_category_summary": [
    { "category_name": "Ремонт", "amount": 732000, "percentage": 0.268 },
    { "category_name": "Маркетинг", "amount": 1057930, "percentage": 0.387 },
    { "category_name": "Зарплата", "amount": 550000, "percentage": 0.201 },
    { "category_name": "Штрафы", "amount": 11800, "percentage": 0.004 }
  ]
}
```

### Data Source

- `cash_journal_entries` where `operation_type = 'expense'`, grouped by `vehicle_id`
- Joined with `expense_categories` for category name and type
- Revenue from same table where `operation_type = 'income'`
- Entries without `vehicle_id` are grouped as "General/Overhead" expenses

### TypeScript Types

```typescript
interface ExpenseCategoryBreakdown {
  category_id: string | null;
  category_name: string;
  category_type: string;
  amount: number;
  entries_count: number;
}

interface ExpenseEntry {
  id: string;
  date: string;
  description: string | null;
  category_name: string;
  amount: number;
  payment_method: string;
}

interface VehicleExpenseRow {
  vehicle_id: string;
  nickname: string | null;
  license_plate: string;
  total_expenses: number;
  total_revenue: number;
  profit: number;
  expense_ratio: number;
  expenses_by_category: ExpenseCategoryBreakdown[];
  expense_entries: ExpenseEntry[];
}

interface VehicleExpensesTotals {
  total_expenses: number;
  total_revenue: number;
  total_profit: number;
  avg_expense_ratio: number;
}

interface VehicleExpensesResponse {
  period: string;
  vehicles: VehicleExpenseRow[];
  totals: VehicleExpensesTotals;
  by_category_summary: { category_name: string; amount: number; percentage: number }[];
}
```

---

## 4. Manager Performance Report

Revenue and vehicle statistics per manager.
Replicates the manager-level view from Excel (who manages which vehicles, their revenue contribution).

### Request

```
GET /api/v1/reports/manager-performance?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month `YYYY-MM` |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "fleet_totals": {
    "total_revenue": 37466068,
    "total_vehicles": 59,
    "total_rentals": 142,
    "avg_utilization": 0.85
  },
  "managers": [
    {
      "manager_id": "uuid",
      "manager_name": "Исламбек",
      "vehicles_managed": 22,
      "total_revenue": 15200000,
      "revenue_share": 0.4057,
      "avg_revenue_per_vehicle": 690909,
      "total_rentals": 55,
      "avg_utilization": 0.88,
      "daily_performance": {
        "1": { "revenue": 640000, "active_vehicles": 20 },
        "2": { "revenue": 580000, "active_vehicles": 19 }
      },
      "top_vehicles": [
        {
          "vehicle_id": "uuid",
          "nickname": "Акцент 399",
          "total_revenue": 450000
        }
      ],
      "revenue_coefficient_avg": 0.41
    }
  ]
}
```

### Data Source

- `rentals` grouped by `manager_id` → count rentals, link to vehicles
- `cash_journal_entries` (income) joined with `rentals` via `rental_id` to get `manager_id`
- `users` table for manager name
- Revenue coefficient = manager's revenue / total fleet revenue (per day, then averaged)

### TypeScript Types

```typescript
interface ManagerDailyPerformance {
  [day: string]: {
    revenue: number;
    active_vehicles: number;
  };
}

interface ManagerTopVehicle {
  vehicle_id: string;
  nickname: string | null;
  total_revenue: number;
}

interface ManagerPerformanceRow {
  manager_id: string;
  manager_name: string;
  vehicles_managed: number;
  total_revenue: number;
  revenue_share: number;
  avg_revenue_per_vehicle: number;
  total_rentals: number;
  avg_utilization: number;
  daily_performance: ManagerDailyPerformance;
  top_vehicles: ManagerTopVehicle[];
  revenue_coefficient_avg: number;
}

interface FleetTotals {
  total_revenue: number;
  total_vehicles: number;
  total_rentals: number;
  avg_utilization: number;
}

interface ManagerPerformanceResponse {
  period: string;
  fleet_totals: FleetTotals;
  managers: ManagerPerformanceRow[];
}
```

---

## 5. P&L by Investor

Enhanced P&L showing profit split per investor/partner.
Combines existing `CompanyPnl` with investor vehicle data.

### Request

```
GET /api/v1/reports/pnl-by-investor?period=2025-04
```

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `period` | string | Yes | — | Month `YYYY-MM` |
| `investor_id` | UUID | No | all | Single investor detail |

### Response `200 OK`

```json
{
  "period": "2025-04",
  "company_totals": {
    "total_revenue": 37466068,
    "total_expenses": 4845000,
    "net_profit": 2165917,
    "vehicle_count": 59
  },
  "investors": [
    {
      "investor_id": "uuid",
      "investor_name": "Адеке",
      "investor_type": "partner",
      "vehicles": [
        {
          "vehicle_id": "uuid",
          "nickname": "Акцент 066",
          "revenue": 405000,
          "direct_expenses": 30000,
          "net_contribution": 375000
        }
      ],
      "vehicle_count": 18,
      "total_revenue": 7451000,
      "total_direct_expenses": 320000,
      "gross_profit": 7131000,
      "overhead_share": 1480000,
      "profit_share_percent": 60,
      "profit_share_amount": 3390600,
      "company_share_amount": 2260400,
      "payout_amount": 5297000,
      "debt_balance": 7312000,
      "net_settlement": 2165917
    }
  ],
  "own_vehicles": {
    "vehicle_count": 12,
    "total_revenue": 8200000,
    "total_direct_expenses": 450000,
    "net_contribution": 7750000
  }
}
```

### Data Source

- `vehicle_investors` — which vehicles belong to which investor
- `cash_journal_entries` — revenue and expenses per vehicle
- `investor_payouts` — payout history
- `investors` — investor details and profit distribution config
- Overhead is split proportionally by vehicle count or revenue share

### TypeScript Types

```typescript
interface InvestorVehiclePnl {
  vehicle_id: string;
  nickname: string | null;
  revenue: number;
  direct_expenses: number;
  net_contribution: number;
}

interface InvestorPnlRow {
  investor_id: string;
  investor_name: string;
  investor_type: string;
  vehicles: InvestorVehiclePnl[];
  vehicle_count: number;
  total_revenue: number;
  total_direct_expenses: number;
  gross_profit: number;
  overhead_share: number;
  profit_share_percent: number;
  profit_share_amount: number;
  company_share_amount: number;
  payout_amount: number;
  debt_balance: number;
  net_settlement: number;
}

interface CompanyTotals {
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
  vehicle_count: number;
}

interface OwnVehiclesSummary {
  vehicle_count: number;
  total_revenue: number;
  total_direct_expenses: number;
  net_contribution: number;
}

interface PnlByInvestorResponse {
  period: string;
  company_totals: CompanyTotals;
  investors: InvestorPnlRow[];
  own_vehicles: OwnVehiclesSummary;
}
```

---

## Vue Composables

### `useVehicleRevenueGrid`

```typescript
import { ref, watch } from 'vue'
import { api } from '@/shared/api'

export function useVehicleRevenueGrid() {
  const data = ref<VehicleRevenueGridResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch(period: string, filters?: { category?: string; branch_id?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ period })
      if (filters?.category) params.set('category', filters.category)
      if (filters?.branch_id) params.set('branch_id', filters.branch_id)
      const res = await api.get(`/reports/vehicle-revenue-grid?${params}`)
      data.value = res.data
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load revenue grid'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetch }
}
```

### `useFleetUtilization`

```typescript
export function useFleetUtilization() {
  const data = ref<FleetUtilizationResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch(period: string, filters?: { category?: string; branch_id?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ period })
      if (filters?.category) params.set('category', filters.category)
      if (filters?.branch_id) params.set('branch_id', filters.branch_id)
      const res = await api.get(`/reports/fleet-utilization?${params}`)
      data.value = res.data
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load utilization'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetch }
}
```

### `useVehicleExpenses`

```typescript
export function useVehicleExpenses() {
  const data = ref<VehicleExpensesResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch(period: string, filters?: { vehicle_id?: string; category?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ period })
      if (filters?.vehicle_id) params.set('vehicle_id', filters.vehicle_id)
      if (filters?.category) params.set('category', filters.category)
      const res = await api.get(`/reports/vehicle-expenses?${params}`)
      data.value = res.data
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load expenses'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetch }
}
```

### `useManagerPerformance`

```typescript
export function useManagerPerformance() {
  const data = ref<ManagerPerformanceResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch(period: string) {
    loading.value = true
    error.value = null
    try {
      const res = await api.get(`/reports/manager-performance?period=${period}`)
      data.value = res.data
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load manager performance'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetch }
}
```

### `usePnlByInvestor`

```typescript
export function usePnlByInvestor() {
  const data = ref<PnlByInvestorResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch(period: string, investorId?: string) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({ period })
      if (investorId) params.set('investor_id', investorId)
      const res = await api.get(`/reports/pnl-by-investor?${params}`)
      data.value = res.data
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Failed to load investor P&L'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, fetch }
}
```

---

## UI Screens

### Screen 1: Vehicle Revenue Grid

```
+------------------------------------------------------------------+
| Revenue Grid                              [April 2025 v] [Export] |
+------------------------------------------------------------------+
| Filters: [All Categories v] [All Branches v]                     |
+------------------------------------------------------------------+
| Vehicle       | Class  | Mgr  | Rate  | 1    | 2    | ... | Total|
|---------------|--------|------|-------|------|------|-----|------|
| Акцент 066    | Эконом | Исл. | 18000 | 15k  | 15k  | ... | 405k |
| Акцент 095    | Эконом | Айд. | 18000 | 15k  | 15k  | ... | 450k |
| ...           |        |      |       |      |      |     |      |
|---------------|--------|------|-------|------|------|-----|------|
| ИТОГО         |        |      | 1.67M | 1.1M | 1.1M | ... | 37.5M|
| Vehicles (>0) |        |      |       | 44   | 46   | ... |      |
| Utilization   |        |      |       | 74%  | 78%  | ... | 85%  |
+------------------------------------------------------------------+
| Summary: 59 vehicles | Avg daily: 1.25M | Best: Акцент 095 (450k)|
+------------------------------------------------------------------+
```

- Cells color-coded: green (>= daily rate), yellow (< daily rate), red (0 = idle)
- Scroll horizontally for days 1-31
- Click vehicle row to drill into vehicle detail page

### Screen 2: Fleet Utilization Chart

```
+------------------------------------------------------------------+
| Fleet Utilization                         [April 2025 v]          |
+------------------------------------------------------------------+
| [Line Chart: utilization % per day, 0-100% y-axis]               |
| Day 1: 74.6% ████████████████░░░░                                |
| Day 5: 93.2% ██████████████████████████░                         |
| ...                                                               |
+------------------------------------------------------------------+
| By Category:                                                      |
| Эконом  [████████████████████ 91%] 12 vehicles | 5.4M revenue    |
| Комфорт [████████████████░░░░ 84%] 19 vehicles | 14.2M revenue   |
| Бизнес  [████████████████░░░░ 82%] 28 vehicles | 17.9M revenue   |
+------------------------------------------------------------------+
| Avg: 85% | Min: 74.6% (Day 1) | Max: 93.2% (Day 5)              |
+------------------------------------------------------------------+
```

### Screen 3: Vehicle Expenses

```
+------------------------------------------------------------------+
| Vehicle Expenses                          [April 2025 v]          |
+------------------------------------------------------------------+
| [Pie Chart: expenses by category]                                 |
| Ремонт 26.8% | Маркетинг 38.7% | Зарплата 20.1% | Штрафы 0.4% |
+------------------------------------------------------------------+
| Vehicle       | Revenue | Expenses | Profit  | Ratio | Details   |
|---------------|---------|----------|---------|-------|-----------|
| Акцент 131    | 420k    | 147k     | 273k    | 35%   | [View]    |
| Акцент 888    | 380k    | 309k     | 71k     | 81%   | [View]    |
| ...           |         |          |         |       |           |
|---------------|---------|----------|---------|-------|-----------|
| TOTAL         | 37.5M   | 2.73M    | 34.7M   | 7.3%  |           |
+------------------------------------------------------------------+
```

- High expense ratio rows highlighted in red/orange
- Click [View] to expand expense entries for that vehicle

### Screen 4: Manager Performance

```
+------------------------------------------------------------------+
| Manager Performance                       [April 2025 v]          |
+------------------------------------------------------------------+
| [Bar Chart: revenue per manager]                                  |
+------------------------------------------------------------------+
| Manager    | Vehicles | Revenue | Share | Util. | Coefficient     |
|------------|----------|---------|-------|-------|-----------------|
| Исламбек   | 22       | 15.2M   | 40.6% | 88%   | 0.41            |
| Айдар      | 23       | 14.8M   | 39.5% | 86%   | 0.40            |
| Еркош      | 10       | 5.2M    | 13.9% | 78%   | 0.14            |
| Димаш      | 2        | 1.2M    | 3.2%  | 92%   | 0.03            |
| Тау        | 1        | 0.6M    | 1.6%  | 95%   | 0.02            |
| Тима       | 1        | 0.5M    | 1.2%  | 90%   | 0.01            |
+------------------------------------------------------------------+
| Fleet Total: 59 vehicles | 37.5M revenue | 142 rentals | 85% util|
+------------------------------------------------------------------+
```

### Screen 5: Investor P&L

```
+------------------------------------------------------------------+
| Investor P&L                              [April 2025 v]          |
+------------------------------------------------------------------+
| Company Totals: Revenue 37.5M | Expenses 4.85M | Profit 2.17M    |
+------------------------------------------------------------------+
| Investor | Type    | Cars | Revenue | Expenses | Payout | Balance |
|----------|---------|------|---------|----------|--------|---------|
| Адеке    | partner | 18   | 7.45M   | 320k     | 5.3M   | -7.3M   |
| Дархан   | partner | 8    | 3.1M    | 180k     | 1.8M   | 0       |
| ...      |         |      |         |          |        |         |
| Own fleet| own     | 12   | 8.2M    | 450k     | —      | —       |
+------------------------------------------------------------------+
| Click investor row to expand vehicle-level breakdown              |
+------------------------------------------------------------------+
```

---

## Permissions

| Endpoint | Required Permission |
|----------|-------------------|
| Vehicle Revenue Grid | `report.view` |
| Fleet Utilization | `report.view` |
| Vehicle Expenses | `report.view` |
| Manager Performance | `report.view` or `admin` |
| P&L by Investor | `report.view` or `financial_manager` |

---

## Error Responses

| Status | When |
|--------|------|
| `400` | Invalid period format (not `YYYY-MM`) |
| `401` | Not authenticated |
| `403` | Insufficient permissions |
| `503` | Database unavailable |
