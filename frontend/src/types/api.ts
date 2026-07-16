// Mirrors backend/app/schemas/*.py — keep these in sync with the Pydantic models.

export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Url {
  id: number;
  short_code: string;
  short_url: string;
  original_url: string;
  created_at: string;
  expires_at: string | null;
  click_count: number;
  last_clicked_at: string | null;
  is_expired: boolean;
}

export interface UrlListResponse {
  items: Url[];
  total: number;
  page: number;
  page_size: number;
}

export interface UrlCreateInput {
  original_url: string;
  expires_at?: string | null;
}

export interface UrlUpdateInput {
  original_url?: string;
  expires_at?: string | null;
}

export type SortBy = "created_at" | "click_count";
export type SortOrder = "asc" | "desc";

export interface ListUrlsParams {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: SortBy;
  order?: SortOrder;
}

export interface ClickBucket {
  period: string;
  count: number;
}

export interface BreakdownItem {
  label: string;
  count: number;
}

export type AnalyticsGroupBy = "day" | "week";

export interface UrlAnalytics {
  short_code: string;
  total_clicks: number;
  group_by: AnalyticsGroupBy;
  clicks_over_time: ClickBucket[];
  by_browser: BreakdownItem[];
  by_os: BreakdownItem[];
  by_device_type: BreakdownItem[];
}

export interface ApiErrorBody {
  detail?: string | { msg: string }[];
  error?: string;
}
